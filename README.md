# Kitzur Shulchan Aruch — RAG

Hebrew-only, right-to-left RAG chatbot over the Kitzur Shulchan Aruch.

## Layout

- `backend/` — `kitzur_core` library (CrewAI Flow + DirectorySearchTool + ChromaDB). No UI dependencies.
- `frontend/` — `kitzur_chat` library (Chainlit UI). Imports only `kitzur_core.api`.
- `sorce_files/` — source text (one pipe-delimited file).
- `data/seifim/` — generated per-seif Markdown chunks (gitignored).
- `chroma_db/` — persistent vector store (gitignored).

## Setup (one-time)

```
conda activate Chainlit
pip install -e backend -e frontend
cp .env.example .env
# fill in OPENAI_API_KEY
```

## Run

```
conda activate Chainlit

# 1. Ingest the source into per-seif Markdown files
python backend/scripts/ingest.py

# 2. Build the persistent Chroma index
python backend/scripts/build_index.py

# 3a. Backend-only CLI smoke test
python backend/scripts/run_cli.py

# 3b. Chainlit UI — must be run from frontend/ so .chainlit/config.toml is picked up
cd frontend
chainlit run src/kitzur_chat/app.py -w
```

The Chainlit UI runs at http://localhost:8000.
