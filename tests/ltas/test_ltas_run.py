import pytest

from RemoteOrchestratorPy import LocalTaskActionSequence, ltas_taskify
from RemoteOrchestratorPy import RTASExecutionError

# Try to run it
import os
import sys
from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain
DOIT_WORKDIR = os.environ['DOIT_WORKDIR']
import pytest


# 1. This is the state we will monitor
EXECUTION_LOG = []
ltas =  LocalTaskActionSequence()

@ltas_taskify(ltas)
def local_task_sequence_generator(ltas):
    """
    """
    add_step = ltas.get_step_adder()
    # do local task 1
    def local_task_1(arg1, **kwargs):
        print("Exec local_task_1")
        EXECUTION_LOG.append(f"task1_{arg1}")
        pass

    def local_task_2(arg1, **kwargs):
        EXECUTION_LOG.append(f"task2_{arg1}")
        pass
    
    # Register steps
    
    add_step([local_task_1, ["val1"], {}], "step_1")
    add_step([local_task_2, ["val2"], {}], "step_2")
    
    yield from ltas

    
def test_run():
    os.chdir(DOIT_WORKDIR)
    try:
        EXECUTION_LOG.clear()
        doit_main = DoitMain(ModuleTaskLoader(sys.modules[__name__]))
        doit_main.run([]
                      )
        expected_log = ["task1_val1", "task2_val2"]
        # assert EXECUTION_LOG == expected_log, (
        #     f"Execution state mismatch. Expected {expected_log}, got {EXECUTION_LOG}"
        # )
        
    except Exception as e:
        print (f"Exception happend during task creation phase: {e}")
        raise e
    finally:

        print ("finished deployment workflow execution")
        
    if ltas.task_failed_abort_execution:
        raise RTASExecutionError(str(ltas.task_failed_exception), ltas)
