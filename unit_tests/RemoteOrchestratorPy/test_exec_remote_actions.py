import tomllib
from RemoteOrchestratorPy import (RemoteTaskActionSequence,
                                  doit_taskify,
                                  get_leaf_task_label,
                                  FileConfig,
                                  setup_remote_openbsd

                                  )
import sys
from fabric import Connection, Config
from pathlib import Path
import os
from doit.tools import run_once
import logging

from doit_extntools.precompute_remote_file_md5sum import (pickle_compute_md5_remote_target_set,
                                                          precompute_remote_files_md5
                                                          )


# Configure logging
logging.basicConfig(
    filename='unit_test.log',        # Log file name
    level=logging.DEBUG,       # Minimum log level to capture
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    filemode='a'               # File mode: 'a' for append, 'w' for overwrite
)





config_path = "./test_remote_orchestor_py.toml"
with open(config_path, "rb") as f:
   config =  tomllib.load(f)
   paths_config = config['paths']
   adming_public_key_file = paths_config['adming_public_key_file']
   deployment_remote_workdir = Path(paths_config['remote_workdir'])
   local_workdir = Path(config['paths']['local_workdir'])
   CLUSTER_RESOURCES_DATADIR = Path(config['paths']['cluster_resources_datadir'])

   conn_config = config['connection']
   target_server_ip = conn_config['target_server_ip']
   user = conn_config['user']

connect_kwargs = {
    "key_filename": f"{CLUSTER_RESOURCES_DATADIR}/{adming_public_key_file}",
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

rtas = RemoteTaskActionSequence(target_server_ip, ("adming", fabric_conn_adming),
                                
                                os_type="linux"
                                )
rtas_by_ip = {}
rtas_by_ip[target_server_ip] = rtas
rtas.set_active_user("adming")

all_rtas = [rtas]

import remote_actions



@doit_taskify(all_rtas,
              )

def setup_remote(rtas):
    yield from setup_remote_openbsd(rtas,
                                    local_workdir,  
                                    deployment_remote_workdir,
                                    remote_actions,
                                    f"{CLUSTER_RESOURCES_DATADIR}/{adming_public_key_file}"
                                    )


    


# complete setup_remote task before execution of this task    
@doit_taskify(all_rtas,
              task_dep=[get_leaf_task_label(setup_remote)]
)
def rtas_test(rtas):

   # ========================= local step pre ========================
    def step_local_step_pre(rtas):
        print("perform local_step_pre")

    rtas.set_task_local_step_pre(step_local_step_pre, rtas)

    # ============================== end =============================


    # ============================== end =============================

    # ========================== fetch files =========================


    # ============================== end =============================
    
    def step_local_step_post(rtas):
        print("perform local_step_post")

    rtas.set_task_local_step_post(step_local_step_post, rtas)
    
    yield from rtas
    



def task_final():
    def do_action():
        print("performing final task action")

    def teardown():
        print("performing final task teardown")
        
    return { 'actions': [do_action],
             'task_dep': [get_leaf_task_label(rtas_test)
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
DOIT_WORKDIR = Path(os.environ['DOIT_WORKDIR'])

os.chdir(DOIT_WORKDIR)
# first load the tasks so that precompute-remote-files-md5
doit_main = DoitMain(ModuleTaskLoader(sys.modules[__name__]))
precompute_remote_files_md5(rtas_by_ip)
doit_main.run(sys.argv[1:])




