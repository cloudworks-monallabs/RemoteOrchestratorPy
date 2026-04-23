from doit.task import Task
from doit.loader import load_tasks
from doit.doit_cmd import DoitMain

doit_main = DoitMain()
doit_main.setup({})
tasks, config = load_tasks(doit_main, {})

leave it 
