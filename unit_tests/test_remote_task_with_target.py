from RemoteOrchestratorPy import (RemoteTaskActionSequence,
                                  doit_taskify,
                                  get_leaf_task_label,
                                  FileConfig,
                                  setup_remote_debian 
                                  )
import sys
from fabric import Connection, Config
from pathlib import Path
import os
from doit.tools import run_once
import logging

# Configure logging
logging.basicConfig(
    filename='unit_test.log',        # Log file name
    level=logging.DEBUG,       # Minimum log level to capture
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    filemode='a'               # File mode: 'a' for append, 'w' for overwrite
)





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


fabric_conn_adming = Connection(host=ipv6,
                                user="adming",
                                config=fabric_config
                         )

rtas = RemoteTaskActionSequence(ipv6, ("adming", fabric_conn_adming),
                                
                                os_type="linux"
                                )
rtas.set_active_user("adming")

all_rtas = [rtas]

import remote_actions

# debian linux setup remote

remote_workdir = "/home/adming/deployment_service"    

@doit_taskify(all_rtas)
def setup_remote(rtas):
    yield from setup_remote_debian(rtas, "/home/adming/DrivingRange/CloudWorks/deployment_service",
                                 remote_workdir, remote_actions, "/home/adming/.ssh/id_rsa")


# complete setup_remote task before execution of this task    
@doit_taskify(all_rtas, task_dep=[get_leaf_task_label(setup_remote)])
def remote_with_target(rtas):
    remote_task_append = rtas.set_task_remote_step_iter()
    #  argument order
    #  the tuple for remote func execution command
    #  task label
    #  task kwargs
    remote_task_append(("wget_url", [f"https://cdn.openbsd.org/pub/OpenBSD/snapshots/arm64/man76.tgz"],
                        {}

                        ), "download_tgz", 
                       targets=[f"{remote_workdir}/man76.tgz"]
                       )
        
    
    yield from rtas
    


#print("task_label = ",     TASKWITHEXCEPTION.__leaf_final_task_label__)


def task_final():
    def do_action():
        print("hellow")

    def teardown():
        print("in teardown")
        
    return { 'actions': [do_action],
             #'task_dep': [get_leaf_task_label(TASKWITHEXCEPTION)]
             'task_dep': [#"TASKSHIPFILES_leaf_final_"
                 #get_leaf_task_label(TASKSFETCHFILES)
                 get_leaf_task_label(remote_with_target)
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
    'default_tasks' :  ["final",
                        
                        ]
    
    
    }

import os
from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain
import sys
os.chdir("/home/adming/DrivingRange/CloudWorks/deployment_service")
DoitMain(ModuleTaskLoader(sys.modules[__name__])).run(sys.argv[1:])



"""
- test refetch w
"""
