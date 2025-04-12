import os
import random
import string
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell
from jupyter_client import KernelManager
import uuid

from app.types import (
    JupyterNotebookCell,
    JupyterNotebookCellWithOutput,
    NewJupyterCellRequest,
)


def get_random_string(
    length: int, allowed_chars: str = string.ascii_letters + string.digits
):
    """
    Generates a random string of specified length using characters from the allowed_chars set.

    Args:
        length: The desired length of the random string.
        allowed_chars: A string containing characters allowed in the random string.

    Returns:
        A random string of the specified length.
    """
    return "".join(random.choice(allowed_chars) for _ in range(length))


class NotebookSession:
    def __init__(self):
        self.km = KernelManager()
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready()

    def shutdown(self):
        self.kc.stop_channels()
        self.km.shutdown_kernel()

    def restart(self):
        self.shutdown()
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready()


def save(func):
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)
        args[0]._save()
        return ret

    return wrapper


class Notebook:

    class CellIdMapping:
        def __init__(self):
            self.ids_to_idx = {}
            self.idx_to_ids = []

        def add_cell(self, cell_id: str, index: int):
            self.ids_to_idx[cell_id] = index
            self.idx_to_ids.append(cell_id)

        def get_index(self, cell_id: str) -> int:
            return self.ids_to_idx[cell_id]

        def get_cell_id(self, index: int) -> str:
            return self.idx_to_ids[index]

        def id_exists(self, cell_id: str) -> bool:
            return cell_id in self.ids_to_idx

    def __init__(self, directory: str, name: str):
        self.path = os.path.join(directory, name)
        self.nb = new_notebook()
        self.cell_ids = []
        self.session = NotebookSession()
        self.id_mapping = self.CellIdMapping()
        if not os.path.exists(directory):
            os.makedirs(directory)
        self._save()

    def _save(self):
        with open(self.path, "w") as f:
            nbformat.write(self.nb, f)

    @save
    def add_cell(self, cell: NewJupyterCellRequest) -> JupyterNotebookCell:
        while True:
            cell_id = get_random_string(5)
            if cell_id not in self.id_mapping.ids_to_idx:
                break
        self.id_mapping.add_cell(cell_id, len(self.nb.cells))
        if cell.cell_type == "code":
            self.nb.cells.append(new_code_cell(cell.source))
        elif cell.cell_type == "markdown":
            self.nb.cells.append(new_markdown_cell(cell.source))
        return JupyterNotebookCell(
            id=cell_id, source=cell.source, cell_type=cell.cell_type, filepath=self.path
        )

    @staticmethod
    def _parse_msg(msg: dict) -> nbformat.NotebookNode:
        obj = nbformat.NotebookNode()
        obj.output_type = msg["msg_type"]
        obj.execution_count = 1
        obj.metadata = {}
        obj.update(**msg["content"])
        return obj

    @save
    def execute_cell(self, cell_id: str) -> JupyterNotebookCellWithOutput:
        if not self.id_mapping.id_exists(cell_id):
            raise ValueError("Cell not found")
        cell = self.nb.cells[self.id_mapping.get_index(cell_id)]
        msg_id = self.session.kc.execute(cell.source)
        outputs = []
        cell.outputs = []
        while True:
            msg = self.session.kc.get_iopub_msg()
            if msg["parent_header"].get("msg_id") != msg_id:
                continue
            msg_type = msg["msg_type"]
            if msg_type == "status" and msg["content"]["execution_state"] == "idle":
                break
            elif msg_type == "execute_result":
                outputs.append(msg["content"]["data"]["text/plain"])
                cell.outputs.append(Notebook._parse_msg(msg))
            elif msg_type == "stream":
                outputs.append(msg["content"]["text"])
                cell.outputs.append(Notebook._parse_msg(msg))
            elif msg_type == "error":
                outputs.append("\n".join(msg["content"]["traceback"]))
                cell.outputs.append(Notebook._parse_msg(msg))
        print(self.nb.cells[self.id_mapping.get_index(cell_id)])
        return JupyterNotebookCellWithOutput(
            id=cell_id,
            source=cell.source,
            cell_type=cell.cell_type,
            output=outputs,
            filepath=self.path,
        )

    def get_cells(self) -> list[JupyterNotebookCell]:
        return [
            JupyterNotebookCell(
                id=cell.id,
                source=cell.source,
                cell_type=cell.cell_type,
                filepath=self.path,
            )
            for cell in self.nb.cells
        ]

    def restart_kernel(self):
        self.session.restart()


class NotebooksManager:
    def __init__(self):
        self.notebooks = {}

    def create_notebook(self, directory: str, name: str) -> str:
        nbk = Notebook(directory, name)
        self.notebooks[nbk.path] = nbk
        return nbk.path

    def get_notebook(self, nb_id: str) -> Notebook:
        if nb_id not in self.notebooks:
            raise ValueError("Notebook not found")
        return self.notebooks[nb_id]
