from app.settings import app
import redis.asyncio as redis
from app.settings import logger
from app.core.response_parser import add_links
import json
import asyncio
from app.backend.controllers.messages import register_message
from app.core.utils import initialize_rag
from celery import Task


class AsyncTask(Task):
    abstract = True

    def __call__(self, *args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.run(*args, **kwargs))

    async def run(self, *args, **kwargs):
        pass


redis_client = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)


@app.task(base=AsyncTask, queue='high_priority', bind=True, max_retries=3)
async def process_documents(self, collection_name: str, files: list[str], chat_id: str):
    await logger.info("Start background task")
    RAG = initialize_rag()
    try:
        await RAG.upload_documents(collection_name=collection_name, documents=files)
        return {"status": "success", "collection_name": collection_name, "chat_id": chat_id}
    except Exception as e:
        await logger.error(f"Error processing the documents at process_documents: {e}")
        self.retry(countdown=2**self.request.retries, exc=e)


@app.task(base=AsyncTask, queue='default', bind=True, max_retries=3)
async def generate_response(self, collection_name: str, prompt: str, chat_id: str, task_id: str):
    RAG = initialize_rag()
    await logger.info(f"Task id -----> {task_id}")
    try:
        full_response = ""
        async for chunk in RAG.generate_response_stream(collection_name=collection_name, user_prompt=prompt):
            print(chunk)
            full_response += chunk
            await redis_client.rpush(f"response:{task_id}:chunks", json.dumps({"chunk": chunk}))
            await redis_client.set(f"response:{task_id}:status", "streaming")
            await asyncio.sleep(0.01)
        await logger.info(f"Full response length: {len(full_response)}, preview: {full_response[:200]}...")
        await register_message(content=await add_links(full_response), sender="assistant", chat_id=chat_id)
        await redis_client.set(f"response:{task_id}:status", "completed")
        await redis_client.expire(f"response:{task_id}:chunks", 300)
        return {"status": "success", "response": full_response, "chat_id": chat_id}
    except Exception as e:
        await logger.error(f"Error at generate_response: {e}")
        await redis_client.set(f"response:{task_id}:status", "failed")
        await redis_client.set(f"response:{task_id}:error", str(e))
        self.retry(countdown=2**self.request.retries, exc=e)