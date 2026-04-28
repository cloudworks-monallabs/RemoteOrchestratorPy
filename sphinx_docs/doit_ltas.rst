ltas_taskify
============

.. py:decorator:: ltas_taskify(**kwargs)

   A decorator that transforms a Python generator function into a suite of ``pydoit`` tasks managed as a sequential execution chain. 
   
   It initializes a :class:`LocalTaskActionSequence` context and handles the automatic generation of "root" and "leaf" tasks to ensure a strict execution order, even when sub-actions or multiple command sequences are involved.

   :param task_dep: A list of task names that must complete successfully before this task sequence begins. These dependencies are anchored to the internal ``_root_enter_`` task.
   :param \**kwargs: Additional keyword arguments passed to the underlying ``pydoit`` task dictionary (e.g., ``targets``, ``file_dep``, ``uptodate``).

   **Function Signature**
   
   The decorated function must accept at least one argument, which will receive the initialized :class:`LocalTaskActionSequence` (ltas) instance:

   .. code-block:: python

      @ltas_taskify(task_dep=["setup_environment"])
      def my_pipeline(ltas):
          append = ltas.get_step_adder()
          append("echo 'Step 1'", label="first")
          append("echo 'Step 2'", label="second")
          yield from ltas

   **Internal Behavior**

   1. **Root Task Creation**: Automatically yields a task named ``<func_name>:_root_enter_`` which acts as the entry point for the dependency graph.
   2. **Sequence Chain**: Uses the ``finalize()`` method of the LTAS instance to automatically link the ``task_dep`` of each appended action to its predecessor, creating a linear chain.
   3. **Execution Guard**: Wraps all actions in an ``action_wrapper`` that monitors for failures. If an action raises an exception, ``task_failed_abort_execution`` is set to ``True``, and subsequent actions in the sequence are skipped.
   4. **Leaf Task Creation**: Automatically yields a final task ``<func_name>:_leaf_final_`` that depends on the completion of the entire local step sequence.

   **Attributes added to the decorated function**

   * ``__root_enter_task_label__``: The string identifier for the start task.
   * ``__leaf_final_task_label__``: The string identifier for the completion task.
   * ``create_doit_tasks``: A reference to the generator itself, compatible with ``pydoit`` task discovery.
