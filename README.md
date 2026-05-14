# 🎓 Past Paper Creator

[![macOS](https://img.shields.io/badge/Platform-macOS-blue.svg)](https://apple.com)
[![Python](https://img.shields.io/badge/Language-Python-yellow.svg)](https://python.org)
[![Privacy](https://img.shields.io/badge/Privacy-Local--First-green.svg)](https://ollama.com)

A professional suite for generating exam-style past papers using Local AI (Ollama) or hosted providers. Designed for students and educators to create endless practice materials that match specific syllabus requirements.

---

## 🚀 Getting Started

This project is designed to be used in two ways: as a native **macOS Application** (recommended) or via a **Python CLI**.

### 🍏 macOS Application (Recommended)
The macOS app provides a beautiful SwiftUI interface for generating papers, managing local models, and tracking progress.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/james8464/Past-paper-generation.git
    cd Past-paper-generation
    ```
2.  **Open in Xcode**:
    Navigate to the `macOS/` directory and open `PastPaperCreator.xcodeproj`.
3.  **Build and Run**:
    Select the `PastPaperCreator` scheme and click the Play button.

> [!TIP]
> Ensure you have [Ollama](https://ollama.com) installed for local generation, or provide API keys for hosted providers in the app settings.

### 🐍 Python CLI
For developers or power users who prefer the command line.

1.  **Set up environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e "Backend/Core[dev]"
    ```
2.  **Run the bridge**:
    ```bash
    python bridge.py generate --subject economics --paper 1 --output ~/Downloads --dry-run
    ```

---

## 📂 Project Structure

The project is organized to clearly separate the application layers and content.

-   **`macOS/`**: Native SwiftUI application built for macOS.
-   **`Backend/`**: Core Python logic and the JSON-lines bridge.
    -   `Core/`: The main Python package for generation and benchmarking.
-   **`Resources/`**: Subject-specific resource packs (Economics, Computer Science, etc.).
-   **`Tests/`**: Automated test suite for the backend bridge.
-   **`bridge.py`**: The primary entry point for the Python CLI and the macOS app wrapper.

---

## 🛠 Features

-   **Local AI Integration**: Full support for Ollama, allowing for private, offline generation.
-   **Multi-Subject Support**: Modular architecture for different exam boards and subjects.
-   **Native Experience**: High-performance SwiftUI app with system notifications and smooth progress tracking.
-   **Benchmarking**: Built-in diagnostics to test your Mac's performance for local AI workloads.
-   **Privacy First**: No analytics, no tracking. Your data stays on your machine.

---

## 🔒 Privacy & Security

We believe in **Local-First** AI.
-   **Local Models**: By default, generation happens on your machine using Ollama.
-   **No Tracking**: No telemetry or remote data collection is included.
-   **Encrypted Keys**: API keys for hosted providers are stored securely in your macOS Keychain.

---

## 👨‍💻 Contributing

Contributions are welcome! Whether it's adding new subjects to `Resources/` or improving the `macOS/` app, feel free to open a PR.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

*Created with ❤️ by James Durup*
