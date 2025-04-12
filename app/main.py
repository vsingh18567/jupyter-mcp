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
from app.notebook_manager import NotebooksManager
from app.types import *

app = FastAPI()
manager = NotebooksManager()


@app.post("/create_notebook", response_model=str, operation_id="create_notebook")
def create_notebook(req: CreateNotebookRequest) -> str:
    return manager.create_notebook(req.directory, req.name)


@app.post("/add_cell", response_model=JupyterNotebookCell, operation_id="add_cell")
def add_cell(req: NewJupyterCellRequest) -> JupyterNotebookCell:
    notebook = manager.get_notebook(req.filepath)
    return notebook.add_cell(req)


@app.get(
    "/get_notebook_cells",
    response_model=list[JupyterNotebookCell],
    operation_id="get_notebook_cells",
)
def get_notebook_cells(filepath: str) -> list[JupyterNotebookCell]:
    notebook = manager.get_notebook(filepath)
    return notebook.get_cells()


@app.post(
    "/execute_cell",
    response_model=JupyterNotebookCellWithOutput,
    operation_id="execute_cell",
)
def execute_cell(req: ExecuteJupyterCellRequest) -> JupyterNotebookCellWithOutput:
    notebook = manager.get_notebook(req.filepath)
    return notebook.execute_cell(req.cell_id)


mcp = FastApiMCP(
    app,
    # Optional parameters
    name="Jupyter Notebook MCP",
    description="Modify and execute Jupyter Notebooks",
    base_url="http://localhost:8000",
    describe_all_responses=True,  # Include all possible response schemas in tool descriptions
    describe_full_response_schema=True,  # Include full JSON schema in tool descriptions
)

# Mount the MCP server directly to your FastAPI app
mcp.mount()
