import os
import sys
from pathlib import Path

import wget


def wget_url(base_url):
    raise ValueError
    fn = wget.download(base_url)
    print (f"Downloded {fn}")



def write_file(fn):

    Path("/tmp/dask_execution.txt").write_text("executed via dask worker")
    return f"{fn}42"

