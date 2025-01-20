"""
wrappers around fabric commands to help PyDoIT to do actions on remote machine
"""
import doit
from doit.tools import run_once
from pathlib import Path
import os
import tempfile
from doit_extntools import RemoteFilesDep, RemoteCommandError
import logging
logger = logging.getLogger(__name__)

from typing import NamedTuple
# use to describe behaviour for ship and fetch file
class FileConfig(NamedTuple):
    file_path: str
    clean_local: bool = False
    clean_remote: bool = False
    target_path: str = None

    
    
def get_ref_name(trec):
    """
    """
    return f"""{trec['basename']}:{trec['name']}"""


def ship_file(fabric_conn,
              file_to_ship,
              dest_path
              ):
    """
    dest_path: a Path like expression
    """
    try:
        fabric_conn.put(file_to_ship, str(dest_path))
    except Exception as e:
        logger.debug(f"FILE-ship-FAILURE: {file_to_ship} due to {e}")
        raise e
    pass


def fetch_file(fabric_conn,
               file_to_fetch,
               target_path
              ):
    try:
        #local_fp = str(Path(fetch_dir)/Path(file_to_fetch).name)
        fabric_conn.get(str(file_to_fetch), str(target_path))
        
    except Exception as e:
        logger.debug(f"FILE-Fetch-FAILURE: {file_to_fetch} due to {e}")
        raise e

        
    pass

def teardown_shipfile(fabric_conn, fileconfig):
    if fileconfig.clean_local:
        print("cleaning up local file")
        fileconfig.file_path.unlink()

    if fileconfig.clean_remote:
        print("cleaning up remote file")
        result = fabric_conn.run(f"rm -f {fileconfig.target_path}", warn=True)
        if result.ok:
            logger.info(f"File {fileconfig.target_path} deleted successfully.")
        else:
            logger.debug(f"Failed to delete file: {fileconfig.target_path}")

def teardown_fetchfile(fabric_conn, fileconfig):
    if fileconfig.clean_local:
        print("cleaning up local file")
        fileconfig.target_path.unlink()

    if fileconfig.clean_remote:
        print("cleaning up remote file")
        result = fabric_conn.run(f"rm -f {fileconfig.file_path}", warn=True)
        if result.ok:
            logger.info(f"File {fileconfig.file_path} deleted successfully.")
        else:
            logger.debug(f"Failed to delete file: {fileconfig.file_path}")            
    
def log_command_exec_status(cmdstr, result, task_label, rtas):
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    logger = logging.getLogger(__name__)
    # False indicates the task generally failed
    
    if not stderr:    
        logger.info(f"IP Address: {rtas.ipv6} || {task_label} || For command: {cmdstr}")
        logger.info(stdout)
        rtas.remote_task_results[task_label] = ("Success", stdout)
        return True

    else:
        logger.error(f"IP Address: {rtas.ipv6} || {task_label} || For command: {cmdstr}")
        logger.error(stderr)
        rtas.remote_task_results[task_label] = ("Error", stderr)

        
        #return False
        raise RemoteCommandError("remote command execution failed", result.return_code, stderr)
            

 
        


class RTASExecutionError(Exception):
    """Custom exception for task execution failures."""
    def __init__(self, message, rtas):
        super().__init__(message)
        self.rtas = rtas





import os

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
service_port = 7777
def setup_remote(rtas, remote_workdir, remote_upload_file):
    """
    remote_upload_file: user provided pycode file that needs to be upload to remote server;
    its functions are going to be called during execution
    
    """

    launch_service_str = f"""
#!/bin/bash

cd {remote_workdir}
    
. ./venv/bin/activate; 

# Run the command and check for errors
nohup python3 /tmp/remote_execution_service.py {service_port} > /tmp/run.log 2>&1 & 
pid=$!

# Wait briefly to allow any immediate errors to surface
sleep 1

# Check if the process is still running
if ! kill -0 $pid 2>/dev/null; then
    echo -1  >&2  # Return -1 if the process failed to start
    exit 1
fi

# Return the PID if the process is running
echo $pid
exit 0
    """
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as launch_service_fh:
        launch_service_fh.write(launch_service_str)
        launch_service_fh.flush()

    
    # Example usage
    config = FileConfig(filename="example.txt")
    print(config.filename)  # Outputs: example.txt

    
    # put a teardown task to remove the file
    rtas.set_task_ship_files_iter([FileConfig(f"{current_file_directory}/remote_execution_service.py", False, True),
                                   FileConfig(launch_service_fh.name, True, True)
                                   ],
                                  "/tmp"
                                  )
    launch_service_basename = Path(launch_service_fh.name).name
    remote_task_append = rtas.set_task_remote_step_iter()

    remote_task_append(f"mkdir {remote_workdir}", "create_workdir", uptodate=[run_once]
        )
    remote_task_append(f"cd {remote_workdir}; python3 -m venv venv", "create_python_venv", uptodate=[run_once]
        )

    # install rpyc
    remote_task_append(f"cd {remote_workdir}; . ./venv/bin/activate; pip install rpyc", "install_rpyc", uptodate=[run_once]
        )

    # start server
    #command = f"nohup python3 /tmp/remote_execution_service.py {service_port} > /tmp/run.log 2>&1 &  echo $!"

    def teardown(rtas):
        task_label = f"{rtas.basename}:remote_step:launch_rpyc"
        print("result of launch = ", rtas.remote_task_results[task_label])
        print("now teardown the remote RPyC server")
    # remote_task_append(f"cd {remote_workdir}; . ./venv/bin/activate; {command}", "launch_rpyc", teardown=[(teardown, [rtas])]
    #     )
    remote_task_append(f"cd {remote_workdir}; sh /tmp/{launch_service_basename}", "launch_rpyc", teardown=[(teardown, [rtas])]
                       )
