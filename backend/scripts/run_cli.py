"""Backend-only REPL for the Kitzur Shulchan Aruch RAG.

No Chainlit. Uses only the public API (`kitzur_core.ask`). Type a Hebrew or
English question, get a Hebrew answer with sources. Empty line / Ctrl-D / Ctrl-C
exits.
"""
from __future__ import annotations
import sys

from kitzur_core import ask


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    print("Kitzur Shulchan Aruch RAG — backend CLI")
    print("Type a question (Hebrew or English). Empty line to exit.\n")
    while True:
        try:
            q = input("שאלה / Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not q:
            return 0
        try:
            answer = ask(q)
        except Exception as e:
            print(f"\n[error] {e}\n", file=sys.stderr)
            continue
        print()
        print(answer)
        print("\n" + "─" * 60 + "\n")


if __name__ == "__main__":
    sys.exit(main())
