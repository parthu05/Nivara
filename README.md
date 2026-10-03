# Nivara

Nivara is a local-first wellness companion for supportive conversation and simple mood and journal tracking. It is a v1 prototype, not therapy, diagnosis, or emergency care.

## V1

- Sign up with an email, password, and country; show a country-specific support resource where one is configured.
- Chat with Gemini in the cloud by default, with relevant passages retrieved from `data/knowledge_base`.
- Save mood check-ins and journal entries in SQLite, scoped to the signed-in account.

The knowledge base is indexed in the background when the app starts. For local Ollama use, install the model locally; for cloud mode, set `GEMINI_API_KEY` in `.env` and set `LLM_PROVIDER=gemini`.

## Run Locally

Requirements: Python and PowerShell on Windows. For local Ollama use, install [Ollama](https://ollama.com/download).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# For Gemini cloud mode
# set LLM_PROVIDER=gemini
# set GEMINI_API_KEY=your_key_here

# For local Ollama mode
# ollama pull llama3.2
# ollama pull nomic-embed-text
uvicorn app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>. Update the provider settings in `.env` as needed.

## Possible Next Versions

These are ideas, not current features: faster streamed chat and broader verified helpline coverage; mood trends, reminders, and journal export; tailored check-ins for use cases such as student stress or sleep routines.
