import XCTest
@testable import PastPaperCreator

final class PastPaperCreatorTests: XCTestCase {
    func testBackendProgressEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"progress","stage":"render","message":"Rendering question paper","progress":0.88}"#)
        XCTAssertEqual(event, .progress(stage: "render", message: "Rendering question paper", progress: 0.88))
    }

    func testBackendFileEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"file","role":"mark_scheme","path":"/tmp/ms.pdf"}"#)
        XCTAssertEqual(event, .file(role: "mark_scheme", path: "/tmp/ms.pdf"))
    }

    func testAppStoreModeDisablesOllamaManagement() {
        XCTAssertFalse(DistributionMode.appStore.canManageOllama)
        XCTAssertTrue(DistributionMode.direct.canManageOllama)
    }

    func testCatalogReadyBoardsUseCorrectResourceFolders() throws {
        let economics = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        XCTAssertTrue(economics.isReady)
        XCTAssertEqual(economics.resourcePath, "a-levels/economics/edexcel-a")
        XCTAssertEqual(economics.backendSubject, "economics")

        let computerScience = try XCTUnwrap(ExamCatalog.board(id: "computer-science-aqa"))
        XCTAssertTrue(computerScience.isReady)
        XCTAssertEqual(computerScience.resourcePath, "a-levels/computer-science/aqa")
        XCTAssertEqual(computerScience.backendSubject, "computer_science")

        let placeholder = try XCTUnwrap(ExamCatalog.board(id: "biology-aqa"))
        XCTAssertFalse(placeholder.isReady)
    }
}
