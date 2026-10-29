import Foundation
import XCTest
@testable import Keldin

final class BenchmarkLocalizationTests: XCTestCase {
    func testInvalidScoreNoticeUsesSelectedLanguageAndUnknownErrorsStayVerbatim() {
        let message = BenchmarkVerdict.invalidScoreMessage
        XCTAssertEqual(NativeInterfaceCopy.benchmarkText(message, locale: Locale(identifier: "en")), message)
        XCTAssertEqual(NativeInterfaceCopy.benchmarkText(message, locale: Locale(identifier: "fr")), "Le test de performance a renvoyé un score invalide.")
        XCTAssertEqual(NativeInterfaceCopy.benchmarkText("Exact OS failure 17", locale: Locale(identifier: "fr")), "Exact OS failure 17")
    }

    func testWorkspaceLabelsAndProgressUseFrenchResources() {
        let cases: [(LocalizedStringResource, String)] = [
            ("Benchmark", "Test du Mac"),
            ("Results", "Résultats"),
            ("Metric", "Mesure"),
            ("Value", "Valeur"),
            ("Detail", "Détail"),
            ("Benchmark score", "Score du test de performance"),
            ("Benchmark progress", "Progression du test de performance"),
            ("Run the benchmark to calibrate ETA and check whether this Mac is ready for local generation.", "Lancez le test pour estimer les temps de création et vérifier les capacités de ce Mac."),
            ("Running CPU, memory, storage, PDF, network, power and Ollama checks", "Vérification du processeur, de la mémoire, du stockage, des PDF, du réseau, de l’alimentation et d’Ollama"),
        ]
        for (resource, french) in cases {
            XCTAssertEqual(InterfaceText.resolve(resource, language: "fr"), french)
            XCTAssertNotEqual(InterfaceText.resolve(resource, language: "en"), french)
        }
        let duration = 30
        let runLabel: LocalizedStringResource = "Run \(duration) Second Test"
        XCTAssertEqual(InterfaceText.resolve(runLabel, language: "fr"), "Lancer le test de 30 secondes")
        XCTAssertEqual(InterfaceText.resolve(runLabel, language: "en"), "Run 30 Second Test")
    }

    func testEveryKnownVerdictAndDetailUsesChosenEnglishOrFrench() {
        let cases = [
            ("Benchmark failed", "Échec du test de performance"),
            ("No samples were collected.", "Aucun échantillon n’a été recueilli."),
            ("Ready for local generation", "Prêt pour la création locale"),
            ("This Mac should generate papers comfortably with the selected local setup.", "Ce Mac devrait pouvoir créer des sujets dans de bonnes conditions avec la configuration locale sélectionnée."),
            ("Capable with slower local models", "Compatible avec des modèles locaux plus lents"),
            ("Generation should work, but large Ollama models may take noticeably longer.", "La création devrait fonctionner, mais les grands modèles Ollama peuvent prendre sensiblement plus de temps."),
            ("Use smaller models or hosted AI", "Utilisez des modèles plus petits ou une IA hébergée"),
            ("The diagnostic found limited headroom for local generation.", "Le diagnostic indique une marge de ressources limitée pour la création locale."),
        ]
        for (english, french) in cases {
            XCTAssertEqual(NativeInterfaceCopy.benchmarkText(english, locale: Locale(identifier: "en")), english)
            XCTAssertEqual(NativeInterfaceCopy.benchmarkText(english, locale: Locale(identifier: "fr")), french)
        }
        let verdict = BenchmarkVerdict(score: 0.65, verdict: "Ready for local generation", detail: "This Mac should generate papers comfortably with the selected local setup.")
        XCTAssertEqual(NativeInterfaceCopy.benchmarkText(verdict.verdict, locale: Locale(identifier: "fr")), "Prêt pour la création locale")
        XCTAssertEqual(verdict.score, 0.65)
        XCTAssertEqual(verdict.verdict, "Ready for local generation")
    }

    func testKnownMetricCopyIsLocalizedButUnknownAndOSDataStayVerbatim() {
        let cases = [
            ("Device", "Appareil"),
            ("Architecture", "Architecture"),
            ("Processor", "Processeur"),
            ("CPU Cores", "Cœurs CPU"),
            ("Memory", "Mémoire"),
            ("Performance Cores", "Cœurs de performance"),
            ("Efficiency Cores", "Cœurs économes en énergie"),
            ("CPU Throughput", "Débit CPU"),
            ("Average CPU Load", "Charge CPU moyenne"),
            ("Free Memory", "Mémoire disponible"),
            ("Memory Pressure", "Pression mémoire"),
            ("Swap Used", "Mémoire d’échange utilisée"),
            ("Disk Write", "Écriture disque"),
            ("Disk Read", "Lecture disque"),
            ("Small-file Latency", "Latence des petits fichiers"),
            ("Output Free Space", "Espace disponible pour les fichiers"),
            ("PDF Render", "Rendu PDF"),
            ("Network Latency", "Latence réseau"),
            ("Network Download", "Téléchargement réseau"),
            ("Ollama Response", "Réponse d’Ollama"),
            ("Thermal Speed Limit", "Limite de performance thermique"),
            ("Power Source", "Alimentation"),
            ("Battery Level", "Niveau de batterie"),
            ("Python Runtime", "Version de Python"),
            ("Hashing workload used as a local model proxy.", "La charge de calcul par hachage sert d’indicateur pour un modèle local."),
            ("Proxy for many small PDF and image writes.", "Indicateur pour de nombreuses petites écritures de PDF et d’images."),
            ("Unavailable during benchmark", "Indisponible pendant le test de performance"),
            ("Ollama was not reachable during benchmark", "Ollama était inaccessible pendant le test de performance"),
            ("Unavailable on this Mac", "Indisponible sur ce Mac"),
        ]
        for (english, french) in cases {
            XCTAssertEqual(NativeInterfaceCopy.benchmarkText(english, locale: Locale(identifier: "en")), english)
            XCTAssertEqual(NativeInterfaceCopy.benchmarkText(english, locale: Locale(identifier: "fr")), french)
        }
        for raw in ["AC Power", "Darwin 25.1 arm64", "Unknown backend refusal: code 42", "Ready for local generation [future version]"] {
            XCTAssertEqual(NativeInterfaceCopy.benchmarkText(raw, locale: Locale(identifier: "fr")), raw)
        }
        for unit in ["%", "ms", "pages/s"] {
            XCTAssertEqual(NativeInterfaceCopy.benchmarkUnit(unit, locale: Locale(identifier: "fr")), unit)
        }
    }

    func testMetricDisplayUsesFrenchDecimalsWithoutChangingRawValueOrUnit() {
        let metric = BenchmarkMetric(name: "Memory", value: 1.25, unit: "GB", detail: nil, score: 0.6)
        XCTAssertEqual(metric.displayValue(locale: Locale(identifier: "fr")), "1,25 Go")
        XCTAssertEqual(metric.displayValue(locale: Locale(identifier: "en")), "1.25 GB")
        XCTAssertEqual(metric.value, 1.25)
        XCTAssertEqual(metric.unit, "GB")
        XCTAssertEqual(metric.score, 0.6)
        XCTAssertEqual(NativeInterfaceCopy.benchmarkUnit("cores", locale: Locale(identifier: "fr")), "cœurs")
        XCTAssertEqual(NativeInterfaceCopy.benchmarkUnit("MB/s", locale: Locale(identifier: "fr")), "Mo/s")
        XCTAssertEqual(NativeInterfaceCopy.benchmarkUnit("unrecognised-unit", locale: Locale(identifier: "fr")), "unrecognised-unit")
    }

    func testThermalPercentageAndDiagnosticOnlyValuesKeepTheirMeaning() {
        let thermal = BenchmarkMetric(name: "Thermal Speed Limit", value: 75, unit: "%", detail: nil, score: 0.75)
        XCTAssertEqual(thermal.displayValue(locale: Locale(identifier: "fr")), "75 %")
        XCTAssertEqual(thermal.value, 75)
        XCTAssertEqual(thermal.unit, "%")
        XCTAssertFalse(thermal.displayValue(locale: Locale(identifier: "fr")).contains("°"))
        let known = BenchmarkMetric(name: "Network Latency", value: nil, unit: nil, detail: "Unavailable during benchmark", score: nil)
        XCTAssertEqual(known.displayValue(locale: Locale(identifier: "fr")), "Indisponible pendant le test de performance")
        let unknown = BenchmarkMetric(name: "Device", value: nil, unit: nil, detail: "Darwin 25.1 arm64", score: nil)
        XCTAssertEqual(unknown.displayValue(locale: Locale(identifier: "fr")), "Darwin 25.1 arm64")
    }
}
