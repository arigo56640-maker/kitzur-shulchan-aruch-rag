# kitzur_core (backend)

Backend library for the Kitzur Shulchan Aruch RAG.

## Public API

```python
from kitzur_core import ask, build_flow

answer = ask("מה לעשות מיד עם ההתעוררות?")
```

Everything else under `kitzur_core.*` is internal.

## Scripts

- `scripts/ingest.py` — `sorce_files/kitzur_shulchan_aruch.txt` → `data/seifim/*.md` (one file per seif)
- `scripts/build_index.py` — warms `chroma_db/` via DirectorySearchTool
- `scripts/run_cli.py` — REPL that calls `ask()` (no Chainlit)
