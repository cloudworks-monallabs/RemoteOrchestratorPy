..
   RemoteOrchestratePy
   ====================

   RemoteOrchestratePy is a Python-based solution for orchestrating IT workloads across a cluster of remote machines. It  integrates PyDoit with Fabric and Dash, offering straightforward workflow to ease the process of writing automation scripts for remote machine IT operations.

Key features:
-------------

#. **Better Coding Ergonomics**:
  
  - Avoids the need to learn a new language for builds/automation.
  - Leverages Python syntax and constructs.
  - Minimal boilerplate.
  - Express task dependencies cleanly and in straightforward manner
  - Easy to read, maintain, modify, and extend.

#. **General Purpose**:
  
  - Not limited to IT workloads, Capable of handling any tasks that can expressed using Python or command line.
  - Suitable for both simple and complex workflows involving multiple remote machines.

#. **Fine Grained**:
  
  - Allows precise control over each step in the workflow without unnecessary verbosity

#. **Extends to Remote Machines**:
  
  - Is able to  define tasks that depend on the completion of actions executed on remote machines.
  - Ensures tasks are executed in the correct order based on remote and local dependencies.

#. **Super and Subtask sequence**

  - Hierarchical task management with super and subtask sequences.
  - Super task sequences manage broad, overarching services or functions.
  - Subtask sequences manage specific details under a super task sequence.

#. **Supports Dask to remotely run python script**
   
   - Requires no python file logistic handling
   - Use of Python codes, instead of bash command strings, makes it trivally easy to run complex workflows on remote directly from local
   - Supports all PyDoit task dependencies even though task is running remotely.
     
    
  
.. contents:: Table of Contents
    :depth: 3

Workflow for operating on remote machine
----------------------------------------
In RemoteOrchestratePy, a workflow that involves a remote machine is called RemoteTaskActionSequence or RTAS/rtas for short. A RTAS consists of five phases in following sequences:

- local step pre
- ship files
- remote steps
- fetch files
- local step post

An rtas should have at work (action) defined for least one phase. 

1. **Local Step Pre**:
    - This phase involves initial preparations and operations performed locally before any interaction with the remote machine. Typical tasks might include generating necessary files, setting up configurations, or performing initial computations.

2. **Ship Files**:
    - During this phase, files either generated or needed from the local environment or other workflow files  are transferred to the remote machine. This ensures that the remote environment has all the necessary data and resources to perform its tasks.

3. **Remote Steps**:
    - This phase encompasses all the operations executed on the remote machine. Operations can be expressed as string which is executed on shell via `fabric_conn.run` api. Alternatively, you can define a function that uses dask to run python script remotely.  The results of these operations are typically stored on the remote machine until they are fetched back.

4. **Fetch Files**:
    - In this phase, the outputs or results produced by the remote steps are retrieved from the remote machine back to the local environment. This ensures that the local environment has access to the processed data for further use or analysis.

5. **Local Step Post**:
    - The final phase involves any concluding tasks that need to be performed locally after retrieving files from the remote machine. This might include further processing of data, generating reports, or cleaning up temporary files used during the workflow.

Each phase is designed to encapsulate a specific part of the workflow, providing a structured approach to managing tasks across local and remote environments. Note that in any given RTAS, one or more of these phases can be optional or missing, depending on the specific requirements of the workflow.

.. note::
   
   If there are multiple RTAS or if within a single rtas there are multiple sub-rtas then we a setup (or prefix) and teardown (final) task is required as well to encapsulate the generated task sequence. 
	    
Background and Overview:
------------------------

Python pydoit allows one to  express tasks (or actions) and their dependencies in an easy-to-understand Pythonic way. Other then this, its capability is like any other build tool:  it infers which tasks need to be run based on their dependencies and executes them efficiently.

Pydoit provides several standard  as well as custom constructs to define task dependencies such as `file_dep`, `task_dep`, `targets`, `run_once`, `uptodate`, `calc_dep`, `create_after` etc.

These constructs offer a flexible and powerful way to manage complex workflows. For example:

- `file_dep` specifies files that a task depends on, ensuring tasks are executed only when their dependencies have changed.
- `task_dep` allows for specifying dependencies between tasks.
- `targets` define the output files produced by a task, which helps pydoit determine if the task needs to be rerun.
- The `run_once` construct ensures that a task is executed only once, regardless of how many times it is referenced.
- The `uptodate` construct can be used to add custom conditions for determining whether a task is up-to-date.
- `calc_dep` dynamically calculates additional dependencies for a task.
- The `create_after` construct ensures that a task is created only after another specified task has been completed, which is useful for managing dynamic task generation.


Sample Example
~~~~~~~~~~~~~~

.. code-block:: python

from doit.tools import run_once, create_folder
import os

def task_initial_setup():
    return {
        'actions': [(create_folder, ['output'])],
        'targets': ['output'],
        'uptodate': [run_once],
    }

def task_preprocess():
    return {
        'actions': ['echo "Preprocessing data" > output/preprocess.txt'],
        'file_dep': ['input.txt'],
        'targets': ['output/preprocess.txt'],
    }

def task_process():
    return {
        'actions': ['echo "Processing data" > output/process.txt'],
        'file_dep': ['output/preprocess.txt'],
        'targets': ['output/process.txt'],
        'task_dep': ['preprocess'],
    }

def task_finalize():
    return {
        'actions': ['echo "Finalizing process" > output/finalize.txt'],
        'file_dep': ['output/process.txt'],
        'targets': ['output/finalize.txt'],
        'calc_dep': ['process'],
    }

def task_summary():
    return {
        'actions': ['cat output/finalize.txt output/process.txt output/preprocess.txt > output/summary.txt'],
        'file_dep': ['output/finalize.txt', 'output/process.txt', 'output/preprocess.txt'],
        'targets': ['output/summary.txt'],
        'create_after': ['finalize'],
    }

def task_cleanup():
    return {
        'actions': [(os.remove, ['output/summary.txt']), (os.remove, ['output/finalize.txt']), (os.remove, ['output/process.txt']), (os.remove, ['output/preprocess.txt'])],
        'task_dep': ['summary'],
        'run_once': True,
    }

This example demonstrates:

#. *task_initial_setup*: Uses run_once to create the output directory only once.
   
#. *task_preprocess*: Uses file_dep to depend on input.txt and produces output/preprocess.txt.
   
#. *task_process*: Uses task_dep to depend on task_preprocess and produces output/process.txt.
   
#. *task_finalize*: Uses calc_dep to dynamically depend on task_process and produces output/finalize.txt.
   
#. *task_summary*: Uses create_after to ensure it is created after task_finalize and combines files into output/summary.txt.
   
#. *task_cleanup*: Uses task_dep to depend on task_summary and run_once to clean up only once.


   
RemoteOrchestratePy builds on pydoit to enable build/make features for orchestrating IT commands over a cluster of remote machines. By integrating pydoit with Fabric and Dash, RemoteOrchestratePy simplifies the process of writing and managing automation scripts for remote machine operations. It extends pydoit's capabilities to handle remote execution seamlessly, allowing users to define tasks that run across multiple machines with ease. This integration makes it possible to automate complex IT operations involving multiple remote hosts, ensuring efficient and reliable orchestration of tasks.



Popular Build Tools and Key Differences with PyDoit
---------------------------------------------------

Several popular build tools exist across different ecosystems, each with its own strengths and use cases. Here's a comparison of some widely used build tools and how they differ from PyDoit. 
Note that we have highlighted only the tools seemed like syntax is easy to follow. Other popular build tools like Maven, CMake, Gradle are know to have dense, verbose syntax that is not recommended for general purpose use cases.


1. **Make**:
   
    - **Use Case**: Predominantly used in C/C++ development.
    - **Strengths**: Simple syntax, widely supported, excellent for small to medium-sized projects.
    - **Key Differences**: Make uses a declarative approach with Makefiles, whereas PyDoit uses a more Pythonic and programmatic approach to define tasks.
    - **Example**:

      .. code-block:: make

        output.txt: input.txt
            cat input.txt > output.txt

      **Command to run:**

      .. code-block:: bash

	 make
	 


2. **Ninja**:
   
    - **Use Case**: High-performance builds, often used in large projects.
    - **Strengths**: Extremely fast, designed for incremental builds.
    - **Key Differences**: Ninja focuses on speed and is typically used as a backend for build systems like CMake. PyDoit, on the other hand, is a task management tool that integrates directly with Python scripts.

 - **Example**:
   
.. code-block:: ninja

        rule copy
            command = cp $in $out

        build output.txt: copy input.txt

      **Command to run:**

      .. code-block:: bash

        ninja
   

3. **Bazel**:
    - **Use Case**: Large-scale projects, high-performance builds.
    - **Strengths**: Scalable, supports multiple languages, built-in sandboxing.
    - **Key Differences**: Bazel uses its own BUILD language and focuses on performance and reproducibility. PyDoit offers more straightforward task definitions using Python.

- **Example**:

      .. code-block:: python

        genrule(
            name = "copy_file",
            srcs = ["input.txt"],
            outs = ["output.txt"],
            cmd = "cp $(SRCS) $(OUTS)",
        )

      **Command to run:**

      .. code-block:: bash

        bazel build //:copy_file


      

		

Usage/API
---------

All functionalities of RemoteOrchestratorPy is accessed via `RemoteTaskActionSequence` and decorator `doit_taskify`.

`doit_taskify`  is a helper decorator to eliminate
some of boilerplate code. First, we show API usage
without the decorator with boilerplate code and
next we show the use of doit_taskify that makes
the code cleaner and less verbose.

Installation
^^^^^^^^^^^^

To install RemoteOrchestratePy clone the repo and include the code path in the PYTHONPATH enviornment variable.


.. code-block:: bash

   git clone `git@github.com:cloudworks-monallabs/RemoteOrchestratorPy.git`_

   
Super and sub task sequence
^^^^^^^^^^^^^^^^^^^^^^^^^^^
RTAS supports notion of super and sub task sequence.

A super task sequence is a higher-level task that involves setting up a broad, overarching service or function. For example, setting up a web server runtime environment would be a super task sequence. This task sequence includes installing the necessary software, setting up runtime configurations, and ensuring that the service is up and running.

A subtask sequence, on the other hand, is a more specific and detailed sequence of tasks that falls under the umbrella of the super task sequence. For example, configuring individual websites being served by the web server would be subtask sequences. Each subtask sequence might include setting up the site configuration files, setting permissions, and deploying content specific to each website.

This hierarchical structure allows for modular and organized task management, making complex IT operations more manageable.

See api `set_super_task_seq` and `set_new_subtask_seq` on setting up super and subtask sequence.


APIs for RemoteTaskActionSequence
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Constructor
```````````
The class RemoteTaskActionSequence is initialized with
constructor that takes ip address and list of tuple consisting of  ssh user and fabric conn.


.. class:: RemoteTaskActionSequence

   :param ipv6: The IP address of the remote machine.
   :type ipv6: str
   :param args: Variable number of positional arguments. Each args is a tuple of SSH username and corresponding Fabric connection.
   :type args: tuple


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
```````````````

.. function:: set_active_user(user="adming")

    Sets the active SSH user for the RemoteTaskActionSequence.

    :param user: The SSH username to set as active. Defaults to "adming".
    :type user: str
    :raises AssertionError: If the provided user is not found in the SSH users and Fabric connections.


set_super_task_seq
``````````````````
 Sets up a new super task sequence with the given label `basename`.

 .. method::set_super_task_seq(self, basename, id_args=[])
 
   setup a new task sequence with label `basename` qualified with `id_args`.
   

set_new_subtask_seq
```````````````````
Sets up a new subtask sequence on the target node with additional qualifiers.

.. method:: set_new_subtask_seq(self, id_args= [])

    :param id_args: A list of identifiers for the subtask sequence.
    :type id_args: list
		   

	      
set_task_local_step_pre
```````````````````````
    Sets the local step pre-function for a task in the RemoteTaskActionSequence.
    
.. method:: set_task_local_step_pre(step_func, *args, **kwargs)



    :param step_func: The function to be executed as the local step pre-function.
    :type step_func: callable
    :param args: Positional arguments to be passed to the `step_func`.
    :type args: tuple
    :param kwargs: Keyword arguments to be passed to the `step_func`. Can include task attributes such as `targets`, `file_dep`, `uptodate`, `task_dep`
    :type kwargs: dict


set_task_ship_files_iter
````````````````````````
Generates tasks per given file to ship to remote destination. The local file is treated as file dependency
and remote is treated as target for the task

    
.. method:: set_task_ship_files_iter(files_to_ship, dest_dir, **kwargs)

    :param files_to_ship: A list of file paths to be shipped.
    :type files_to_ship: list of str
    :param dest_dir: The destination directory on the remote machine where the files will be shipped.
    :type dest_dir: str
    :param kwargs: Additional keyword arguments to customize the behavior of the file shipping process.
    :type kwargs: dict


		  
set_task_remote_step_iter
`````````````````````````

 Returns a function `remote_task_append` used to append a new remote task to the sequence.

 .. method:: set_task_remote_step_iter
    :return: A function `remote_task_append` to append a new remote task to the sequence.
    :rtype: function


remote_task_append
%%%%%%%%%%%%%%%%%%

The `remote_task_append` function is used to add a new task to the sequence of remote tasks. 
It takes a command (`cmd`), a label (`label`), and additional arguments and keyword arguments.

- If `cmd` is a string, it will be executed via Fabric's `run` function on the remote machine.

- If `cmd` is a function, it is assumed to use Dask to run Python code remotely.


.. method:: remote_task_append(cmd, label, *args, **kwargs)

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
Assume in file `remote_actions.py` has code as follows:
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
`````````````````````````

Creates tasks, one per give file to fetch from the remote machine to a local directory. 

	
.. method:: set_task_fetch_files_iter(files_to_fetch, local_dir="/tmp")
   :param files_to_fetch: A list of file paths to be fetched from the remote machine.
   :type files_to_fetch: list of str
   :param local_dir: The local directory where the files will be fetched to. Defaults to "/tmp".
   :type local_dir: str

		    
set_task_local_step_post
````````````````````````
Sets the given function to be executed as a task as part of
local step post phase.

    
.. method:: set_task_local_step_post(self, step_func, *args, **kwargs):

    :param step_func: The function to be executed as the local step post-function.
    :type step_func: callable
    :param args: Additional positional arguments to be passed to the `step_func`.
    :type args: tuple
    :param kwargs: task dependency arguments.
    :type kwargs: dict
    """    

A typical output of execution of RTAS would look as follows:

.. code-block::

   .. code-blocks:: bash

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

   
    
Demo: A complete workflow
-------------------------


Initialize RTAS
```````````````

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
``````````````````````````````
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
----------
RemoteOrchestratorPy provides  `doit_taskify` to elimate some
of the repeatitive boilerplate and make the code look more clean. It derives the label from name of the function and appends setup and teardown tasks as required:

Usage shown below

Demo for doit_taskify
`````````````````````

.. code-block:: python
		
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

