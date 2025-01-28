import rpyc

service_port = 7777
# conn = rpyc.connect("192.168.0.102",
#                                          service_port)
conn = rpyc.ssl_connect("192.168.0.185",
                        
                    port=service_port,
                    keyfile="client.key",  # Client's private key
                    certfile="client.crt",  # Client's signed certificate
                    )
conn.root.load_module("alpha_beta")
conn.root.exec_action("remote_actions", "wget", "url")

#conn.root.exec_action("remote_actions", "dummy_utils", )
