.. RemoteOrchestorPy documentation master file, created by
   sphinx-quickstart on Mon Jun  3 17:17:01 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to RemoteOrchestorPy's documentation!
=============================================

RemoteOrchestratePy provides a straightforward way to express builds and workflows over a cluster of  machines.

For the TLDR folks, the example below demonstrates how to use RemoteOrchestratePy to set up and deploy a webserver, along with a collection of websites to be hosted on it:

.. code-block::
   
   @doit_taskify(all_rtas)
   def deploy_webserver_runtime(rtas):
      rtas.set_task_local_step_pre(...)
      rta.set_task_ship_files_iter(...)
      remote_task_append = set.set_task_remote_step_iter()

      # add a series of remote steps each with its own qualifier
      remote_task_append(...)
      remote_task_append(...)
      ...

      rtas.set_task_fetch_files_iter(...)
      rtas.set_task_local_step_post(...)


      # generate tasks  for super task sequence
      yield from rtas

      # define sub rtas: e.g., rtas that configures individual websites
      for <website> in hosted_websites:
	  rtas.set_new_subtask_seq(id_args = [id(<website>)]
				       )
	  # define work for subtask sequence
	  ...
	  ...

	  # store the final task of this rtas 
	  yield from rtas

.. note::
   
   See :ref:`demo` on how to initialize `all_rtas` object --  the set of machines  as target for deployment

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. include:: ./IntroUsage.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
