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
   
