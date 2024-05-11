=================
Developer docs
=================

Some notes
-----------
- remote_task has task dependency on file_to_ship
- files_to_ship task as file dependency on files_to_ship

- upload file doesn't update

  to_ship_file will be run if the remote file is not present
  but it won't update if local file is present
  
Internal Details
----------------



Remote Task Action Sequence: RTAS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Arguments
++++++++++

Positional
''''''''''
 - rt_tag
   all generated task will have rt_tag 
 - ipv6
 - id_args : subtask name is defined using id_args:, kind-of like primary key 
  
Optional
'''''''''
 - remote_work_dir="/tmp",
 - local_work_dir="/tmp",
 - target_nodeset=None,
 - pre_deps=[],

   Tasks on which RTAS dependes on
 - calc_dep=None,
 - fabric_conn=None

				 

The 5 generated tasks
+++++++++++++++++++++

dummy_task
''''''''''
   Is only generated only non-None calc_dep argument

local_steps_pre
'''''''''''''''

  - pre_deps is the dependency
  - targets if defined are set
  - file_dep if defined is set

ship_files    
''''''''''
  - file_dep : files_to_ship 
  - uptodate : custom checker that checks on remote machine if files exists
  

