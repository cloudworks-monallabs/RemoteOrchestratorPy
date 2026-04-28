import sys
def task_say_hello():
    def do_action():
        print("hellow")

    def teardown():
        print("in teardown")
        
    return { 'actions': [do_action],
             'teardown': [teardown],
             'file_dep': ["a_file", "b_file"]

        }

from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain
from doit.cmd_run import Run

loader = ModuleTaskLoader(sys.modules[__name__])
# 2. Create a command instance (Run is the most common for task loading)
# We don't execute it; we just use it to provide the interface load_tasks needs.
cmd = Run(task_loader=loader)
tasks = loader.load_tasks(cmd, [])

for task in tasks:
    # Basic metadata
    name = task.name
    targets = ", ".join([str(t) for t in task.targets]) if task.targets else "None"
    file_deps = ", ".join([str(d) for d in task.file_dep]) if task.file_dep else "None"
    task_deps = ", ".join(task.task_dep) if task.task_dep else "None"
    
    # Uptodate is often a list of callables or booleans
    # We convert to string representation for easy reading
    uptodate = str(task.uptodate) if task.uptodate else "Default (Timestamp)"

    print(f"{name:<40} | {targets:<20} | {file_deps}")
    
    # Optional: print more detailed attributes
    if task.task_dep:
        print(f"  └─ Task Dependencies: {task_deps}")
    if task.uptodate:
        print(f"  └─ Up-to-date check: {uptodate}")
    print("-" * 80)
    
