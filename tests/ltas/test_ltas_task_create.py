import pytest

from RemoteOrchestratorPy import LocalTaskActionSequence, ltas_taskify

ltas =  LocalTaskActionSequence()
@ltas_taskify(ltas)
def local_task_sequence_generator(ltas):
    """
    """
    add_step = ltas.get_step_adder()
    # do local task 1
    def local_task_1(arg1, arg2, **kwargs):
        pass
    add_step([local_task_1,
                       ["arg1",
                       "arg2",
                        ],
                       {"kwarg1":"kwarg1",
                        "kwarg2":"kwarg2"
                       }
                       ],
                      "local_work_step_1"
                      # other task metadata  
                      )

    def local_task_2(arg1, arg2, **kwargs):
        pass
    add_step([local_task_2,
                       ["arg1",
                       "arg2",
                        ],
                       {"kwarg1":"kwarg1",
                       
                       "kwarg2":"kwarg2"
                       }
                       ],
                      "local_work_step_2"
                      # other task metadata  
                      )    

    
    yield from ltas
    

def test_LTAS_api_calls_default_usage():
    # 1. Execute the generator to collect task dictionaries
    # Note: ltas_taskify makes the function return a generator of tasks
    tasks = list(local_task_sequence_generator())

    # 2. Extract task names for easy assertion
    # pydoit identifies tasks as 'basename:name'
    task_names = [f"{t['basename']}:{t['name']}" for t in tasks]

    # Expected Names based on your ltas_taskify logic:
    # - The root enter task
    # - The individual steps (prefixed with 'local_step:')
    # - The final 'local_step' aggregator
    # - The leaf final task
    
    base = "local_task_sequence_generator"
    expected_names = [
        f"{base}:_root_enter_",
        f"{base}:local_step:local_work_step_1",
        f"{base}:local_step:local_work_step_2",
        f"{base}:local_step",
        f"{base}:_leaf_final_"
    ]

    assert task_names == expected_names

    # 3. Verify Dependencies (The Chain)
    # Task 1 should depend on _root_enter_
    task_1 = tasks[1]
    assert f"{base}:_root_enter_" in task_1['task_dep']

    # Task 2 should depend on Task 1 (Sequential Chaining)
    task_2 = tasks[2]
    assert f"{base}:local_step:local_work_step_1" in task_2['task_dep']

    # The aggregator 'local_step' should depend on the last step in the iter
    aggregator = tasks[3]
    assert f"{base}:local_step:local_work_step_2" in aggregator['task_dep']

    # The _leaf_final_ should depend on the aggregator
    leaf = tasks[4]
    assert f"{base}:local_step" in leaf['task_dep']

    print("\nTask Chain Verified: Root -> Step 1 -> Step 2 -> Aggregator -> Leaf")
    


    

def mock_uptodate_check():
    return True

def mock_teardown_func():
    print("Cleaning up...")

ltas =  LocalTaskActionSequence()    
@ltas_taskify(ltas,
    task_dep=["external_setup"], 
    uptodate=[False], 
    targets=["global_log.txt"]
)
def local_task_sequence_generator_with_task_metadata(ltas):
    """
    Test generator to verify metadata propagation to pydoit dicts.
    """
    add_step = ltas.get_step_adder()
    
    # Task with specific modifiers
    add_step(
        "echo 'Action 1'", 
        "step_with_metadata",
        file_dep=["input.txt"],
        targets=["output.bin"],
        teardown=[(mock_teardown_func,)],
        uptodate=[mock_uptodate_check]
    )
    
    yield from ltas

def test_LTAS_metadata_propagation():
    # 1. Execute the generator
    tasks = list(local_task_sequence_generator_with_task_metadata())
    base = "local_task_sequence_generator_with_task_metadata"
    
    # 2. Assert Metadata on the Root Task (_root_enter_)
    # This comes from the @ltas_taskify decorator kwargs
    root_task = next(t for t in tasks if t['name'] == "_root_enter_")
    assert "external_setup" in root_task['task_dep']
    assert root_task['uptodate'] == [False]
    assert "global_log.txt" in root_task['targets']

    # 3. Assert Metadata on the Individual Step Task
    # This comes from the get_step_adder (append) kwargs
    step_task = next(t for t in tasks if "local_step:step_with_metadata" in t['name'])
    
    # Check pydoit modifiers
    assert "input.txt" in step_task['file_dep']
    assert "output.bin" in step_task['targets']
    assert step_task['uptodate'] == [mock_uptodate_check]
    assert step_task['teardown'] == [(mock_teardown_func,)]
    
    # Verify the automatic chaining logic still exists alongside metadata
    # The step task should still depend on the root task
    assert f"{base}:_root_enter_" in step_task['task_dep']

    # 4. Verify specific LTAS internal dependency consumption
    # The code says: if self.task_dep: trec['task_dep'].extend(self.task_dep); self.task_dep = []
    # This ensures that 'external_setup' didn't accidentally leak into the step_task 
    # if it was already consumed by the root.
    assert "external_setup" not in step_task['task_dep']

    print("\nMetadata Validation Successful: Targets, File_Deps, and Teardowns correctly mapped.")
    

