Background and Overview:
========================

`Pydoit  <https://pydoit.org/>`_ is a Python-based build automation tool that offers a clean, Pythonic approach to defining tasks and their dependencies. Like other build tools, it analyzes dependencies to determine the correct execution order for the necessary tasks and runs them efficiently.

Pydoit provides a range of standard and custom constructs for defining task dependencies, including ``file_dep``, ``task_dep``, ``targets``, ``run_once``, ``uptodate``, ``calc_dep``, and ``create_after``. These constructs offer a flexible and robust way to manage complex workflows. Here's an overview with examples:

- **file_dep**: Specifies file dependencies for a task, ensuring tasks are executed only when their dependent files have changed.

  Example:

  .. code-block:: python

      def task_compile():
          return {
              'file_dep': ['source.c'],
              'targets': ['output.o'],
              'actions': ['gcc -c source.c -o output.o']
          }

- **task_dep**: Defines dependencies between tasks, ensuring proper execution order.

  Example:

  .. code-block:: python

      def task_build():
          return {
              'task_dep': ['compile'],
              'actions': ['gcc output.o -o program']
          }

- **targets**: Identifies the output files produced by a task, helping pydoit determine if the task needs to be rerun.

  Example:

  .. code-block:: python

      def task_convert():
          return {
              'file_dep': ['data.csv'],
              'targets': ['data.json'],
              'actions': ['csvtojson data.csv > data.json']
          }

- **uptodate** : Allows custom conditions to be defined for checking whether a task is up-to-date.

  Example:

  .. code-block:: python

      def task_backup():
          return {
              'actions': ['backup_tool --run'],
              'uptodate': [lambda: os.path.exists('backup_done')]
          }

	  
  - `pydoit` provided callables :  These callables can be used with `uptodate` to define conditions for checking if a task needs to be re-executed:

    - `run_once`: execute a task only once (used for tasks without dependencies)
    - `result_dep`:  check if the result of another task has changed
    - `timeout`: indicate that a task should “expire” after a certain time interval
    - `config_changed`: check for changes in a “configuration” string or dictionary
    - `check_timestamp_unchanged()`: check access, status change/create or modify timestamp of a given file/directory

    
- **calc_dep**:  Compute the task depdency as a separate task. Also see `delayed task execution <https://pydoit.org/task-creation.html#delayed-task-creation>`_

  Example:

  .. code-block:: python

      def task_process():
          return {
              'calc_dep': ['dep_calculator'],
              'actions': ['process_data.sh']
          }

      def task_dep_calculator():

	      def do_action():

		  return {'task_dep': ...}


	  return { 'actions': [do_action],

		   ...
		   ...
		 }


- **create_after** : Task creation is deferred until a target task has completed.
  An example scenario where this is useful: Suppose you are working on a pipeline where the first task generates a list of files, and subsequent tasks need to process those files. Since the list of files is unknown until the first task runs, you can use create_after to defer the creation of processing tasks until the file-generation task is completed.
  
  Example:

  .. code-block:: python

     import glob

     from doit import create_after


     @create_after(executed='early', target_regex='.*\.out')
     def task_build():
	 for inf in glob.glob('*.in'):
	     yield {
		 'name': inf,
		 'actions': ['cp %(dependencies)s %(targets)s'],
		 'file_dep': [inf],
		 'targets': [inf[:-3] + '.out'],
		 'clean': True,
	     }

     def task_early():
	 """a task that create some files..."""
	 inter_files = ('a.in', 'b.in', 'c.in')
	 return {
	     'actions': ['touch %(targets)s'],
	     'targets': inter_files,
	     'clean': True,
	 }
    

    
		  

These constructs make pydoit a powerful tool for managing intricate task dependencies in an efficient and Pythonic way.

RemoteOrchestratePy: Extending PyDoit for remote operations
===========================================================

RemoteOrchestratePy builds on Pydoit to enable build/make features for orchestrating IT commands over a cluster of remote machines. By integrating pydoit with Fabric and Dash, RemoteOrchestratePy simplifies the process of writing and managing automation scripts for remote machine operations. It extends Pydoit's capabilities to handle remote execution seamlessly, allowing users to define tasks that run across multiple machines with ease. This integration makes it possible to automate complex IT operations involving multiple remote hosts, ensuring efficient and reliable orchestration of tasks.


Key Features
~~~~~~~~~~~~

Compared to other build tools like make, bazel, maven, etc., RemoteOrchestratePy stands out in following manner:

- **Better Coding Ergonomics**:
   
  - Avoids the need for learning a new language for builds/automation.
  - Leverages Python syntax and constructs.
  - Minimal boilerplate.
  - Express task dependencies cleanly and in straightforward manner
  - Easy to read, maintain, modify, and extend.
    
- **General Purpose**:
  
  - Not limited to IT workloads -- RemoteOrchestratePy is capable of handling any tasks that can expressed using Python or command line scripts.
  - Suitable for both simple and complex build expression involving multiple remote machines.

- **Fine Grained**:
  
  - Allows precise control over each step in the workflow without unnecessary verbosity

- **Extends to Remote Machines**:
  
  - Is able to  define tasks that depend on the completion of actions executed on remote machines.
  - Ensures tasks are executed in the correct order based on remote and local dependencies.

- **Super and Subtask sequence**

  - Hierarchical task management with super and subtask sequences.
  - Super task sequences manage broad, overarching services or functions.
  - Subtask sequences manage specific details under a super task sequence.

- **Supports Dask to remotely run python script**
   
  - Requires no python file logistic handling
  - Use of Python codes, instead of bash command strings, makes it trivally easy to run complex workflows on remote directly from local
  - Supports  PyDoit file task dependencies even though task is running remotely.
     
    



	    
Workflow for operating on remote machine
========================================

In RemoteOrchestratePy, a workflow that involves a remote machine is called RemoteTaskActionSequence or RTAS/rtas for short. A RTAS consists of five phases in following sequence:

- local step pre
- ship files
- remote steps
- fetch files
- local step post

An rtas should have  work (action) defined for at least one of the phases. 

#. **Local Step Pre**: This phase involves initial preparations and operations performed locally before any interaction with the remote machine. Typical tasks might include generating necessary files, setting up configurations, or performing initial computations.

#. **Ship Files**: During this phase, files either generated or needed from the local environment or other workflow files  are transferred to the remote machine. This ensures that the remote environment has all the necessary data and resources to perform its tasks.

#. **Remote Steps**: This phase encompasses all the operations executed on the remote machine. Operations can be expressed as series of strings which are executed within shell of remote machine. Alternatively, you can define a function that uses dask to run python script remotely.  

#. **Fetch Files**: In this phase, the outputs or results produced by the remote steps are retrieved from the remote machine back to the local environment. This ensures that the local environment has access to the processed data for further use or analysis.

#. **Local Step Post**: The final phase involves any concluding tasks that need to be performed locally after retrieving files from the remote machine. This might include further processing of data, generating reports, or cleaning up temporary files used during the workflow.

Each phase is designed to encapsulate a specific part of the workflow, providing a structured approach to managing tasks across local and remote environments. Note that in any given RTAS, one or more of these phases can be optional or missing, depending on the specific requirements of the workflow.

..
  .. note::

     If there are multiple RTAS or if within a single rtas there are multiple sub-rtas then a setup (or prefix) and teardown (final) task is required as well to encapsulate the generated task sequence. 



Super and sub task sequence
~~~~~~~~~~~~~~~~~~~~~~~~~~~
RTAS supports notion of super and sub task sequence.

A super task sequence is a higher-level task that involves setting up a broad, overarching service or function. For example, setting up a web server runtime environment would be a super task sequence. This task sequence includes installing the necessary software, setting up runtime configurations, and ensuring that the service is up and running.

A subtask sequence, on the other hand, is a more specific and detailed sequence of tasks that falls under the umbrella of the super task sequence. For example, configuring individual websites being served by the web server would be subtask sequences. Each subtask sequence might include setting up the site configuration files, setting permissions, and deploying content specific to each website.

This hierarchical structure allows for modular and organized task management, making complex IT operations more manageable.

      
Usage/API
=========

All functionalities of RemoteOrchestratorPy is accessed via `RemoteTaskActionSequence` and decorator `doit_taskify`.

`doit_taskify`  is a helper decorator to eliminate
some of boilerplate code. First, we show API usage
without the decorator with boilerplate code and
next we show the use of doit_taskify that makes
the code cleaner and less verbose.



Installation
~~~~~~~~~~~~

To install RemoteOrchestratePy clone the repo and include the code path in the PYTHONPATH enviornment variable.


.. code-block:: bash
   pip install doit patchwork dask[distributed]
   git clone git@github.com:cloudworks-monallabs/PyDoIt-ExtnTools.git
   git clone git@github.com:cloudworks-monallabs/RemoteOrchestratorPy.git

#. Add both repos path to `PYTHONPATH`
   
Running
~~~~~~~

#. First fire dask worker on the target nodes

   .. code-block::

      python3 -m venv venv
      . ./venv/bin/activate
      pip install dask[distributed]
      dask scheduler
      dask worker 192.168.0.102:8786
      
#. Run pydoit+RemoteOrchestratorPy code

   .. code-block::

      python  ~/RemoteOrchestratorPy/devel_tests/td_doit_rtas.py
      

APIs for RemoteTaskActionSequence
=================================


Constructor
~~~~~~~~~~~

The class RemoteTaskActionSequence is initialized with
constructor that takes ip address and list of tuple consisting of  ssh user and fabric conn.


.. py:class:: RemoteTaskActionSequence
   :noindex:

   :param ipv6: The IP address of the remote machine.
   :type ipv6: str
   :param args: Variable number of positional arguments. Each args is a tuple of SSH username and corresponding Fabric connection.
   :type args: tuple
   :noindex:

      
An example showing initialization of RemoteTaskActionSequence with for a single remote machine with two ssh users: `root` and `adming`.

.. code-block:: python

   import sys
   import os
   from doit_rtas import RemoteTaskActionSequence, doit_taskify

   from fabric import Connection, Config
   from pathlib import Path

   from doit.tools import run_once

   connect_kwargs = {
   "key_filename": <path-to-ssh-public-key-file>,
   }
   
   fabric_config = Config(overrides={
   'connect_kwargs': connect_kwargs,
   'run': {
        'hide': True,
        'warn': True,
        'echo': True
    },
    })


   fabric_conn_root = Connection(host=ipv6,
                         user="root",
                         config=fabric_config
                         )

   fabric_conn_adming = Connection(host=ipv6,
                         user="adming",
                         config=fabric_config
                         )
		
   rtas = RemoteTaskActionSequence(ipv6,
                                  ('root', fabric_conn_root),
				  ('adming', fabric_conn_adming)
   
		)

		
set_active_user
~~~~~~~~~~~~~~~

   
Sets the active SSH user for the RemoteTaskActionSequence.

    
   .. py:function:: set_active_user(user="admin")
      :noindex:


      :param user: The SSH username to set as active. Defaults to "adming".
      :type user: str
      :raises AssertionError: If the provided user is not found in the SSH users and Fabric connections.


set_super_task_seq
~~~~~~~~~~~~~~~~~~

 Setup a new task sequence with label `basename` qualified with `id_args`.

 .. py:function:: set_super_task_seq(self, basename, id_args=[])
    :noindex:



set_new_subtask_seq
~~~~~~~~~~~~~~~~~~~

Sets up a new subtask sequence on the target node with additional qualifiers.

.. py:function:: set_new_subtask_seq(self, id_args= [])
   :noindex:

   :param id_args: A list of identifiers for the subtask sequence.
   :type id_args: list
		          
set_task_local_step_pre
~~~~~~~~~~~~~~~~~~~~~~~

    Sets the local step pre-function for a task in the RemoteTaskActionSequence.
    
.. py:function:: set_task_local_step_pre(step_func, *args, **kwargs)
   :noindex:
      
   :param step_func: The function to be executed as the local step pre-function.
   :type step_func: callable
   :param args: Positional arguments to be passed to the `step_func`.
   :type args: tuple
   :param kwargs: Task dependency attributes such as `targets`, `file_dep`, `uptodate`, `task_dep`
   :type kwargs: dict


set_task_ship_files_iter
~~~~~~~~~~~~~~~~~~~~~~~~

Generates tasks per given file to ship to remote destination. The local file is treated as file dependency
and remote is treated as target for the task

    
.. py:function:: set_task_ship_files_iter(files_to_ship, dest_dir, **kwargs)
   :noindex:

   :param files_to_ship: A list of file paths to be shipped.
   :type files_to_ship: list of str
   :param dest_dir: The destination directory on the remote machine where the files will be shipped.
   :type dest_dir: str
   :param kwargs: Task dependency attributes such as `targets`, `file_dep`, `uptodate`, `task_dep`
   :type kwargs: dict


set_task_remote_step_iter
~~~~~~~~~~~~~~~~~~~~~~~~~

 Returns a function `remote_task_append` used to append a new remote task to the sequence.

 .. py:function:: set_task_remote_step_iter
    :noindex:
       
    :returns: A function `remote_task_append` to append a new remote task to the sequence.
    :rtype: function


remote_task_append
%%%%%%%%%%%%%%%%%%

The `remote_task_append` function is used to add a new task to the sequence of remote tasks. 
It takes a command (`cmd`), a label (`label`), and additional arguments and keyword arguments.

- If `cmd` is a string, it will be executed via Fabric's `run` function on the remote machine.

- If `cmd` is a function, it is assumed to use Dask to run Python code remotely.


.. py:function:: remote_task_append(cmd, label, *args, **kwargs)
   :noindex:

   :param cmd: The command to be executed as the remote task. If a string, it will be executed via Fabric's `run` function. If a function, it is assumed to use Dask to run Python code remotely.
   :type cmd: str or function
   :param label: A label for the task.
   :type label: str
   :param args: arguments if cmd is function
   :type args: 
   :param kwargs: task dependency arguments like `file_dep`, `targets`, etc
   :type kwargs: dict		 
		 

Using Dask to execute remote step
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

The code snippet show how to use dask to
execute python code on remote machine.
Assume the file `remote_actions.py` has code as follows:

.. code-block:: python
		
   import os
   import sys
   from pathlib import Path

   def write_file(fn):
       Path("/tmp/dask_execution.txt").write_text("executed via dask worker")
       return f"{fn}42"

Create function `do_remote_action`: as follows:

.. code-block:: python
		
   import remote_actions
   def do_remote_action(remote_file_path):
     future = client.submit(remote_actions.write_file, remote_file_path)
     print(future.result())

Now, to turn this into a pydoit task:

.. code-block:: python

   task_remote_step_append(do_remote_action,
                            "remote_file1",
                            "/tmp/remote_file1",
                            targets = ["/tmp/remote_file1"]
                            )
			    
See, working with Dask section, on setting up Dask with RemoteOrchestratorPy.



set_task_fetch_files_iter
~~~~~~~~~~~~~~~~~~~~~~~~~
Creates tasks, one per given file to fetch from the remote machine to a local directory. 

	
.. py:function:: set_task_fetch_files_iter(files_to_fetch, local_dir="/tmp")
   :noindex:
	    
   :param files_to_fetch: A list of file paths to be fetched from the remote machine.
   :type files_to_fetch: list of str
   :param local_dir: The local directory where the files will be fetched to. Defaults to "/tmp".
   :type local_dir: str

		 
set_task_local_step_post
~~~~~~~~~~~~~~~~~~~~~~~~
Sets the given function to be executed as a task as part of
local step post phase.

    
.. py:function:: set_task_local_step_post(self, step_func, *args, **kwargs):
   :noindex:

   :param step_func: The function to be executed as the local step post-function.
   :type step_func: callable
   :param args: Additional positional arguments to be passed to the `step_func`.
   :type args: tuple
   :param kwargs: task dependency arguments.
   :type kwargs: dict

		 
Demo: A complete workflow
=========================


Initialize RTAS
~~~~~~~~~~~~~~~

.. code-block:: python

   from doit_rtas import RemoteTaskActionSequence, doit_taskify
   import sys
   from fabric import Connection, Config
   import os
   from doit.tools import run_once

   ipv6 = "<>"

   connect_kwargs = {
   "key_filename": "<>"
   }
   fabric_config = Config(overrides={
   'connect_kwargs': connect_kwargs,
    'run': {
        'hide': True,
        'warn': True,
        'echo': True
   },
   })

   fabric_conn_root = Connection(host=ipv6,
                         user="root",
		config=fabric_config
                )

   fabric_conn_adming = Connection(host=ipv6,
                         user="adming",
                         config=fabric_config
                         )

   rtas = RemoteTaskActionSequence(ipv6, ("root",     fabric_conn_root),
		("admin", fabric_conn_admin
		)
		
   rtas.set_active_user("admin")


Define a doit task using RTAS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The example code defines both super and sub rtas.


.. code-block:: python

   def task_showcase_rtas(all_rtas):
    """
    all_rtas: list of rtas one for reach remote machine on which to execute the task.
    """
    # a group task to prefix all starting task of the 
    # rtas
    trec = {'basename': "deploy_webserver_runtime_prefix",
             'actions': None,
            'task_dep': ["<>"]
            }
        
    yield trec
    rtas_tasks = []
    for rtas in all_rtas:
        rtas.set_super_task_seq("deploy_webserver_runtime")
        rtas.set_task_local_step_pre(...)
        rta.set_task_ship_files_iter(...)
        remote_task_append = set.set_task_remote_step_iter()

        # add a series of remote steps each with its own qualifier
        remote_task_append(...)
        remote_task_append(...)
        ...

        rtas.set_task_fetch_files_iter(...)
        rtas.set_task_local_step_post(...)

        # store the final task of this rtas 
        rtas_tasks.append(rtas.task_label)
        # generate a series of tasks for super task sequence
        yield from rtas

        # define sub rtas: e.g., rtas that configures individual websites
        for <website> in hosted_websites:
            rtas.set_new_subtask_seq(id_args = [id(<website>)]
                                     )
            # define work for subtask sequence
            ...
            ...

            # store the final task of this rtas 
            rtas_tasks.append(rtas.task_label)
            yield from rtas

            pass
        pass
    
    # group task represents the teardown for super and all the subtasks
    trec = {'basename': "deploy_webserver_runtime",
            'actions': None,
            'task_dep': rtas_tasks, 
            }
        
    yield trec

Decorator
=========

RemoteOrchestratorPy provides  `doit_taskify` to elimate some
of the repeatitive boilerplate and make the code look more clean. It derives the label from name of the function and appends setup and teardown tasks as required:

Usage shown below

.. _demo:

Demo for doit_taskify
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
		
   from doit_rtas import (RemoteTaskActionSequence,
                       doit_taskify,
                       )

   connect_kwargs = {
       "key_filename": <path-to-ssh-public-key-file>,
    }
    
   ip_addr = <an-ip-address>
       connect_kwargs = {
        "key_filename": f"{cluster_resources_datadir}/{adming_public_key_file}",
    }
    fabric_config = Config(overrides={
        'connect_kwargs': connect_kwargs,
        'run': {
            'hide': True,
            'warn': True,
            'echo': True
        },
    })

    fabric_conn_root = Connection(host=ip_addr,
                                  user="root",
                                  config=fabric_config
                                  )

    fabric_conn_adming = Connection(host=ip_addr,
                                    user="adming",
                                    config=fabric_config
                                    )
				    
    rtas = RemoteTaskActionSequence(ipv6)
   
    all_rtas = [rtas]
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


  
		 
A typical output of execution of RTAS would look as follows:

.. code-block:: bash

   python  /home/kabira/Development/cloudworks-monallabs/RemoteOrchestratorPy/devel_tests/td_doit_rtas.py                     
   -- test_drive_rtas:45.76.4.30::local_step_pre                                                        
   -- test_drive_rtas:45.76.4.30::ship_file:super_0
   -- test_drive_rtas:45.76.4.30::ship_file:super_1
   .  test_drive_rtas:45.76.4.30::ship_file:super_2
   in RemoteFileDep: dependency is not uptodate...rerun task
   .  test_drive_rtas:45.76.4.30::remote_step
   in RemoteFileDep: dependency is uptodate
   -- test_drive_rtas:45.76.4.30::fetch_file:remote_file1
   in RemoteFileDep: dependency is uptodate
   -- test_drive_rtas:45.76.4.30::fetch_file:remote_file2
   in RemoteFileDep: dependency is uptodate
   -- test_drive_rtas:45.76.4.30::fetch_file:remote_file3
   -- test_drive_rtas:45.76.4.30::local_step_post
   .  test_drive_rtas:45.76.4.30::worker_id:0:local_step_pre
   local step called:  sub_workder_id:0
   -- test_drive_rtas:45.76.4.30::worker_id:0:ship_file:sub_workder_id:0_0
   -- test_drive_rtas:45.76.4.30::worker_id:0:ship_file:sub_workder_id:0_1
   -- test_drive_rtas:45.76.4.30::worker_id:0:ship_file:sub_workder_id:0_2
   in RemoteFileDep: dependency is uptodate
   -- test_drive_rtas:45.76.4.30::worker_id:0:remote_step
   in RemoteFileDep: dependency is uptodate
   .  test_drive_rtas:45.76.4.30::worker_id:0:fetch_file:remote_file01
   in RemoteFileDep: dependency is uptodate
   .  test_drive_rtas:45.76.4.30::worker_id:0:fetch_file:remote_file02
   in RemoteFileDep: dependency is uptodate
   .  test_drive_rtas:45.76.4.30::worker_id:0:fetch_file:remote_file03
   .  test_drive_rtas:45.76.4.30::worker_id:0:local_step_post
		 
