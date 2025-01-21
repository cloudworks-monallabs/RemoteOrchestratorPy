import rpyc
import sys
from rpyc.utils.authenticators import SSLAuthenticator

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

    def exposed_client_callback(self):
        # callback for the client 
        self.conn.root.read_file()
        pass
    
    def exposed_load_module(self, module_string):
        print ("load the module")


if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    # authenticator = SSLAuthenticator(
    #     keyfile="server.key", 
    #     certfile="server.crt", 
    #     #ca_certs="/etc/ssl/certs/"  # The Root CA certificate
    #     ca_certs="/home/adming/DrivingRange/CloudWorks/deployment_service/rootCA.pem"
    # )
    # Every connection will get its own ExecutionService instance
    server_handle = ThreadedServer(ExecutionService, port=int(sys.argv[1]),
                                   #authenticator=authenticator
                                   )


    server_handle.start()
    print("Shutting down proxy server")
    

