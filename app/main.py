from enum import Enum
import uuid
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import random
import string

import os
import subprocess
from loguru import logger
from pydantic import BaseModel, Field
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor
from jupyter_client import kernelspec
from app.notebook_manager import NotebookManager
from app.types import *

app = FastAPI()
manager = NotebookManager()


@app.post("/create_notebook")
def create_notebook(req: CreateNotebookRequest) -> str:
    return manager.create_notebook(req.directory, req.name)


@app.post("/add_cell")
def add_cell(req: NewJupyterCellRequest) -> JupyterNotebookCell:
    notebook = manager.get_notebook(req.filepath)
    return notebook.add_cell(req)


@app.get("/get_notebook_cells")
def get_notebook_cells(filepath: str) -> list[JupyterNotebookCell]:
    notebook = manager.get_notebook(filepath)
    return notebook.get_cells()


@app.post("/execute_cell")
def execute_cell(req: ExecuteJupyterCellRequest) -> JupyterNotebookCellWithOutput:
    notebook = manager.get_notebook(req.filepath)
    return notebook.execute_cell(req.cell_id)


mcp = FastApiMCP(
    app,
    # Optional parameters
    name="My API MCP",
    description="My API description",
    base_url="http://localhost:8000",
)

# Mount the MCP server directly to your FastAPI app
mcp.mount()
