import rpyc
from plumbum import SshMachine
import os
import inspect
from pathlib import Path
from rpyc.core.consts import STREAM_CHUNK
service_port = 7777
# conn = rpyc.connect("192.168.0.102",
#                                          service_port)
local_port = 18356
import remote_actions

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

    def exposed_read_file(self):
        print("Hurray ==>  exposed_read_file called " )
        pass

    def exposed_file_reader(self, localpath, chunk_size=STREAM_CHUNK):
        assert isinstance(localpath, Path)
        
        with localpath.open("rb") as lfh:
            while True:
                buf = lfh.read(chunk_size)
                if not buf:
                    break
                yield buf

        
with SshMachine("localhost",
                user = "adming",
                keyfile="/home/adming/.ssh/id_rsa"
                ) as rem:


    #conn = rpyc.utils.factory.ssh_connect(rem, service_port)
    # create tunnel between remote_host:service_port to local_port on localhost
    with rem.tunnel(local_port, service_port):
        conn = rpyc.connect("localhost",
                             local_port,
                             service=ClientService
                             )
        # conn = rpyc.classic.connect("localhost", port=local_port)
        #localpath = os.path.dirname(os.path.abspath(inspect.getsourcefile(remote_actions)))
        target_module = remote_actions
        localpath = absolute_path = Path(os.path.abspath(target_module.__file__))
        remotepath = "/tmp/remote_actions.py"
        
        print (Path(localpath))
        conn.root.upload_module(localpath, target_module.__name__)
        #conn.root.copy_local_file(Path(localpath)/"remote_actions.py", remotepath)
         # #
         # rpyc.utils.classic.upload(conn, Path(localpath)/"remote_actions.py", "/tmp/remote_actions.py")
        #conn = rpyc.classic.connect("localhost", port=local_port)
    #rpyc.utils.classic.upload_module(conn, remote_actions)
    

# from rpyc.utils.classic import upload_module
# from plumbum import SshMachine

# import remote_actions  # Ensure this module is in the local Python path

# # Configuration
# remote_host = "localhost"  # Replace with the remote host
# remote_user = "adming"     # Replace with the SSH username
# private_key_path = "/home/adming/.ssh/id_rsa"
# service_port = 18861       # Port where RPyC server is running on the remote machine

# # Establish SSH connection
# with SshMachine(remote_host, user=remote_user, keyfile=private_key_path) as rem:
#     # Forward the remote port locally
#     local_port = rem.tunnel(service_port)
    
#     # Connect to the forwarded port using rpyc.classic.connect
#     conn = rpyc.classic.connect("localhost", port=local_port)
    
#     # Upload the module
#     upload_module(conn, remote_actions)

#     print("Module uploaded successfully!")

#     # Perform additional remote operations if needed
#     print(conn.modules.sys.platform)

#     # Close the connection
#     conn.close()
