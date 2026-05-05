from __future__ import annotations

from pathlib import Path

from pastpapergen.cli import default_output_dir, generate_package

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("A-Level Economics Edexcel A Paper Generator")
    print("1: Paper 1 - Markets and Business Behaviour")
    print("2: Paper 2 - The National and Global Economy")
    print("3: Paper 3 - Microeconomics and Macroeconomics")

    paper = input("Choose paper (1/2/3): ").strip()
    use_ollama = input("Use Ollama LLM? (y/N): ").strip().lower() == "y"
    seed_text = input("Seed (optional, press Enter to skip): ").strip()
    seed = int(seed_text) if seed_text else None

    paths = generate_package(
        paper=paper,
        syllabus_path=PROJECT_ROOT / "data/syllabus_seed.json",
        output_dir=default_output_dir(),
        seed=seed,
        model="qwen2.5:14b",
        ollama_url="http://localhost:11434",
        dry_run=not use_ollama,
        progress=_print_progress,
    )

    print("\nSaved to Downloads:")
    print(paths["question_paper"])
    print(paths["source_booklet"])
    print(paths["mark_scheme"])
    return 0


def _print_progress(message: str) -> None:
    print(f"[progress] {message}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
