# RemoteOrchestratePy

RemoteOrchestratePy is a Python-based solution for orchestrating IT workloads across a cluster of remote machines. It seamlessly integrates PyDoit with Fabric and Dash, offering straightforward workflow to ease the process of writing automation script on  remote machine IT operations.

## Why PyDoit:

There are compelling reasons for choosing PyDoit:

1. **Expressive Task Management:** PyDoit empowers you to define task dependencies and scheduling constraints using Python, aligning seamlessly with the language's expressiveness.

2. **Simplicity and Pythonic Approach:** PyDoit is user-friendly and makes the best use of Python's inherent constructs. For a comprehensive look at PyDoit's merits and basic usage, check out [Doit: the goodest python task-runner you never heard of](https://www.bitecode.dev/p/doit-the-goodest-python-task-runner).

In general, PyDoit offers the following features and advantages:

- **Task Runner and Build System:** doit is described as both a task runner and a build system. It can be used for automating various tasks in a project, including building, testing, and deploying.

- **Dependency Management:** doit handles task dependencies, ensuring that tasks are executed in the correct order based on their dependencies.

- **Parallel Execution:** Tasks can be executed in parallel, making it suitable for projects with multiple tasks that can run concurrently.

- **Error Handling:** doit provides error handling for tasks and stops execution in case of failure, preventing further tasks from running.

- **Customization:** You can customize doit to fit your project's specific needs by defining your own tasks and actions.





# Usage
Provides 4 utility functions: `gen_task_ship_files`, `gen_task_remote_exec`, `gen_task_local_exec`, `gen_task_fetch_files` (to-be-implemented). 

Also, provide a higher-order template called remote-task.

## Higher-Order Template: "remote-task"

The "remote-task" template is a higher-order template and consists of sequence of:

1. `local_step_pre`: Local tasks to be executed before shipping files or executing remote tasks.
2. `ship_files`: Task to ship files to the remote machine.
3. `remote-steps`: Remote tasks to be executed on the remote machine.
4. `fetch-files` (to-be-implemented): Task to fetch files back from the remote machine.
5. `local_step_post`: Perform post-remote execution tasks.

It is designed to succiently express a useful unit of remote work which starts by doing some prep work locally, 
shipping scripts and data remotely, doing remote execution, downloading the resulting files and finally some 
local post-op local work. 

## APIs

### `gen_task_ship_files(files_to_ship, ipv6, label, id_args=[], remote_dir="/tmp", is_dep_task=True, deps=[])`

Create a doit task to ship files to a remote machine.

#### Parameters:

- `files_to_ship` (list): A list of file paths to be shipped to the remote machine.

- `ipv6` (str): The IPv6 address of the remote machine.

- `label` (str): A label for the task.

- `id_args` (list, optional): Additional arguments to include in the task's name. Default is an empty list.

- `remote_dir` (str, optional): The destination directory on the remote machine where the files will be copied. Default is "/tmp".

- `is_dep_task` (bool, optional): Indicates whether this task is a dependency task. If set to `True`, the task's `basename` will be set to the provided `label`. Default is `True`.

- `deps` (list, optional): A list of dependencies for this task, specifying other tasks that must be executed before this one.

#### Returns:

- `rec` (dict): A dictionary representing the task configuration that can be used with `pydoit`. The task created by this function will use ClusterShell to ship files to the specified remote machine.

### Description:

This function generates a `pydoit` task configuration for shipping files to a remote machine using ClusterShell. It allows you to define the files to be shipped, the destination directory on the remote machine, and other task-related parameters.

The resulting task can be added to your `pydoit` task list and executed as part of your project's automation workflow.

#### Example:

```python
files_to_ship = ['file1.txt', 'file2.txt']
ipv6 = '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
label = 'ship_files_task'

1. Generate the task configuration
task_config = gen_task_ship_files(files_to_ship, ipv6, label)

2. Add the task to your pydoit task list
tasks = [task_config]

3. Run the tasks using pydoit
doit.run(tasks)
```

### `get_ref_name(trec)`

Return the full task identifier for use in the `task_dep` argument list based on a given task record.

#### Parameters:

- `trec` (dict): A dictionary representing a task record.

#### Returns:

- `identifier` (str): The full task identifier, including the task's `basename` and `name`.

#### Description:

This function takes a task record as input and returns the full identifier that can be used in the `task_dep` argument list of other tasks. The full identifier includes both the task's `basename` and `name`, allowing it to be used as a dependency reference in other tasks.

The `get_ref_name` function is particularly useful when you need to specify dependencies between tasks in a `pydoit` task configuration. By providing a task record, you can easily generate the correct task reference needed to establish task dependencies.

#### Example:

```python
# Define a task record
task_record = {
    'basename': 'my_task',
    'name': 'task_instance',
    # Other task configuration properties...
}
```
1. Get the full task identifier
```python
task_dependency = get_ref_name(task_record)
```
2. Use the task_dependency in another task's task_dep list
```python
other_task = {
    'name': 'other_task',
    'actions': ['do_something'],
    'task_dep': [task_dependency],  # Use the generated task reference
}
```

### `gen_task_remote_exec(cmdstr, ipv6, id_args=[], args=[], label=None, is_dep_task=False, deps=[])`

Create a `pydoit` task to remotely execute a command on a specified IPv6 address.

#### Parameters:

- `cmdstr` (str or callable): The command string to execute on the remote machine or a callable function that generates the command string.
- `ipv6` (str): The IPv6 address of the remote machine.
- `id_args` (list, optional): Additional identifier arguments to include in the task name.
- `args` (list, optional): Additional arguments to pass to the command (if `cmdstr` is a callable).
- `label` (str, optional): A label for the task, which is used as the task's `basename` and `exec_cmd_label`. If not provided and `cmdstr` is callable, the function's name will be used as the label.
- `is_dep_task` (bool, optional): Whether this task is a dependency task.
- `deps` (list, optional): A list of task records that this task depends on.

#### Returns:

- `task_config` (dict): The task configuration dictionary for use with `pydoit`.

#### Description:

This function generates a `pydoit` task configuration for remotely executing a command on a specified IPv6 address using the ClusterShell library. It provides flexibility in defining the command either as a static string (`cmdstr`) or as a callable function that dynamically generates the command based on input arguments (`cmdstr` should be callable in this case).

- If `label` is not provided, and `cmdstr` is a callable, the function's name will be used as the `basename` and `exec_cmd_label` for the task.
- Task dependencies can be specified using the `deps` parameter, and their references will be added to the `task_dep` list.

#### Example:


1. Define a remote execution task using a command string
```python
remote_exec_task = gen_task_remote_exec("echo 'Hello, World!'", "2001:db8::1")
```

2. Define a remote execution task using a callable function
```python
def generate_command(ipv6, *args):
    return f"ping {ipv6} {' '.join(args)}"

remote_exec_task_callable = gen_task_remote_exec(
    generate_command, "2001:db8::2", args=["-c 5"], label="ping_task"
)
```

3. Define other tasks and dependencies
```python
dependencies = [remote_exec_task, remote_exec_task_callable]

other_task = {
    'name': 'other_task',
    'actions': ['do_something'],
    'task_dep': [get_ref_name(dep) for dep in dependencies],
}
```


### `gen_task_local_exec(func, id_args, args=[], is_dep_task=True, deps=[], label=None)`

Create a `pydoit` task to execute a Python function locally.

#### Parameters:

- `func` (callable): The Python function to execute as the task's action.
- `id_args` (list or tuple): Arguments to pass to the `func` when it is executed.
- `args` (list, optional): Additional arguments to pass to the `func`.
- `is_dep_task` (bool, optional): Whether this task is a dependency task.
- `deps` (list, optional): A list of task records that this task depends on.
- `label` (str, optional): A label for the task, which is used as the task's `basename`.

#### Returns:

- `task_config` (dict): The task configuration dictionary for use with `pydoit`.

#### Description:

This function generates a `pydoit` task configuration for executing a Python function locally as part of a `pydoit` workflow. It allows you to specify the function (`func`) to execute, along with any arguments (`id_args` and `args`) to pass to that function during execution.

- The `id_args` parameter should be a list or tuple containing the arguments to be passed to `func`.
- Additional arguments can be provided using the `args` parameter.
- Task dependencies can be specified using the `deps` parameter, and their references will be added to the `task_dep` list.
- If a `label` is provided, it will be used as the `basename` for the task; otherwise, the `basename` will be derived from the `func`'s name.

#### Example:


1. Define a Python function to be executed
```python
def my_function(arg1, arg2):
    result = arg1 + arg2
    print(f"Result: {result}")
```
2. Create a pydoit task for executing the function
```python
task_config = gen_task_local_exec(my_function, id_args=[10, 20], label="add_task")
```

3. Define other tasks and dependencies
```python
dependencies = [task_config]

other_task = {
    'name': 'other_task',
    'actions': ['do_something'],
    'task_dep': [get_ref_name(dep) for dep in dependencies],
}
```







### `doit_task_generator_for_RTAS(rt_tag, ipv6, id_args, remote_work_dir="/tmp")`

Create a generator for generating a sequence of tasks that represent a Remote Task Action Sequence (RTAS).

#### Parameters:

- `rt_tag` (str): An identifier for the remote task sequence.
- `ipv6` (str): The IPv6 address of the remote machine.
- `id_args` (list or tuple): Arguments to be passed to various tasks within the sequence.
- `remote_work_dir` (str, optional): The remote working directory where files will be shipped and remote tasks will be executed.

#### Returns:

- `wrapper` (function): A generator function that generates tasks for the RTAS sequence.

#### Description:

The `doit_task_generator_for_RTAS` function creates a generator function that is used to generate a sequence of tasks representing a Remote Task Action Sequence (RTAS). An RTAS consists of five batches of tasks:

1. `local_work_pre`: Local tasks to be executed before shipping files.
2. `ship_files`: Task to ship files to the remote machine.
3. `remote-work`: Remote tasks to be executed on the remote machine.
4. `ship-files`: Task to ship files back from the remote machine (not yet implemented).
5. `local_work_post`: Local tasks to be executed after receiving files from the remote machine.

Each batch of tasks is generated using corresponding task generator functions such as `gen_task_local_exec`, `gen_task_ship_files`, and `gen_task_remote_exec`.

The generator function `wrapper` takes arguments for each batch of tasks, and it generates and yields the task configurations for each batch. Tasks within each batch may have dependencies on tasks from previous batches.

#### Example:


1. Define an RTAS generator for a specific remote task
```python
rtas_generator = doit_task_generator_for_RTAS("my_remote_task", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", ["arg1", "arg2"])
```
# Generate tasks for the RTAS sequence
```python

for task_config in rtas_generator(
    local_steps_pre=local_work_pre_func,
    to_ship_files=["file1.txt", "file2.txt"],
    remote_steps=remote_work_func,
    from_ship_files=None,
    local_steps_post=local_work_post_func
):
    tasks.append(task_config)
```

3. Create a pydoit task to execute the RTAS sequence
```python
doit_task = {
    'name': 'execute_RTAS',
    'actions': None,
    'task_dep': [get_ref_name(rtas_generator.final_task)],
    'uptodate': [run_once]
}
```
