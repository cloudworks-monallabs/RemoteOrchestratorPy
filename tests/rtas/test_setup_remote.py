import sys
from pathlib import Path
from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain
from rtas.rtas_common import (the_rtas,
                          local_workdir,
                          remote_workdir,
                          CLUSTER_RESOURCES_DATADIR,
                          adming_ssh_private_key_file,
                          FileConfig,
                          rtas_taskify,
                          deployment_remote_workdir,
                          get_leaf_task_label,
                          setup_remote_debian
                          )

from doit_extntools.precompute_remote_file_md5sum import (pickle_compute_md5_remote_target_set,
                                                          precompute_remote_files_md5
                                                          )

from RemoteOrchestratorPy import RTASExecutionError

# try:
#     # Run a simple 'whoami' command on the remote host
#     # 'hide=False' overrides your config momentarily so you can see the result
#     result = fabric_conn_adming.run('whoami', hide=False)
    
#     if result.ok:
#         print(f"--- Connection Successful! ---")
#         print(f"Connected as: {result.stdout.strip()}")
#         print(f"Target Host: {fabric_conn_adming.host}")
#     else:
#         print("Command executed but returned an error.")

# except Exception as e:
#     print(f"--- Connection Failed ---")
#     print(f"Error details: {e}")
    

import remote_actions


@rtas_taskify([the_rtas])
def setup_remote(rtas):
    yield from setup_remote_debian(rtas,
                                   local_workdir,
                                   remote_workdir,
                                   remote_actions,
                                   f"{CLUSTER_RESOURCES_DATADIR}/{adming_ssh_private_key_file}",
                                   )






@rtas_taskify([the_rtas],
              task_dep=[get_leaf_task_label(setup_remote)]
              )
def execute_remote_task(rtas):
    """
    Task sequence to download a tiny file and sync it back.
    """
    
    
    # 2. Add the remote download task (using the remote_actions.py dispatch)
    remote_task_append = rtas.set_task_remote_step_iter()
    
    # Downloading robots.txt (~1KB) instead of the kernel
    remote_task_append(
        (
            "wget_url", 
            ["https://www.google.com/favicon.ico"], 
            {"out": remote_workdir}
        ),
        label="wget_favicon_ico",
        targets=[f"{remote_workdir}/favicon.ico"]
    )

    # 3. Synchronize/Fetch the file back to the local controller
    # This treats the remote file as a dependency for the local copy
    rtas.set_task_fetch_files_iter(
        [
            FileConfig(
                Path(f"{remote_workdir}/favicon.ico"), # Remote Source
                False,                               # expand_archive
                False,                               # delete_remote
                Path("favicon.ico.from_remote") 
            )
        ],
        Path(local_workdir), # Local Base Directory
    )
    yield from rtas

rtas_by_ip = { the_rtas.ipv6: the_rtas
              }


def test_run():

    try:
        doit_main = DoitMain(ModuleTaskLoader(sys.modules[__name__]))
        precompute_remote_files_md5(rtas_by_ip)
        doit_main.run([]
                      )
        
    except Exception as e:
        print (f"Exception happend during task creation phase: {e}")
        raise e
    finally:

        print ("finished deployment workflow execution")


    if the_rtas.task_failed_abort_execution:
        raise RTASExecutionError(str(the_rtas.task_failed_exception), the_rtas)
    # Assertion 3: Verify the physical file existence and size
    assert expected_local_file.exists(), f"Target file was not fetched to {expected_local_file}"
    assert expected_local_file.stat().st_size > 0, "Target file exists but is empty"
    
    
