#. rtas is dag
   - our notion of dag is running 
     - top to bottom
       - at the bottom most node is the final task to be executed
	 
#. every rtas is bounded from top and bottom
   
   - on to the top is
     - rtas_{basename}
       - essentially there is only one prefix task for all task sequence
	 - f"{basename}_prefix"
	 
   - at the bottom of rtas is the task
     - with description `f"""{basename}:{self.ipv6}:{ "_".join([str(_) for _ in id_args])}::rtas"""`
     -

#. local_step_post has file_dep on fetch_files_iter     
#. Log info messages
   - RTAS-abort-taskgen:
     - task generation is aborted because rtas.task_failed_abort_execution was set during previous execution
   - RTAS-skip-task:
     - task execution skipped because some pre-dependent task failed execution
   - RTAS-abort-task
     - a running task is aborted due to exception
       
#. pip install
   rpyc doit-api
   
#. rpyc secure over ssl
   - server : where RpyC server is created
     - assume ssh keys are already generated
   - client : the node which will connect to the server
     - assume ssh keys are already generated
       
   -  Convert the SSH Private Key to PEM Format
       .. code-block::
	  openssl rsa -in server_privatekey -outform PEM -out server_privatekey.pem


     -  Generate a Self-Signed Certificate
	.. code-block::
	   openssl rsa -in client_privatekey -outform PEM -out client_privatekey.pem

     - Server Self-Signed Certificate
       .. code-block::
	  openssl req -new -x509 -key server_privatekey.pem -out server.cert -days 365

	  openssl req -new -x509 -key client_privatekey.pem -out client.cert -days 365


     - Server side code
       
	  
	openssl genrsa -out rootCA.key 4096

	openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1825 -out rootCA.pem

	openssl genrsa -out server.key 2048
	openssl req -new -key server.key -out server.csr
	openssl req -new -key server.key -out server.csr -config openssl.cnf
	openssl x509 -req -in server.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out server.crt -days 825 -sha256
	openssl genrsa -out client.key 2048
	openssl req -new -key client.key -out client.csr -config openssl.cnf
	openssl x509 -req -in client.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out client.crt -days 825 -sha265
	
#. rpyc secure over ssl using self certificates
   - Generate the Root CA's Private Key and root-ca-certificate
     .. code-block::
	openssl genrsa -out rootCA.key 4096

	openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1825 -out rootCA.pem

   - Generate the Server's Private Key and certificate-signing-request
     .. code-block::
	openssl genrsa -out server.key 2048
	openssl req -new -key server.key -out server.csr -config openssl.cnf

   - Sign the certificate
     .. code-block::
	openssl x509 -req -in server.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out server.crt -days 825 -sha256

   - Create client private key and csr

     .. code-block::
	openssl genrsa -out client.key 2048
	openssl req -new -key client.key -out client.csr -config openssl.cnf

     - sign the certificate
       .. code-block::
	  openssl x509 -req -in client.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out client.crt -days 825 -sha256


#. register the certs with the os and set
   sudo cp rootCA.pem /usr/local/share/ca-certificates/rootCA.crt

   sudo update-ca-certificates
   .. code-block::
      (venv) adming@raspberrypi:~/deploy_ojstack $ sudo ls -l /etc/ssl/certs | grep rootCA
      lrwxrwxrwx 1 root root     10 Jan 19 17:42 2521e240.0 -> rootCA.pem
      lrwxrwxrwx 1 root root     43 Jan 19 17:42 rootCA.pem -> /usr/local/share/ca-certificates/rootCA.crt

pip-system-certs

#. Big bug: for some reason my server.crt is self.signed :(
   - how to verify if your server.crt is self signed
     .. code-block::
	openssl verify -CAfile server.crt server.crt

	should return ok

	and
	openssl verify -CAfile rootCA.pem server.crt
	should return error
	C = IN, ST = KARNATAKA, L = BENGALURU, O = Monallabs, OU = Cloudworks, CN = monallabs.in
	error 29 at 1 depth lookup:subject issuer mismatch
	C = IN, ST = KARNATAKA, L = BENGALURU, O = Monallabs, OU = Cloudworks, CN = monallabs.in
	error 29 at 1 depth lookup:subject issuer mismatch
	C = IN, ST = KARNATAKA, L = BENGALURU, O = Monallabs, OU = Cloudworks, CN = monallabs.in
	error 29 at 1 depth lookup:subject issuer mismatch

   - lets fix it
     .. code-block::
	
	openssl req -new -key server.key -out server.csr -config openssl.cnf
#. no need for ssl authentication

#. using ssh pluvblum
   - TODO: usee ssh-agent instead of providing private key into your code
     .. code-block::
	eval $(ssh-agent)
	ssh-add ~/.ssh/id_rsa
   - 
#. you can list using
   doit  -f  /home/kabira/Development/cloudworks-monallabs/RemoteOrchestratorPy/devel_tests/devel_setup_remote.py --dir .  list --all --deps
#. Get task info
   -  doit  -f  /home/kabira/Development/cloudworks-monallabs/RemoteOrchestratorPy/devel_tests/devel_setup_remote.py --dir . info setup_remote:192.168.0.102:inner:_leaf_final_
