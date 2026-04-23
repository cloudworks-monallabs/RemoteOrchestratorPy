#. The setup
   - call setup_remote_debian
   - args
     - local_workdir
     - remote_workdir,
     - remote_action_module,
     - remote_ssh_private_key,
     - local_port=18356,
			

   - example
   .. code-block::
      from RemoteOrchestratorPy import (RemoteTaskActionSequence,
                                  doit_taskify,
                                  get_leaf_task_label,
                                  FileConfig,
                                  setup_remote_debian 
                                  )

      @doit_taskify(all_rtas)
      def setup_remote(rtas):
      yield from setup_remote_debian(rtas,
				     "/home/adming/DrivingRange/CloudWorks/netboot_admin",
				     remote_workdir,
				     remote_actions,
				     "/home/adming/.ssh/id_rsa")
				   
  
