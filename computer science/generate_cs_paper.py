from __future__ import annotations

from cspapergen.cli import default_output_dir, generate_package
from cspapergen.tui import progress_reporter


def main() -> int:
    print("AQA A-Level Computer Science Paper 2 Generator")
    print("1: Paper 2 - Computer Science theory")

    choice = input("Choose paper (1): ").strip() or "1"
    if choice != "1":
        raise SystemExit("Only Paper 2 is implemented for Computer Science v1.")
    use_ollama = input("Use Ollama LLM? (y/N): ").strip().lower() == "y"
    seed_text = input("Seed (optional, press Enter to skip): ").strip()
    seed = int(seed_text) if seed_text else None

    with progress_reporter(fps=10) as progress:
        paths = generate_package(
            output_dir=default_output_dir(),
            seed=seed,
            dry_run=not use_ollama,
            model="qwen2.5:14b",
            ollama_url="http://localhost:11434",
            progress=progress,
        )

    print("\nSaved to Downloads:")
    print(paths["question_paper"])
    print(paths["mark_scheme"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
