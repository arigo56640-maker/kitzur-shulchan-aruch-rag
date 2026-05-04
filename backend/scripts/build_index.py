"""Build (or refresh) the persistent ChromaDB index from data/seifim/.

Run once after `ingest.py` to embed all seif files into the persistent Chroma store
at `chroma_db/`. After this runs, runtime callers (run_cli.py, the Chainlit app)
can query the existing collection without re-embedding.
"""
from __future__ import annotations
import sys

from kitzur_core.config import CHROMA_DIR, SEIFIM_DIR
from kitzur_core.rag import build_search_tool


def main() -> int:
    if not SEIFIM_DIR.exists() or not any(SEIFIM_DIR.glob("*.md")):
        print(
            f"No seif files at {SEIFIM_DIR}. Run backend/scripts/ingest.py first.",
            file=sys.stderr,
        )
        return 1

    print(f"Ingesting {SEIFIM_DIR} -> {CHROMA_DIR} ...")
    tool = build_search_tool(ingest=True)
    print("Ingestion complete.")

    query = "השכמת הבוקר"
    print(f"\nSanity query: {query!r}")
    result = tool._run(query)
    print(result[:800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
