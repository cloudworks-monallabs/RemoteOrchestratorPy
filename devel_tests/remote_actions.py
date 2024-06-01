import os
import sys
from pathlib import Path

def write_file(fn):
    Path("/tmp/dask_execution.txt").write_text("executed via dask worker")
    return f"{fn}42"

