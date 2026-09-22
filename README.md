# AURA — AI Automation Assistant 🤖

AURA is a Python-based AI Automation Assistant designed to understand user requests, create execution plans, use registered tools, apply security checks, analyze GitHub repositories, and generate useful final responses.

AURA uses **Groq LLMs** as its intelligence layer and follows a modular **Planner → Executor → Tools → Response** architecture.

---

## ✨ Features

- 🧠 Intelligent task planning
- ⚙️ Multi-step task execution
- 🔐 Security and permission layer
- 🐙 GitHub repository integration
- 📖 GitHub README analysis
- 🌐 Web page fetching
- 📁 Local file tools
- 🤖 Groq LLM integration
- 🚀 FastAPI web interface
- ☁️ Vercel deployment ready
- 🧩 Modular tool architecture
- 🛡️ Environment-based secret management

---

## 🏗️ Architecture

```text
                         ┌─────────────────┐
                         │      User       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │      AURA       │
                         │   Orchestrator  │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     Planner     │
                         │                 │
                         │ Creates task    │
                         │ execution plan  │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    Executor     │
                         │                 │
                         │ Executes steps │
                         └────────┬────────┘
                                  │
                  ┌───────────────┼────────────────┐
                  │               │                │
                  ▼               ▼                ▼
             ┌─────────┐    ┌───────────┐    ┌──────────┐
             │ GitHub  │    │   Web     │    │  Files   │
             │  Tool   │    │   Tool    │    │   Tool   │
             └─────────┘    └───────────┘    └──────────┘
                  │
                  ▼
          ┌─────────────────┐
          │ README Analyzer │
          └────────┬────────┘
                   │
                   ▼
             ┌───────────┐
             │ Groq LLM  │
             └─────┬─────┘
                   │
                   ▼
          ┌─────────────────┐
          │   Final Answer  │
          └─────────────────┘