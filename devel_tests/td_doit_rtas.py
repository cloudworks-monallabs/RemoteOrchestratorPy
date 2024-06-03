"""
this test will create a 1 super rtas and 2 subrtas.
In each rtas: the local_step_pre will write 3 files,
the ship file iter would ship those files,
remote_step_iter will read the content, compute gmd5sum, do some dash work,
and write output
fetch_files will retrieve both files
and local step post will write those to result file for the subtask

"""

from doit_rtas import RemoteTaskActionSequence, doit_taskify
import sys
from fabric import Connection, Config
from pathlib import Path
import os
from doit.tools import run_once

ipv6 = "45.76.4.30"

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
# rtas.add_ssh_user("root", fabric_conn_root)
# rtas.add_ssh_user("adming", fabric_conn_adming)
rtas.set_active_user("adming")

all_rtas = [rtas]
# ================================ end ===============================

# =================== setup tasks and dependencies ===================

def local_step_pre(task_label):
    print ("local step called: ", task_label)
    Path(f"/tmp/{task_label}_0").write_text(f"{task_label}_0")
    Path(f"/tmp/{task_label}_1").write_text(f"{task_label}_1")
    Path(f"/tmp/{task_label}_2").write_text(f"{task_label}_2")
    pass

def local_step_post(task_label, remote_file1, remote_file2, remote_file3):
    Path(f"/tmp/result_{task_label}").write_text(Path(remote_file1).read_text() +  
        Path(remote_file2).read_text()  + 
        Path(remote_file3).read_text()
    )
        
    pass

@doit_taskify(all_rtas)
def test_drive_rtas(rtas):
    
    rtas.set_task_local_step_pre(local_step_pre,
                                 "super",
                                 targets = [

                                     Path(f"/tmp/super_0"),
                                     Path(f"/tmp/super_1"),
                                     Path(f"/tmp/super_2")

                                     ],
                                 uptodate = [run_once]

                                 )
    
    rtas.set_task_ship_files_iter( [

                                     Path(f"/tmp/super_0"),
                                     Path(f"/tmp/super_1"),
                                     Path(f"/tmp/super_2")

                                     ],
                                   "/tmp"
        )
    rtas.set_task_remote_step("""cd /tmp/; touch remote_file1; echo "hello"> remote_file1; echo "hello"> remote_file2; echo "hello"> remote_file3;""",
                              targets = ["/tmp/remote_file1",
                                         "/tmp/remote_file2",
                                         "/tmp/remote_file3",
                                         
                                         
                                         ]

        )
    
    rtas.set_task_fetch_files_iter(["/tmp/remote_file1",
                                    "/tmp/remote_file2",
                                    "/tmp/remote_file3",
                                    
                                    ],
                                   "/tmp")
                                   
    rtas.set_task_local_step_post(local_step_post,
                                  "super",
                                  "/tmp/remote_file1",
                                    "/tmp/remote_file2",
                                    "/tmp/remote_file3",
                                  targets = [f"/tmp/result_super"

                                      ]
                                  )
    yield from rtas

    # ======================== create subtasks =======================

    rtas.set_new_subtask_seq(id_args=["worker_id:0"])
    task_label = "sub_workder_id:0"
    rtas.set_task_local_step_pre(local_step_pre,
                                 task_label,
                                 targets = [

                                     Path(f"/tmp/{task_label}_0"),
                                     Path(f"/tmp/{task_label}_1"),
                                     Path(f"/tmp/{task_label}_2")

                                     ],
                                 uptodate = [run_once]

                                 )
    
    rtas.set_task_ship_files_iter( [

                                     Path(f"/tmp/{task_label}_0"),
                                     Path(f"/tmp/{task_label}_1"),
                                     Path(f"/tmp/{task_label}_2")

                                     ],
                                   "/tmp"
        )
    rtas.set_task_remote_step("""cd /tmp/; touch remote_file01; echo "hello"> remote_file01; echo "hello"> remote_file02; echo "hello"> remote_file03;""",
                              targets = ["/tmp/remote_file01",
                                         "/tmp/remote_file02",
                                         "/tmp/remote_file03",
                                         
                                         
                                         ]

        )
    
    rtas.set_task_fetch_files_iter(["/tmp/remote_file01",
                                    "/tmp/remote_file02",
                                    "/tmp/remote_file03",
                                    
                                    ],
                                   "/tmp")
                                   
    rtas.set_task_local_step_post(local_step_post,
                                  task_label,
                                  "/tmp/remote_file01",
                                  "/tmp/remote_file02",
                                  "/tmp/remote_file03",
                                    
                                  targets = [f"/tmp/{task_label}"

                                      ]
                                  )
    yield from rtas

    pass

# for _ in test_drive_rtas():
#     print(_)

DOIT_CONFIG = {
    "verbosity": 2,
    
    
    }

# This chdir is essential -- doit switches to the  directory of the dodo file
os.chdir("/home/adming/DrivingRange/CloudWorks/dodo_testdb_v3")

if __name__ == "__main__":
    from doit.cmd_base import ModuleTaskLoader
    from doit.doit_cmd import DoitMain

    try:
        DoitMain(ModuleTaskLoader(sys.modules[__name__])).run(sys.argv[1:])
    except Exception as e:
        print (f"Exception happend during task pipeline execution: {e}")

    finally:
        print ("in final")


print ("calling close")
fabric_conn_root.close()
fabric_conn_adming.close()
