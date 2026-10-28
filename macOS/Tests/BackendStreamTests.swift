import Foundation
import XCTest
@testable import Keldin

final class BackendStreamTests: XCTestCase {
    func testFrenchEventSurvivesEveryPossibleByteSplit() throws {
        let line = #"{"type":"progress","stage":"render","message":"Épreuve créée à Noël ☀️","progress":0.5}"#
        let data = Data((line + "\n").utf8)
        for split in 0...data.count {
            var buffer = BackendEventLineBuffer()
            let lines = buffer.append(Data(data.prefix(split)))
                + buffer.append(Data(data.dropFirst(split)))
            XCTAssertEqual(lines, [line], "Byte split \(split)")
            XCTAssertEqual(buffer.finish(), "")
            if let received = lines.first {
                XCTAssertEqual(
                    try BackendEvent(jsonLine: received),
                    .progress(stage: "render", message: "Épreuve créée à Noël ☀️", progress: 0.5)
                )
            }
        }
    }

    func testSeveralLinesAndFinalUnterminatedEventKeepTheirOrder() {
        var buffer = BackendEventLineBuffer()
        XCTAssertEqual(buffer.append(Data("première\n\ndeuxième\nfin é".utf8)), ["première", "", "deuxième"])
        XCTAssertEqual(buffer.finish(), "fin é")
        XCTAssertEqual(buffer.finish(), "")
    }

    func testOneByteChunksPreserveUnicodeAndFinalLine() {
        var buffer = BackendEventLineBuffer()
        let source = "créée\n完了\n🌞"
        let lines = Data(source.utf8).flatMap { buffer.append(Data([$0])) }
        XCTAssertEqual(lines, ["créée", "完了"])
        XCTAssertEqual(buffer.finish(), "🌞")
    }

    func testInvalidUTF8IsRejectedInsteadOfDroppedOrRepairedInsideJSON() {
        var buffer = BackendEventLineBuffer()
        var data = Data(#"{"type":"done","message":""#.utf8)
        data.append(0xFF)
        data.append(contentsOf: Data("\"}\n".utf8))
        let lines = buffer.append(data)
        XCTAssertEqual(lines.count, 1)
        XCTAssertThrowsError(try BackendEvent(jsonLine: lines[0]))
        XCTAssertEqual(buffer.finish(), "")

        XCTAssertEqual(buffer.append(Data([0xFF])), [])
        XCTAssertThrowsError(try BackendEvent(jsonLine: buffer.finish()))
    }
}
