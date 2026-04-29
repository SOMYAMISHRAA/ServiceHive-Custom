# 🐝 ServiceHive

**An agentic lead-qualification chatbot for AutoStream** — built with LangGraph, Google Gemini, and Flask.

ServiceHive orchestrates a multi-node conversational workflow that classifies intent, retrieves product knowledge via RAG, and captures qualified leads through structured extraction.

---

## ⚙️ Architecture

```
User Message
     │
     ▼
┌────────────┐
│  Classify   │  ← Intent Detection (Gemini Structured Output)
└─────┬──────┘
      │
  ┌───┼────────────┐
  ▼   ▼            ▼
GREETING  RAG   LEAD_CAPTURE
  │       │         │
  ▼       ▼         ▼
 END     END    Collect → Tool → END
```

Each turn flows through a **StateGraph** with memory-backed checkpointing for multi-turn dialogue.

---

## 📂 Structure

```
ServiceHive/
├── agent.py            # LangGraph state machine — nodes, edges, routing
├── app.py              # Flask server with REST endpoints
├── knowledge_base.md   # RAG source: plans, pricing, policies
├── requirements.txt    # Python dependencies
├── .env                # GOOGLE_API_KEY (user-supplied)
├── static/
│   ├── style.css       # Dark-themed UI stylesheet
│   └── script.js       # Frontend chat & session handling
└── templates/
    └── index.html      # Chat interface template
```

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
echo GOOGLE_API_KEY="your-key" > .env
python app.py
```

Runs at **`http://localhost:5000`**.

---

## 🧠 Components

| Module | Role |
|---|---|
| **agent.py** | Intent classification, greeting, RAG, and lead capture nodes |
| **app.py** | Flask routes with UUID session threading |
| **knowledge_base.md** | Product data for the RAG node |

## 🔑 Dependencies

**LangGraph** · **LangChain + Google GenAI** · **Flask** · **python-dotenv**

---

*Agentic workflow with deterministic routing and structured LLM outputs.*
