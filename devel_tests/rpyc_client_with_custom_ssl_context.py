import ssl
from rpyc.core.stream import SocketStream
from rpyc.utils.factory import connect_stream
from rpyc.core.service import VoidService, MasterService, SlaveService
import socket

host="localhost"
port=7777

service=VoidService
config={}
def ssl_connect(**kwargs):
    if kwargs.pop("ipv6", False):
        kwargs["family"] = socket.AF_INET6
    s = SocketStream._connect(host, port, **kwargs)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_cert_chain(certfile="client.crt", keyfile="client.key")
    ssl_context.load_verify_locations(cafile="rootCA.pem")
    s2 = ssl_context.wrap_socket(s, server_hostname=host)
    return connect_stream(SocketStream(s2), service, config)

ssl_connect()
