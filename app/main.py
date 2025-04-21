import asyncio
import nest_asyncio
import os
import logging
import inspect
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import json


from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status
from gitingest import ingest_async

nest_asyncio.apply()

# Globals
WORKING_DIR = "./"
rag = None
task_status = {}
model_download_status = {}

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

class RepoRequest(BaseModel):
    repo_url: str

class QueryRequest(BaseModel):
    query: str
    mode: str = "naive"


async def initialize_rag():
    global rag
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=ollama_model_complete,
        llm_model_name="gemma3:1b",
        llm_model_max_async=4,
        llm_model_max_token_size=32768,
        llm_model_kwargs={
            "host": "http://ollama:11434",
            "options": {"num_ctx": 32768},
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=lambda texts: ollama_embed(
                texts, embed_model="nomic-embed-text", host="http://ollama:11434"
            ),
        ),
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()

def insert_sync(task_id: str, content: str):
    try:
        task_status[task_id] = "ingesting"
        rag.insert(content)
        task_status[task_id] = "completed"
        logging.info("RAG ingestion completed.")
    except Exception as e:
        task_status[task_id] = "failed"
        logging.error(f"Ingestion error: {str(e)}")

async def insert_content_into_rag(task_id: str):
    try:
        with open("downloaded.md", "r", encoding="utf-8") as file:
            content = file.read()
        await asyncio.to_thread(insert_sync, task_id, content)
    except Exception as e:
        # Just in case something unexpected happens even before threading
        task_status[task_id] = "failed"
        logging.error(f"Thread dispatch error: {str(e)}")

# Use lifespan for startup events
@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_rag()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/process-repo/")
async def process_repo(request: RepoRequest, background_tasks: BackgroundTasks):
    try:
        task_id = str(uuid.uuid4())
        task_status[task_id] = "ingesting"

        await ingest_async(request.repo_url, output="downloaded.md")
        background_tasks.add_task(insert_content_into_rag, task_id)

        return JSONResponse(content={
            "message": "Repository is being processed. You can check the task status.",
            "task_id": task_id
        })
    except Exception as e:
        logging.error(f"Repo error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    status = task_status.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": status}



@app.post("/query/")
async def query_rag(request: QueryRequest):
    try:
        result = rag.query(request.query, param=QueryParam(mode=request.mode))
        return PlainTextResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")