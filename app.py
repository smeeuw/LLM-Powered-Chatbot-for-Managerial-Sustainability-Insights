import chainlit as cl
from query import create_query_pipeline
from llama_index.embeddings.ollama import OllamaEmbedding
from config import EMBED_MODEL
from llama_index.core import Settings

Settings.embed_model = EMBED_MODEL

qp = create_query_pipeline()

def sync_func(message: cl.Message):
    response = qp.run(
        query=message.content
    )
    return str(response)

@cl.on_message
async def main(message: cl.Message):
    # Wrap sync_func in a lambda to defer its execution
    async_func = cl.make_async(lambda: sync_func(message))
    answer = await async_func()
    await cl.Message(
        content=answer,
    ).send()





