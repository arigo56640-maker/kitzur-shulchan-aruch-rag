"""Chainlit UI for the Kitzur Shulchan Aruch RAG.

Hebrew-only, right-to-left. Imports only the public API of kitzur_core.
"""
from __future__ import annotations

import chainlit as cl

from kitzur_core import ask

WELCOME = (
    "ברוכים הבאים! "
    "שאלו אותי כל שאלה על קיצור שולחן ערוך — "
    "אענה בעברית עם ציטוט מדויק של הסעיף שממנו נלקחה התשובה."
)


@cl.on_chat_start
async def on_chat_start() -> None:
    await cl.Message(content=WELCOME).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    answer = await cl.make_async(ask)(message.content)
    await cl.Message(content=answer).send()
