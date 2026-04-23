from doit_rtas import RemoteTaskActionSequence, doit_taskify
import sys
from fabric import Connection, Config
from pathlib import Path
import os
from doit.tools import run_once

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
def TASKFUNCNAME(rtas):
    def local_step_pre():
        print(f"local_step_pre called for: rtas_basename = {rtas.basename}")
    rtas.set_task_local_step_pre(local_step_pre
        )
    
    yield from rtas
    

def task_say_hello():
    def do_action():
        print("hellow")

    return { 'actions': [do_action],
             'task_dep': [ 'TASKFUNCNAME:192.168.0.102::rtas']
             

        }

DOIT_CONFIG = {
    "verbosity": 2,
    'default_tasks' :  ["say_hello",
                        
                        ]
    
    
    }
