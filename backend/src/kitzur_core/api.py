_flow_singleton = None
_warmup_tool = None


def _warmup_chroma():
    """Force the persistent chromadb client to fully initialize.

    Without this, the very first chromadb client built in a process (which
    will be the agent's tool's adapter) ends up in a state where queries
    return 'No relevant content found.' even though the collection has
    documents. Building a tool and issuing a throwaway query ahead of the
    Agent's construction primes the per-path client cache so the agent's
    own tool sees a working client. We keep a reference on the module to
    prevent garbage collection from clearing the cache.
    """
    global _warmup_tool
    if _warmup_tool is not None:
        return
    from .rag import build_search_tool
    _warmup_tool = build_search_tool(ingest=False)
    try:
        _warmup_tool._run(search_query="warmup")
    except Exception:
        pass


def build_flow():
    global _flow_singleton
    if _flow_singleton is None:
        _warmup_chroma()
        from .flow import KitzurFlow
        _flow_singleton = KitzurFlow()
    return _flow_singleton


def ask(question: str) -> str:
    return build_flow().kickoff(inputs={"question": question})
