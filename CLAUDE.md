# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Hebrew-only, right-to-left RAG chatbot over the Kitzur Shulchan Aruch. Stack is fixed: **Python 3.11.15 · Chainlit (UI) · CrewAI Flows (orchestration) · CrewAI `DirectorySearchTool` (RAG) · ChromaDB (persistent local store) · gpt-4o-mini (LLM) · `text-embedding-3-small` (embedder) · `.env` for secrets**.

The active design plan lives at `C:\Users\Arie\.claude\plans\architecture-tech-stack-iterative-boot.md` — read it before making structural changes.

## Two-library monorepo

The codebase is split into **two top-level sibling libraries**, each with its own `pyproject.toml`:

- **`backend/`** — package `kitzur_core` (CrewAI Flow + RAG + Chroma config). Zero Chainlit dependency.
- **`frontend/`** — package `kitzur_chat` (Chainlit UI). Imports **only** `from kitzur_core import ask`.

The boundary is one-way and enforced by code review:
- Nothing under `backend/` may `import chainlit`.
- Nothing under `frontend/` may import `kitzur_core.flow`, `kitzur_core.rag`, or `kitzur_core.config` — only the public surface `kitzur_core.ask` / `kitzur_core.build_flow` (re-exported from `backend/src/kitzur_core/__init__.py`).

Shared on-disk artifacts (`data/seifim/`, `chroma_db/`) live at the repo root and their paths are owned by `kitzur_core.config` so the frontend never touches the filesystem layout.

## Environment — always activate the Chainlit conda env

The exact Python version (3.11.15) and pinned package versions are only available in the conda env named `Chainlit` at `C:\Users\Arie\anaconda3\envs\Chainlit\`. The base anaconda env (Python 3.13) will not work — `crewai==1.14.4` and `chainlit==2.11.1` are installed only in the Chainlit env.

Every Python command must start with `conda activate Chainlit` (or use the explicit interpreter path).

## Common commands

From the repo root, with `conda activate Chainlit`:

```
# One-time editable install of both libraries
pip install -e backend -e frontend

# Ingest the source text into per-seif Markdown files (data/seifim/)
python backend/scripts/ingest.py

# Build the persistent ChromaDB index (chroma_db/) — embeds 2,763 seifim via OpenAI
python backend/scripts/build_index.py

# Backend-only REPL (no Chainlit)
python backend/scripts/run_cli.py

# Chainlit UI (RTL, Hebrew-only) — MUST be launched from frontend/ so the
# .chainlit/config.toml in that directory is picked up; otherwise Chainlit
# falls back to defaults and the Hebrew title, language, and custom CSS are
# silently ignored.
cd frontend
chainlit run src/kitzur_chat/app.py -w
```

There is no test suite. Verification is end-to-end at each iteration of the plan.

## Critical gotcha: `CREWAI_STORAGE_DIR` must be set before any `crewai.rag.chromadb` import

`crewai.rag.chromadb.constants.DEFAULT_STORAGE_PATH` is computed **at module import time** via `appdirs.user_data_dir(get_project_directory_name(), "CrewAI")`. On Windows, `appdirs.user_data_dir` returns an absolute path unchanged when given one, so we set `CREWAI_STORAGE_DIR=<absolute path to chroma_db/>` in `backend/src/kitzur_core/config.py` **before** `load_dotenv` and **before** any other module imports `crewai.*`.

Do not move that env-var assignment, and do not pass `settings=Settings(...)` directly into `RagToolConfig["vectordb"]["config"]`: chromadb 1.1.1's `Settings` is pydantic v1, but `ChromaDBConfig` validates with pydantic v2, which raises `BaseModel.validate() takes 2 positional arguments but 3 were given`. Always rely on the env var to redirect storage and pass an empty `config: {}` for `vectordb`.

## crewai-tools 1.14.4 config schema (NOT embedchain)

The `DirectorySearchTool` config in this version is the new `RagToolConfig` shape, not the embedchain dict:

```python
{
  "vectordb":         {"provider": "chromadb", "config": {}},
  "embedding_model":  {"provider": "openai", "config": {"api_key": ..., "model_name": "text-embedding-3-small"}},
}
```

Retrieval breadth is controlled by `limit=` and `similarity_threshold=` on the tool itself (top-level kwargs to `DirectorySearchTool(...)`), not inside the config dict. Current values are `limit=6, similarity_threshold=0.3`. Hebrew embeddings via `text-embedding-3-small` are lexically sensitive (`התעוררות` and `השכמה` score very differently for the same chapter), so we keep `top_k=6` modestly wide and rely on the agent's backstory to retry with rephrased queries when the first candidate set is irrelevant. If you raise the threshold higher, expect more "no source found" answers for questions whose phrasing diverges from the source's terminology.

`build_search_tool()` in `backend/src/kitzur_core/rag.py` has two modes:
- `ingest=True` — passes `directory=str(SEIFIM_DIR)`, which triggers ingestion on construction (slow). Used by `build_index.py` exactly once.
- `ingest=False` (default) — opens the existing persistent collection without re-embedding. Used at runtime so each new process doesn't re-embed 2,763 files. After construction we replace `tool.args_schema` with `FixedDirectorySearchToolSchema` so the agent only sees `search_query` and cannot pass a directory.

## Chromadb warmup is load-bearing — do not remove

`backend/src/kitzur_core/api.py:_warmup_chroma()` builds a throwaway tool and issues a dummy `_run(search_query="warmup")` before `KitzurFlow()` constructs the agent's tool. Without this, the very first chromadb client built in the process (which would otherwise be the agent's tool) ends up in a state where every query returns `"No relevant content found."` even though the collection has 2,763 documents — the symptom is the agent loops 3 times calling its tool, gets nothing back each time, and falls into the "no source found" branch. The warmup keeps a module-level reference to the throwaway tool so its chromadb client stays cached for the lifetime of the process. **Don't `del` it, don't make it local-scope, don't try to "clean it up".**

For the same reason, **don't construct `chromadb.PersistentClient(path=str(CHROMA_DIR))` directly for diagnostics**. chromadb caches one client per path with the first settings it sees; a vanilla diagnostic client will "steal" the slot and the next CrewAI adapter to come along raises `An instance of Chroma already exists for ... with different settings`. If you need to peek at the collection, do it through the warmed-up `_warmup_tool.adapter._client` or via a separate, throwaway path.

## Chainlit config gotcha — don't write a partial config.toml

Chainlit 2.11 refuses to load `.chainlit/config.toml` if any expected section is missing — it errors with `Your config file '...' is outdated. Please delete it and restart the app to regenerate it.` So either provide all of `[project]`, `[features]`, `[features.slack]`, `[features.spontaneous_file_upload]`, `[features.audio]`, `[features.mcp]`, `[features.mcp.sse|streamable-http|stdio]`, `[UI]`, `[meta]`, or delete the file, run Chainlit once to auto-generate the template, and patch in customizations.

The page title (`<title>...</title>`) comes from `[UI] name`, NOT `[project] name`. The `[project] name` is metadata only.

## Source data and chunking strategy

- Source: `sorce_files/kitzur_shulchan_aruch.txt` (the typo "sorce" is intentional — preserved). Pipe-delimited: `siman_field|seif_letter|text`. The `siman_field` looks like `סימן א - דיני השכמת הבוקר ובו ז' סעיפים:`.
- `backend/scripts/ingest.py` parses this, computes the gematria value of the Hebrew siman/seif letters (handles geresh/gershayim, includes 5 final-letter aliases), strips the `ובו ... סעיפים` suffix, and emits `data/seifim/{siman_idx:03d}__{seif_idx:03d}.md` with content:
  ```
  # סימן {siman_letter} - {chapter_title}
  ## סעיף {seif_letter}

  {seif_text}
  ```
- 2,763 seif files across 221 distinct simanim — exactly the structure of the Kitzur. Each `.md` file = exactly one Chroma chunk.
- The chunking decision (per-seif, NOT per-siman) is load-bearing: long simanim exceed the 8,191-token limit of `text-embedding-3-small` and would force silent re-splitting; per-seif also enables exact `(סימן X, סעיף Y)` citations.

## Output format and Hebrew-only contract

The agent (`backend/src/kitzur_core/flow.py`) is constrained by a long Hebrew backstory that mandates:
1. **Always answer in Hebrew**, even when the question is in English (translate internally).
2. **Answer-then-source layout** — answer paragraph, blank line, then a sentence of the form `התשובה שעניתי לך מבוססת על {chapter_title} (סימן X, סעיף Y):`, followed by the **verbatim** seif text from the retrieved chunk.
3. **Multi-query rephrasing** — if the first search returns no relevant seifim, the agent retries with up to two alternative Hebrew phrasings using the source's terminology (e.g. "התעוררות" → "השכמת הבוקר", "מודה אני", "נטילת ידים שחרית"). Hebrew embeddings via `text-embedding-3-small` are sensitive to lexical choice, so this matters.

The frontend renders RTL via `frontend/.chainlit/config.toml` pointing at `frontend/public/custom.css`, which sets `direction: rtl` on body/messages/input but keeps `pre, code` LTR.

## Working directory and OneDrive

The project lives under `c:\Users\Arie\OneDrive\AI_Dev6\kitzur\`. Be aware that OneDrive may sync/lock files mid-write occasionally; if a Chroma file appears corrupted, retry the operation rather than rebuilding the index.
