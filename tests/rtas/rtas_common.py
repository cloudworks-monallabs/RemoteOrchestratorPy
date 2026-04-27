import logging
# Configure logging
logging.basicConfig(
    filename='test_setup_remote_debian.log',        # Log file name
    level=logging.DEBUG,       # Minimum log level to capture
    #format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    format='%(levelname)-8s [%(module)s.%(funcName)s:%(lineno)d] %(message)s',
    filemode='a',               # File mode: 'a' for append, 'w' for overwrite,
    force=True
)


noisy_loggers = [
    "fabric", 
    "paramiko", 
    "invoke", 
    "session", 
    "local", 
    "rpyc"
]

for logger_name in noisy_loggers:
    logging.getLogger(logger_name).setLevel(logging.WARNING)
    
# # Silence Fabric and its underlying engine, Invoke
# logging.getLogger("fabric").setLevel(logging.WARNING)
# logging.getLogger("invoke").setLevel(logging.WARNING)
   
# # Fabric uses Paramiko for SSH, which is notoriously chatty
# logging.getLogger("paramiko").setLevel(logging.WARNING)
   
# # If you use networking libraries like urllib3 or requests
# logging.getLogger("urllib3").setLevel(logging.WARNING)


import tomllib
from RemoteOrchestratorPy import (RemoteTaskActionSequence,
                                  rtas_taskify,
                                  FileConfig,
                                  setup_remote_debian ,
                                  get_leaf_task_label
                                  )
import sys
from fabric import Connection, Config
from pathlib import Path
import os
from doit.tools import run_once
config_path = "./test_rtas.toml"
with open(config_path, "rb") as f:
   config =  tomllib.load(f)
   paths_config = config['paths']
   adming_ssh_private_key_file = paths_config['adming_ssh_private_key_file']
   deployment_remote_workdir = Path(paths_config['remote_workdir'])
   local_workdir = Path(config['paths']['local_workdir'])
   remote_workdir = Path(config['paths']['remote_workdir'])
   CLUSTER_RESOURCES_DATADIR = Path(config['paths']['cluster_resources_datadir'])

   conn_config = config['connection']
   target_server_ip = conn_config['target_server_ip']
   user = conn_config['user']



connect_kwargs = {
    "key_filename": f"{CLUSTER_RESOURCES_DATADIR}/{adming_ssh_private_key_file}",
}
fabric_config = Config(overrides={
    'connect_kwargs': connect_kwargs,
    'run': {
        'hide': True,
        'warn': True,
        'echo': True
    },
})

fabric_conn_adming = Connection(host=target_server_ip,
                                user="adming",
                                config=fabric_config
                         )

the_rtas = RemoteTaskActionSequence(target_server_ip, ("adming", fabric_conn_adming),
                                
                                os_type="linux"
                                )
DOIT_WORKDIR = os.environ['DOIT_WORKDIR']
os.chdir(DOIT_WORKDIR)
