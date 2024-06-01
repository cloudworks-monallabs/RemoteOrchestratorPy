"""
wrappers around fabric commands to help PyDoIT to do actions on remote machine
"""
import doit

from pathlib import Path
import os

import logging
logger = logging.getLogger(__name__)




def get_ref_name(trec):
    """
    """


    return f"""{trec['basename']}:{trec['name']}"""


def ship_file(fabric_conn,
              file_to_ship,
              dest_dir
              ):
    try: 
        logger.info(f"start ship file {file_to_ship}")
        fabric_conn.put(file_to_ship, dest_dir)
        logger.info(f"end ship file {file_to_ship}")
    except Exception as e:
        logger.debug(f"FILE-ship-FAILURE: {file_to_ship} due to {e}")
        raise e
    pass


def fetch_file(fabric_conn,
               file_to_fetch,
               fetch_dir
              ):
    try:
        local_fp = str(Path(fetch_dir)/Path(file_to_fetch).name)
        logger.info(f"start fetch file {file_to_fetch}")
        fabric_conn.get(file_to_fetch, local_fp)
        logger.info(f"end fetch file {file_to_fetch}")
        
    except Exception as e:
        logger.debug(f"FILE-Fetch-FAILURE: {file_to_fetch} due to {e}")
        raise e

        
    pass

def log_command_exec_status(cmdstr, result, task_label, ipv6):
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    logger = logging.getLogger(__name__)
    if not stderr:    
        logger.info(f"IP Address: {ipv6} || {task_label} || For command: {cmdstr}")
        logger.info(stdout)
        
        return "Success"

    else:
        logger.error(f"IP Address: {ipv6} || {task_label} || For command: {cmdstr}")
        logger.error(stderr)

        return "Failed"
            

 
        


