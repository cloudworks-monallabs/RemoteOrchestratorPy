The domain
----------

#. `pure task abstraction, metadata-driven execution, and general-purpose orchestration`

   - `General Purpose Workflow Engines`
     
#. Airflow: Data pipeline

#. Ansible : `Configuration Management`

   
#. Temporal
   - seems related
     -  execute asynchronous, long-running business logic
	- It an implementation of 
	  - Join and Fork
	    - on completion send signal to waiting task
	      - start task if signals from all upstream task is recieved

		
#. Argo Workflows
     - The surface language seem unintutive and messy at first glance
       - It is temporal but for Kubernetes containers
	 - a task is replaced with container
	   
#. Tekton
   - CI/CD over kubernetes


#. Celery
   - Does not have dependency caching
     
Comparison
----------

Are there "Enterprise" versions of RTAS?

If you ever find that pydoit/rtas is becoming too difficult to manage across hundreds of machines, IT professionals usually graduate to Configuration Management (CM) or Infrastructure as Code (IaC) tools.

    Ansible: This is the closest enterprise "big brother" to rtas. It is agentless (SSH-based) and focused on idempotency (checking state before acting). However, it uses YAML, which lacks the pure programmatic flexibility of Python's pydoit.

    SaltStack: If you need speed. It uses a "minion" (agent) on the remote side, allowing it to manage thousands of servers in seconds. It has a very powerful Python API.

    Bazel (by Google): If you want the ultimate "build system" that works across clusters. It is extremely strict and uses "Remote Execution" and "Remote Caching" to ensure that if a binary was built on Server A, Server B just downloads the result.
    
