# kitzur_chat (frontend)

Chainlit UI for the Kitzur Shulchan Aruch RAG. Hebrew-only, right-to-left.

The app imports only the public surface of the backend:

```python
from kitzur_core import ask
```

It never touches `kitzur_core.flow`, `kitzur_core.rag`, or `kitzur_core.config` directly.

## Run

```
conda activate Chainlit
chainlit run src/kitzur_chat/app.py -w
```
