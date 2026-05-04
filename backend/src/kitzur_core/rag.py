"""DirectorySearchTool wired to the project's persistent ChromaDB.

`build_search_tool(ingest=True)` ingests `data/seifim/` on construction; this is the
slow path used by `scripts/build_index.py`. `build_search_tool(ingest=False)` only
opens the existing persistent collection — used at runtime so each new process
doesn't re-embed 2,763 files.
"""
from __future__ import annotations

# NOTE: importing .config first ensures CREWAI_STORAGE_DIR is set before any
# crewai.rag.chromadb import below.
from .config import (
    COLLECTION_NAME,
    EMBED_MODEL,
    OPENAI_API_KEY,
    SEIFIM_DIR,
)

from crewai_tools import DirectorySearchTool
from crewai_tools.tools.directory_search_tool.directory_search_tool import (
    FixedDirectorySearchToolSchema,
)

_RUNTIME_DESCRIPTION = (
    "חיפוש סמנטי בקיצור שולחן ערוך. "
    "מקבל שאילתה בעברית ומחזיר את הסעיפים הרלוונטיים ביותר "
    "עם כותרות סימן וסעיף."
)


def _build_config() -> dict:
    return {
        "vectordb": {
            "provider": "chromadb",
            "config": {},
        },
        "embedding_model": {
            "provider": "openai",
            "config": {
                "api_key": OPENAI_API_KEY,
                "model_name": EMBED_MODEL,
            },
        },
    }


def build_search_tool(ingest: bool = False) -> DirectorySearchTool:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and fill in your key."
        )

    common = dict(
        config=_build_config(),
        collection_name=COLLECTION_NAME,
        limit=6,
        similarity_threshold=0.3,
    )

    if ingest:
        return DirectorySearchTool(directory=str(SEIFIM_DIR), **common)

    tool = DirectorySearchTool(**common)
    tool.args_schema = FixedDirectorySearchToolSchema
    tool.description = _RUNTIME_DESCRIPTION
    return tool
