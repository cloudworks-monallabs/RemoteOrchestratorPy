from doit_rtas import (RemoteTaskActionSequence, doit_taskify, get_leaf_task_label, FileConfig)
import sys
from fabric import Connection, Config
from pathlib import Path
import os
from doit.tools import run_once
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',        # Log file name
    level=logging.INFO,       # Minimum log level to capture
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    filemode='a'               # File mode: 'a' for append, 'w' for overwrite
)

# Test the logger
logging.debug('This is a debug message')
logging.info('This is an info message')
logging.warning('This is a warning message')
logging.error('This is an error message')
logging.critical('This is a critical message')





ipv6 = "192.168.0.102"

# === create rtas with fabric conn for 2 ssh users root and adming ===
cluster_resources_datadir="/home/adming/cluster_resources"
adming_public_key_file = "adming_ssh_rsa_public_key"
connect_kwargs = {
    "key_filename": f"{cluster_resources_datadir}/{adming_public_key_file}",
}
fabric_config = Config(overrides={
    'connect_kwargs': connect_kwargs,
    'run': {
        'hide': True,
        'warn': True,
        'echo': True
    },
})

fabric_conn_root = Connection(host=ipv6,
                              user="root",
                              config=fabric_config
                         )

fabric_conn_adming = Connection(host=ipv6,
                                user="adming",
                                config=fabric_config
                         )

rtas = RemoteTaskActionSequence(ipv6, ("adming", fabric_conn_adming),
                                
                                ("root", fabric_conn_root)
                                )
rtas.set_active_user("adming")

all_rtas = [rtas]


@doit_taskify(all_rtas)
def TASKSHIPFILES(rtas):
    rtas.set_task_ship_files_iter([

        FileConfig(Path(f"/tmp/ship_to_remote.txt"),
                   True,
                   True,
                   Path("/home/adming/deploy_ojstack/renamed_on_target"))
                                     ],
                                   Path("/tmp")
                                  )
        
    
    yield from rtas
    


#print("task_label = ",     TASKWITHEXCEPTION.__leaf_final_task_label__)


def task_say_hello():
    def do_action():
        print("hellow")

    def teardown():
        print("in teardown")
        
    return { 'actions': [do_action],
             #'task_dep': [get_leaf_task_label(TASKWITHEXCEPTION)]
             'task_dep': [#"TASKSHIPFILES_leaf_final_"
                 get_leaf_task_label(TASKSHIPFILES)
                          ],
             'teardown': [teardown]

        }
from doit.reporter import ConsoleReporter

class ErrorReporter(ConsoleReporter):
    def add_failure(self, task, exception):
        super().add_failure(task, exception)
        print(f"Task {task.name} failed. Exception: {exception}")
        
DOIT_CONFIG = {
    "verbosity": 2,
    'reporter': ErrorReporter,
    'default_tasks' :  ["say_hello",
                        
                        ]
    
    
    }

import os
from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain
import sys
os.chdir("/home/adming/DrivingRange/CloudWorks/deployment_service")
DoitMain(ModuleTaskLoader(sys.modules[__name__])).run(sys.argv[1:])



