"""
wrappers around fabric commands to help PyDoIT to do actions on remote machine
"""
import doit
from doit.tools import run_once
from pathlib import Path
import os

from doit_extntools import RemoteFilesDep, RemoteCommandError

from plumbum import SshMachine
from .setup_remote import ClientService, service_port, FileConfig, module_dir

import logging

logger = logging.getLogger(__name__)



    

        
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

def teardown_shipfile(fabric_conn, fileconfig, target_path):
    if fileconfig.clean_local:
        fileconfig.file_path.unlink()

    if fileconfig.clean_remote:
        print("cleaning up remote file")
        result = fabric_conn.run(f"rm -f {target_path(fileconfig)}", warn=True)
        if result.ok:
            logger.info(f"File {target_path(fileconfig)} deleted successfully.")
        else:
            logger.debug(f"Failed to delete file: {target_path(fileconfig)}")

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

def log_command_exec_status_rpyc(cmdstr, result, task_label, rtas):
    logger = logging.getLogger(__name__)
    # False indicates the task generally failed
    
    logger.info(f"IP Address: {rtas.ipv6} || {task_label} || For command: {cmdstr}")
    logger.info(result)
    rtas.remote_task_results[task_label] = ("Success", result)
    return True


    
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
            

 
# client service but         


class RTASExecutionError(Exception):
    """Custom exception for task execution failures."""
    def __init__(self, message, rtas):
        super().__init__(message)
        self.rtas = rtas

