Journal
-------

#. :timestamp:`2025-01-14 19:52:25` added `self.task_failed_abort_execution`

TODO
----
#. incorporate long running task
   .. code-block::
      from doit.tools import LongRunning

      def task_top():
	  cmd = "top"
	  return {'actions': [LongRunning(cmd)],}
  
#. setup
   - for Homelab is different from 
   - setup for vps that is fresh install
   - setup of vps with prebaked image
   - TODO: we need to use calc_dep
   

get dependecy of a taks
-----------------------

doit -f   /home/kabira/Development/cloudworks-monallabs/RemoteOrchestratorPy/devel_tests/test_task_exception.py --dir .  info TASKWITHEXCEPTION_leaf_final_



developement guide
------------------


rtas things
~~~~~~~~~~~
#. rtas.rpyc_conn  = conn
   
