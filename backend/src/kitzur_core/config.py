from pathlib import Path
import os
from dotenv import load_dotenv


def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "sorce_files").is_dir() or (parent / ".env").is_file():
            return parent
    return here.parents[3]


PROJECT_ROOT: Path = _find_project_root()

SOURCE_FILE: Path = PROJECT_ROOT / "sorce_files" / "kitzur_shulchan_aruch.txt"
SEIFIM_DIR: Path = PROJECT_ROOT / "data" / "seifim"
CHROMA_DIR: Path = PROJECT_ROOT / "chroma_db"

# Redirect CrewAI's default Chroma storage to our project-local chroma_db/.
# Must be set before any `crewai.rag.chromadb` import — that module computes
# DEFAULT_STORAGE_PATH at import time. On Windows, appdirs.user_data_dir
# returns an absolute path unchanged, so this env var effectively becomes
# the persist directory.
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["CREWAI_STORAGE_DIR"] = str(CHROMA_DIR)

load_dotenv(PROJECT_ROOT / ".env")

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

LLM_MODEL: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
EMBED_MODEL: str = "text-embedding-3-small"
COLLECTION_NAME: str = "kitzur"
