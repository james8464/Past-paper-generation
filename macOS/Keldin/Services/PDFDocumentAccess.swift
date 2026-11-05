import Foundation
import PDFKit
import Synchronization

enum PDFLoadFailure: Error, Equatable {
    case missing, permissionDenied, unreadable, invalid, locked, wrongFile, bookmark

    var messageResource: LocalizedStringResource {
        switch self {
        case .missing: "This PDF is no longer at its saved location."
        case .permissionDenied: "Keldin can't read this PDF. Choose the same file to allow access."
        case .unreadable: "This PDF couldn't be read. Check the file, then try again."
        case .invalid: "This file couldn't be opened as a PDF."
        case .locked: "This PDF is locked. Unlock it outside Keldin, then try again."
        case .wrongFile: "Choose the same PDF shown in History. Other files won't replace it."
        case .bookmark: "Access to this PDF couldn't be saved. Choose the file again."
        }
    }
}

struct LoadedPDF {
    let document: PDFDocument
    let bytes: Data
}

// The final fallback release also runs on MainActor. A cancelled byte read
// keeps its own token until the reader returns, independently of selection.
@MainActor
private final class PDFScopeGrant {
    private var holders = 0
    private let stop: @MainActor @Sendable () -> Void

    init(stop: @escaping @MainActor @Sendable () -> Void) { self.stop = stop }
    func acquire() { holders += 1 }
    func release() {
        holders -= 1
        if holders == 0 { stop() }
    }
}

final class PDFReadLease: Sendable {
    private let released = Mutex(false)
    private let grant: PDFScopeGrant

    @MainActor
    init(stop: @escaping @MainActor @Sendable () -> Void) {
        grant = PDFScopeGrant(stop: stop)
        grant.acquire()
    }

    @MainActor
    private init(grant: PDFScopeGrant) {
        self.grant = grant
        grant.acquire()
    }

    @MainActor
    func retained() -> PDFReadLease? {
        guard !released.withLock({ $0 }) else { return nil }
        return PDFReadLease(grant: grant)
    }

    @MainActor
    func release() {
        if takeRelease() { grant.release() }
    }

    private func takeRelease() -> Bool {
        released.withLock { released in
            guard !released else { return false }
            released = true
            return true
        }
    }

    deinit {
        if takeRelease() {
            let grant = grant
            Task { @MainActor in grant.release() }
        }
    }
}

struct ScopedLoadedPDF {
    let pdf: LoadedPDF
    let url: URL
    let lease: PDFReadLease
    let needsBookmark: Bool
    let bookmarkURL: URL
}

private actor PDFByteReader {
    let read: @Sendable (URL) throws -> Data

    init(read: @escaping @Sendable (URL) throws -> Data) { self.read = read }

    func bytes(at url: URL) throws -> Data {
        try Task.checkCancellation()
        return try read(url)
    }
}

@MainActor
final class PDFDocumentAccess {
    static let bookmarkKey = "documentPDFBookmarks.v1"
    private let defaults: UserDefaults
    private let readData: @Sendable (URL) throws -> Data
    private let byteReader: PDFByteReader
    private let startAccess: (URL) -> Bool
    private let stopAccess: (URL) -> Void
    private let makeBookmark: (URL) throws -> Data
    private let resolveBookmark: (Data) throws -> (URL, Bool)
    private var scopedURL: URL?

    init(
        defaults: UserDefaults = .standard,
        readData: @escaping @Sendable (URL) throws -> Data = { try Data(contentsOf: $0) },
        startAccess: @escaping (URL) -> Bool = { $0.startAccessingSecurityScopedResource() },
        stopAccess: @escaping (URL) -> Void = { $0.stopAccessingSecurityScopedResource() },
        makeBookmark: @escaping (URL) throws -> Data = {
            try $0.bookmarkData(options: [.withSecurityScope, .securityScopeAllowOnlyReadAccess], includingResourceValuesForKeys: nil, relativeTo: nil)
        },
        resolveBookmark: @escaping (Data) throws -> (URL, Bool) = { data in
            var stale = false
            let url = try URL(resolvingBookmarkData: data, options: [.withSecurityScope, .withoutUI], relativeTo: nil, bookmarkDataIsStale: &stale)
            return (url, stale)
        }
    ) {
        self.defaults = defaults
        self.readData = readData
        self.byteReader = PDFByteReader(read: readData)
        self.startAccess = startAccess
        self.stopAccess = stopAccess
        self.makeBookmark = makeBookmark
        self.resolveBookmark = resolveBookmark
    }

    // Only URL and immutable bytes cross the reader actor. PDFKit parsing,
    // bookmark changes and security-scope ownership remain on MainActor.
    func loadAsync(_ url: URL, recovering selected: URL? = nil) async throws -> ScopedLoadedPDF {
        guard url.isFileURL else { throw PDFLoadFailure.invalid }
        if let selected {
            guard selected.isFileURL, selected.standardizedFileURL == url.standardizedFileURL else {
                throw PDFLoadFailure.wrongFile
            }
        }
        try Task.checkCancellation()
        var accessURL = selected ?? url
        var needsBookmark = true
        if selected == nil, let saved = bookmarks[url.standardizedFileURL.path],
           let (restored, stale) = try? resolveBookmark(saved),
           restored.standardizedFileURL == url.standardizedFileURL {
            accessURL = restored
            needsBookmark = stale
        }
        let granted = startAccess(accessURL)
        let lease = PDFReadLease { [self, accessURL] in
            if granted { stopAccess(accessURL) }
        }
        do {
            let bytes = try await byteReader.bytes(at: url)
            try Task.checkCancellation()
            let pdf = try decode(bytes).get()
            return ScopedLoadedPDF(pdf: pdf, url: url, lease: lease, needsBookmark: needsBookmark, bookmarkURL: accessURL)
        } catch {
            lease.release()
            if error is CancellationError { throw error }
            throw (error as? PDFLoadFailure) ?? failure(for: error)
        }
    }

    func remember(_ loaded: ScopedLoadedPDF) -> Result<Void, PDFLoadFailure> {
        loaded.needsBookmark ? rememberValidatedPDF(loaded.bookmarkURL, for: loaded.url) : .success(())
    }

    func load(_ url: URL) -> Result<LoadedPDF, PDFLoadFailure> {
        guard url.isFileURL else {
            release()
            return .failure(.invalid)
        }
        if scopedURL?.standardizedFileURL != url.standardizedFileURL { release() }
        var shouldRemember = false
        if scopedURL == nil { shouldRemember = true }
        if scopedURL == nil, let data = bookmarks[url.standardizedFileURL.path],
           let (restored, isStale) = try? resolveBookmark(data),
           restored.standardizedFileURL == url.standardizedFileURL {
            if startAccess(restored) { scopedURL = restored }
            shouldRemember = isStale
        }
        let result = read(url)
        if case .success = result, shouldRemember { _ = rememberValidatedPDF(url) }
        if case .failure = result { release() }
        return result
    }

    // The caller already holds access, such as the selected output-folder grant.
    // Recording another PDF must not acquire or release the reader's active lease.
    func rememberReadablePDF(_ url: URL) -> Result<Void, PDFLoadFailure> {
        guard url.isFileURL else { return .failure(.invalid) }
        if case .failure(let failure) = read(url) { return .failure(failure) }
        return rememberValidatedPDF(url)
    }

    func recover(expected: URL, selected: URL?) throws -> Bool {
        guard let selected else { return false }
        guard selected.isFileURL,
              selected.standardizedFileURL == expected.standardizedFileURL else {
            throw PDFLoadFailure.wrongFile
        }
        release()
        if startAccess(selected) { scopedURL = selected }
        do {
            _ = try read(selected).get()
            let bookmark: Data
            do { bookmark = try makeBookmark(selected) }
            catch { throw PDFLoadFailure.bookmark }
            saveBookmark(bookmark, for: expected)
            return true
        } catch {
            release()
            throw error
        }
    }

    func release() {
        if let url = scopedURL {
            scopedURL = nil
            stopAccess(url)
        }
    }

    // The last view can disappear without another selection update.
    deinit { scopedURL?.stopAccessingSecurityScopedResource() }

    private var bookmarks: [String: Data] {
        defaults.dictionary(forKey: Self.bookmarkKey) as? [String: Data] ?? [:]
    }

    private func saveBookmark(_ data: Data, for url: URL) {
        var saved = bookmarks
        saved[url.standardizedFileURL.path] = data
        defaults.set(saved, forKey: Self.bookmarkKey)
    }

    private func rememberValidatedPDF(_ url: URL, for expected: URL? = nil) -> Result<Void, PDFLoadFailure> {
        guard url.isFileURL else { return .failure(.invalid) }
        do {
            saveBookmark(try makeBookmark(url), for: expected ?? url)
            return .success(())
        } catch {
            return .failure(.bookmark)
        }
    }

    private func read(_ url: URL) -> Result<LoadedPDF, PDFLoadFailure> {
        do {
            return decode(try readData(url))
        } catch { return .failure(failure(for: error)) }
    }

    private func decode(_ bytes: Data) -> Result<LoadedPDF, PDFLoadFailure> {
        guard let document = PDFDocument(data: bytes) else { return .failure(.invalid) }
        guard !document.isLocked else { return .failure(.locked) }
        guard document.pageCount > 0 else { return .failure(.invalid) }
        return .success(LoadedPDF(document: document, bytes: bytes))
    }

    private func failure(for error: Error) -> PDFLoadFailure {
        if let error = error as? CocoaError {
            switch error.code {
            case .fileNoSuchFile, .fileReadNoSuchFile: return .missing
            case .fileReadNoPermission: return .permissionDenied
            default: return .unreadable
            }
        }
        return .unreadable
    }
}
