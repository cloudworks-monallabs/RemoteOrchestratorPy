#. RTAS

#. All RTAS should be part of doit_tasks.py
   - ModuleTaskLoader reads tasks from doit_tasks module
   
#. add RTAS dependency on RTAS
   .. code-block::
      @doit_taskify([codegenie_rtas], task_dep=[get_leaf_task_label(setup_remote)])
      def deploy_codegenie(rtas):

#. call remote_actions function
   
