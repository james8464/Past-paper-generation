import Foundation
import PDFKit

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

@MainActor
final class PDFDocumentAccess {
    static let bookmarkKey = "documentPDFBookmarks.v1"
    private let defaults: UserDefaults
    private let readData: (URL) throws -> Data
    private let startAccess: (URL) -> Bool
    private let stopAccess: (URL) -> Void
    private let makeBookmark: (URL) throws -> Data
    private let resolveBookmark: (Data) throws -> (URL, Bool)
    private var scopedURL: URL?

    init(
        defaults: UserDefaults = .standard,
        readData: @escaping (URL) throws -> Data = { try Data(contentsOf: $0) },
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
        self.startAccess = startAccess
        self.stopAccess = stopAccess
        self.makeBookmark = makeBookmark
        self.resolveBookmark = resolveBookmark
    }

    func load(_ url: URL) -> Result<LoadedPDF, PDFLoadFailure> {
        if scopedURL?.standardizedFileURL != url.standardizedFileURL { release() }
        var stale = false
        if scopedURL == nil, let data = bookmarks[url.standardizedFileURL.path],
           let (restored, isStale) = try? resolveBookmark(data),
           restored.standardizedFileURL == url.standardizedFileURL,
           startAccess(restored) {
            scopedURL = restored
            stale = isStale
        }
        let result = read(url)
        if case .success = result, stale,
           let renewed = try? makeBookmark(url) {
            saveBookmark(renewed, for: url)
        }
        if case .failure = result { release() }
        return result
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

    private func read(_ url: URL) -> Result<LoadedPDF, PDFLoadFailure> {
        do {
            let bytes = try readData(url)
            guard let document = PDFDocument(data: bytes) else { return .failure(.invalid) }
            guard !document.isLocked else { return .failure(.locked) }
            guard document.pageCount > 0 else { return .failure(.invalid) }
            return .success(LoadedPDF(document: document, bytes: bytes))
        } catch let error as CocoaError {
            switch error.code {
            case .fileNoSuchFile, .fileReadNoSuchFile: return .failure(.missing)
            case .fileReadNoPermission: return .failure(.permissionDenied)
            default: return .failure(.unreadable)
            }
        } catch {
            return .failure(.unreadable)
        }
    }
}
