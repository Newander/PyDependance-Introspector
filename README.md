# 🐍 Project Dependency Introspector

A CLI tool to parse Python projects and build a dependency tree of modules, classes, functions, and their relationships. Visualize and analyze how your code connects to improve maintainability and architecture decisions.

## ✨ Features
- 🔍 Parse Python sources and extract code objects
- 🌳 Build a dependency tree across modules and objects
- 🧭 Link references and usages between code entities
- 🖼️ Draw/visualize relationships as graphs
- 🧪 Explore via CLI commands and reports

## 🗂️ Project Structure
- `src/` — core library
    - `parser.py` — parses Python code into objects
    - `tree.py` — builds dependency trees
    - `linker.py` — links cross-references
    - `drawer.py` — visualization helpers
    - `code_objs/` — code entities representations
- `main.py` — CLI entry point
- `notebooks/` — experiments and demos

## 🚀 Quick Start
1. Create and activate virtualenv (if not already):
    - macOS/Linux:
      ```bash
          # Bash/Zsh
          python3 -m venv .venv
          source .venv/bin/activate
      ```
    - Windows:
      ```powershell
      py -m venv .venv
      .\.venv\Scripts\activate
      ```
2. Install dependencies:
   ```bash
      pip install -r requirements.txt
   ```
3. Run:
   ```bash
      python main.py --help
   ```

## 🧰 Example CLI Usage
- Build dependency tree for a project:
  ```bash
      python main.py tree --path /path/to/project --out tree.json
  ```
- Visualize as a graph:
  ```bash
      python main.py draw --input tree.json --out graph.html
  ```
- Analyze usages:
  ```bash
      python main.py analyze --path /path/to/project --report report.md
  ```

Note: CLI flags may evolve; run `--help` for the most up-to-date options.

## 📊 Outputs
- JSON artifacts with dependency trees
- HTML/PNG graph visualizations
- Markdown/CSV reports for usages and coupling metrics

## 🧭 Roadmap
- 🛠️ CLI to realize prototyped modules (auto-create missing attributes/methods)
- 🕸️ Dynamic graph networks for interactive exploration
- 📈 CLI to calculate “mean object usage” score across the project
- 🧠 Advanced static analysis (e.g., import resolution, alias tracking)
- 🧪 Test coverage overlay on dependency graph

## 🤝 Contributing
- Fork the repo
- Create a feature branch
- Add tests where applicable
- Open a PR with a clear description

## 🐛 Issues & Feedback
Found a bug or have a feature request? Please open an issue. We appreciate your feedback!

## 📄 License
MIT License — feel free to use, modify, and share.