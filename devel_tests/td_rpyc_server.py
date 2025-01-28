import importlib
from pathlib import Path
import rpyc
import sys
from rpyc.utils.authenticators import SSLAuthenticator

# for deployment service this will come from config/env variables

workdir = Path("/tmp")
class ExecutionService(rpyc.Service):
    def __init__(self):
        pass

    def on_connect(self, conn):
        # code that runs when a connection is created
        # (to init the service, if needed)
        print("client connected")
        self.conn = conn
        pass

    def on_disconnect(self, conn):
        print("client disconnected")
        # code that runs after the connection has already closed
        # (to finalize the service, if needed)
        pass

    def exposed_copy_local_file(self, client_localpath, remotepath):
        # ask client to open file and read out the contents in chunk
        with Path(remotepath).open("wb") as fh:
            for buf in self.conn.root.file_reader(client_localpath):
                fh.write(buf)
            
        pass

    def exposed_upload_module(self, client_local_path, module_name):
        """
        
        """
        if isinstance(client_local_path, Path):
            print("This is a path instance")
        self.exposed_copy_local_file(client_local_path, workdir/f"{module_name}.py")
        spec = importlib.util.spec_from_file_location(module_name, workdir/f"{module_name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[module_name] = module
        print ("module loaded successfully")
        pass
    
    def exposed_load_module(self, module_string):
        print ("load the module")
    def exposed_exec_action(self, module_name, action_func, *args, **kwargs):
        if module_name not in sys.modules:
            raise ValueError(f"Module '{module_name}' is not loaded.")

        module = sys.modules[module_name]

        # Check if the function exists in the module
        if not hasattr(module, action_func):
            raise AttributeError(f"Function '{action_func}' not found in module '{module_name}'.")

        # Retrieve the function
        func = getattr(module, action_func)

        # Ensure it's callable
        if not callable(func):
            raise TypeError(f"'{action_func}' in module '{module_name}' is not callable.")

        # Call the function with provided arguments
        try: 
            return func(*args, **kwargs)
        except Exception as e:
            raise e


if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer, OneShotServer
    # authenticator = SSLAuthenticator(
    #     keyfile="server.key", 
    #     certfile="server.crt", 
    #     #ca_certs="/etc/ssl/certs/"  # The Root CA certificate
    #     ca_certs="/home/adming/DrivingRange/CloudWorks/deployment_service/rootCA.pem"
    # )
    # Every connection will get its own ExecutionService instance
    
    # server_handle = ThreadedServer(ExecutionService, port=int(sys.argv[1]),
    #                                #authenticator=authenticator
    #                                )
    server_handle = OneShotServer(ExecutionService, port=int(sys.argv[1]),
                                   #authenticator=authenticator
                                   )


    server_handle.start()
    print("Shutting down proxy server")
    

