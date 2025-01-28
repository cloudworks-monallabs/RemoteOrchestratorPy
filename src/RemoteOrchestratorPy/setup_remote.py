from plumbum import SshMachine
import rpyc
from rpyc.core.consts import STREAM_CHUNK
from doit.tools import run_once
from pathlib import Path
from typing import NamedTuple
# use to describe behaviour for ship and fetch file
import tempfile
import logging

logger = logging.getLogger(__name__)

import os

# Get the directory of the current file
module_dir = os.path.dirname(os.path.abspath(__file__))


class FileConfig(NamedTuple):
    file_path: str
    clean_local: bool = False
    clean_remote: bool = False
    target_path: str = None
    

service_port = 7777
class ClientService(rpyc.Service):
    def __init__(self):
        pass

    def on_connect(self, conn):
        # code that runs when a connection is created
        # (to init the service, if needed)
        print("server connected")
        pass

    def on_disconnect(self, conn):
        print("server disconnected")
        # code that runs after the connection has already closed
        # (to finalize the service, if needed)
        pass

    def exposed_file_reader(self, localpath, chunk_size=STREAM_CHUNK):
        logger.debug(f" read file {localpath}")
        assert isinstance(localpath, Path)
        
        with localpath.open("rb") as lfh:
            while True:
                buf = lfh.read(chunk_size)
                if not buf:
                    break
                yield buf

        pass
    pass

        
def init_connection(conn_resource_context):
    try:
        # Start the generator to initialize the resource
        logger.debug(" connect to remote")
        next(conn_resource_context)
    except StopIteration:
        #raise RuntimeError("Resource generator is already exhausted.")
        pass

    pass
def teardown_connection(conn_resource_context):
    try:
        # Finalize the generator to clean up resources
        logger.debug("Finally closing rpyc server and client conn")
        next(conn_resource_context)
    except StopIteration:
        pass
    pass

def setup_remote_debian(rtas,
                        local_workdir,
                        remote_workdir,
                        remote_action_module,
                        remote_ssh_private_key,
                        local_port=18356,
                        ):
    """
    remote_action_module: to be uploaded remotely
    remote_ssh_private_key: for passwordless connection between rpyc server (running on remote machine) and
                           local machine
    local_workdir: for temporary files .. we cannot use NamedTemporaryFile because it messes up task info etc.
    
    
    """

    remote_task_append = rtas.set_task_remote_step_iter()
    remote_task_append(f"mkdir {remote_workdir}", "create_workdir", uptodate=[run_once]
        )

    # assume python is already installed 
    # remote_task_append(f"doas pkg_add python-3.12.8p1", "install_python", uptodate=[run_once]
    #     )

    remote_task_append(f"cd {remote_workdir}; python3 -m venv venv", "create_python_venv", uptodate=[run_once]
        )
    # install rpyc
    remote_task_append(f"cd {remote_workdir}; . ./venv/bin/activate; pip install rpyc wget", "install_modules", uptodate=[run_once]
                       )

    yield from rtas
    
    rtas.set_new_subtask_seq(id_args=["inner_rpyc"])

    launch_service_str = f"""
#!/bin/bash

cd {remote_workdir}
    
. ./venv/bin/activate; 

# Run the command and check for errors
nohup python3 remote_execution_service.py {service_port} > remote_execution_service.log 2>&1 & 
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
    
    #with tempfile.NamedTemporaryFile(mode='w', delete=False) as launch_service_fh:
    # delete if file exists
    launch_rpyc_service_fp = Path(f"{local_workdir}/launch_rpyc_service.sh")
    if launch_rpyc_service_fp.exists():
        launch_rpyc_service_fp.unlink()
        
    with launch_rpyc_service_fp.open("w") as launch_service_fh:
        launch_service_fh.write(launch_service_str)
        launch_service_fh.flush()

    
    
    # put a teardown task to remove the file
    rtas.set_task_ship_files_iter([FileConfig(Path(f"{module_dir}/remote_execution_service.py"), False, False),
                                   FileConfig(launch_rpyc_service_fp, False, False)
                                   ],
                                  Path(remote_workdir)
                                  )
    # launch_service_fh<-- named temporary files
    # launch_service_fh.name<-- the temporary file path
    #.Path(launch_service_fh.name).name <-- basename 
    launch_service_basename = launch_rpyc_service_fp.name
    print("launch_service_basename  == ", launch_service_basename)
    remote_task_append = rtas.set_task_remote_step_iter()



    # start server
    #command = f"nohup python3 /tmp/remote_execution_service.py {service_port} > /tmp/run.log 2>&1 &  echo $!"

    def teardown(rtas):
        task_label = f"{rtas.basename}:remote_step:launch_rpyc"
        # although server is started here.
        # it will get teardown when client disconnected
        pass 

    # remote_task_append(f"cd {remote_workdir}; . ./venv/bin/activate; {command}", "launch_rpyc", teardown=[(teardown, [rtas])]
    #     )
    remote_task_append(f"cd {remote_workdir}; sh {launch_service_basename}", "launch_rpyc", teardown=[(teardown, [rtas])]
                       )

    # connect to remote rpyc and upload remote module
    def rpyc_conn_lifecycle(rtas):
        try:
            
            with SshMachine(rtas.ipv6,
                            user = "adming",
                            keyfile="/home/adming/.ssh/id_rsa"
                            ) as rem:
                with rem.tunnel(local_port, service_port) as tunnel:
                    conn = rpyc.connect("localhost",
                                        local_port,
                                        service=ClientService,
                                        config={"sync_request_timeout": 600}
                                        )
                    localpath = Path(os.path.abspath(remote_action_module.__file__))
                    
                    # if remote_action is imported from nested module then its name is fully qualified 
                    remote_action_module_name = remote_action_module.__name__.split(".")[-1]
                    conn.root.upload_module(localpath, remote_action_module_name)
                    rtas.rpyc_conn = conn
                    yield
                    pass
        except Exception as e:
            logger.error("tunneling failed: {e}")

        return True




    conn_resource_context = rpyc_conn_lifecycle(rtas)
    
    rtas.set_task_local_step_post(init_connection,
                                  conn_resource_context,
                                  #uptodate=[run_once]
                                  #teardown = [teardown_connection, (conn_resource_context)]
                                  
                                  )

    
    yield from rtas


def setup_remote_openbsd(rtas,
                         local_workdir,
                      remote_workdir,
                      remote_action_module,
                      remote_ssh_private_key,
                      local_port = 18356,
                      
                      ):
    """
    remote_action_module: to be uploaded remotely
    remote_ssh_private_key: for passwordless connection between rpyc server (running on remote machine) and
                           local machine
    
    
    """

    remote_task_append = rtas.set_task_remote_step_iter()
    remote_task_append(f"mkdir {remote_workdir}", "create_workdir", uptodate=[run_once]
        )

    remote_task_append(f"doas pkg_add python-3.12.8p1 wget", "install_python", uptodate=[run_once]
        )

    remote_task_append(f"cd {remote_workdir}; /usr/local/bin/python3 -m venv venv", "create_python_venv", uptodate=[run_once]
        )
    # install rpyc, wget
    # TODO: faric reports failed
    # remote_task_append(f"cd {remote_workdir}; . ./venv/bin/activate; pip install rpyc wget", "install_rpyc", uptodate=[run_once]
    #                    )

    yield from rtas
    
    rtas.set_new_subtask_seq(id_args=["inner"])

    launch_service_str = f"""
#!/bin/bash

cd {remote_workdir}
    
. ./venv/bin/activate; 

# Run the command and check for errors
nohup python3 remote_execution_service.py {service_port} > remote_execution_service.log 2>&1 & 
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

    launch_rpyc_service_fp = Path(f"{local_workdir}/launch_rpyc_service.sh")
    if launch_rpyc_service_fp.exists():
        launch_rpyc_service_fp.unlink()
        
    with launch_rpyc_service_fp.open("w") as launch_service_fh:
        launch_service_fh.write(launch_service_str)
        launch_service_fh.flush()

    
    # put a teardown task to remove the file
    rtas.set_task_ship_files_iter([FileConfig(Path(f"{module_dir}/remote_execution_service.py"), False, False),
                                   FileConfig(launch_rpyc_service_fp, False, False)
                                   ],
                                  Path(remote_workdir)
                                  )
    # launch_service_fh<-- named temporary files
    # launch_service_fh.name<-- the temporary file path
    #.Path(launch_service_fh.name).name <-- basename 
    launch_service_basename = Path(launch_service_fh.name).name
    remote_task_append = rtas.set_task_remote_step_iter()



    # start server
    #command = f"nohup python3 /tmp/remote_execution_service.py {service_port} > /tmp/run.log 2>&1 &  echo $!"

    def teardown(rtas):
        task_label = f"{rtas.basename}:remote_step:launch_rpyc"
        # although server is started here.
        # it will get teardown when client disconnected
        pass
    remote_task_append(f"cd {remote_workdir}; sh {launch_service_basename}", "launch_rpyc", teardown=[(teardown, [rtas])]
                       )

    # connect to remote rpyc and upload remote module
    def rpyc_conn_lifecycle(rtas):
        try: 
            with SshMachine(rtas.ipv6,
                            user = "adming",
                            keyfile="/home/adming/.ssh/id_rsa"
                            ) as rem:
                with rem.tunnel(local_port, service_port):
                    conn = rpyc.connect("localhost",
                                        local_port,
                                        service=ClientService
                                        )
                    localpath = Path(os.path.abspath(remote_action_module.__file__))
                    remote_action_module_name = remote_action_module.__name__.split(".")[-1]
                    conn.root.upload_module(localpath, remote_action_module_name)
                    rtas.rpyc_conn  = conn
                    yield
        except Exception as e:
            logger.error(f"tunneling failed: {e}")
        return True

    conn_resource_context = rpyc_conn_lifecycle(rtas)
    
    rtas.set_task_local_step_post(init_connection,
                                  conn_resource_context,
                                  #uptodate=[run_once]
                                  teardown = [(teardown_connection, [conn_resource_context])
                                              ]
                                  
                                  )
    yield from rtas
    
