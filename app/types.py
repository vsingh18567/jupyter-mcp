from enum import Enum
from pydantic import BaseModel, Field


class CellType(str, Enum):
    CODE = "code"
    MARKDOWN = "markdown"


class NewJupyterCellRequest(BaseModel):
    filepath: str = Field(
        ..., description="The path to the notebook that the cell belongs to"
    )
    cell_type: CellType = Field(
        ..., description="The type of the cell (code or markdown)"
    )
    source: str = Field(..., description="The source code/markdown of the cell")


class CreateNotebookRequest(BaseModel):
    directory: str = Field(..., description="The directory to create the notebook in")
    name: str = Field(..., description="The name of the notebook")


class ExecuteJupyterCellRequest(BaseModel):
    filepath: str = Field(
        ..., description="The path to the notebook that the cell belongs to"
    )
    cell_id: str = Field(..., description="The id of the cell to execute")


class JupyterNotebookCell(NewJupyterCellRequest):
    id: str = Field(..., description="The id of the cell")


class JupyterNotebookCellWithOutput(JupyterNotebookCell):
    output: list[str] = Field(
        ..., description="The text outputs of the cell, if it has been executed"
    )
