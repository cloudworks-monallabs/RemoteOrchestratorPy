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
