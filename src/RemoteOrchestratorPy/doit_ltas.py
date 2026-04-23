# local task action sequence
#. mostly local task action
#. maybe with subactions

import logging
import subprocess
import functools
from .doit_rtas_helpers import (
                                get_ref_name,
                               )
logger = logging.getLogger(__name__)


def action_wrapper(ltas, action_func):

    def wrapper(*args, **kwargs):
        if ltas.task_failed_abort_execution:
            logger.info(f"LTAS-skip-task: task_failed_abort_execution is True")
            return False
        try:
            logger.info(f"running action {action_func}")
            return action_func(*args, **kwargs)
            
        except Exception as e:
            ltas.task_failed_abort_execution = True
            ltas.task_failed_exception = e
            logger.info(f"LTAS-abort-task: {action_func}:  raised exception {e}")
            return False
        return False

    return wrapper


def local_exec_cmd(ltas,  task_label, *args):

    status = "Success"

    for cmdstr in args:
        # exception will be captured by action wrapper
        result = subprocess.run(cmdstr, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True  # Ensures output is returned as a string
        )
        logger.info(f"Command succeeded: {cmd}")
        if result.stdout:
            logger.info(f"Output: {result.stdout.strip()}")
    return status

def local_exec_func(ltas, task_label, cmdl):
    #result = "success"

    try:
        logger.debug(f"starting local action: {cmdl}")
        the_func = cmdl[0]
        result = the_func(*cmdl[1],
                 **cmdl[2])
        ltas.local_task_results[task_label] = ("Success", result)

        return "Success"
    
    except Exception as e:
        logger.debug(f"local_exec_func failed {e}")
        ltas.local_task_results[task_label] = ("Failed", str(e))

        raise e

def doit_taskify(ltas,
                 **kwargs
                 ):
    """
    all_rtas: list of RemoteTaskActionSequence. Each rtas represents a compte node on which to invoke action sequence
    """
    
    def wrapper(func):
        """
        convert a function to a rtas task sequence generator function.
        prefix and suffix task will be added. 
        """
        ltas_basename = func.__name__
        func.__root_enter_task_label__ = f"{ltas_basename}:_root_enter_"
        func.__leaf_final_task_label__ = f"{ltas_basename}:_leaf_final_"
        @functools.wraps(func)
        def doit_task():
            trec = {'basename': ltas_basename,
                    'name': "_root_enter_",
                    'actions': None,
                    'task_dep': kwargs.get('task_dep', [])

                    }
            yield trec


            all_ltas_tasks = []
            if ltas.task_failed_abort_execution == False:
                task_dep = []


                ltas.set_super_task_seq(ltas_basename, task_dep=task_dep)


                yield from func(ltas)
                all_ltas_tasks.extend(ltas.ltas_taskseq_labels)
            else:
                logger.info(f"LTAS-abort-taskgen:")

            # there is only a single ltas with no ipv6 suffix
            # trec = {'basename': ltas_basename,
            #         'name': "_leaf_final_",
            #         'actions': None,
            #         'task_dep': all_ltas_tasks
            #         }

            # yield trec



        doit_task.create_doit_tasks = doit_task
        return doit_task
    
    return wrapper

    
class LocalTaskActionSequence:
    """
    set the task in sequence:
    - local_step_pre
    - ship_files
    - remote_step
    - fetch_file
    - post
    """
    def __init__(self,
                 *args,
                 **kwargs):
        """
        """
        self.task_local_step = None
        self.subtask_seq_labels = None
        self.task_dep = None
        self.task_failed_abort_execution = False
        self.task_failed_exception = None
        self.os_type = kwargs.get("os_type", "openbsd")

    def set_task_local_step_iter(self):
        """
        """

        # all the task records 
        local_step_trecs = []
        def append(cmd, label, *args, **kwargs):
            """
            if cmd is string-- then the string is executed via fabric.run
            if cmd is a function -- its assumed that it is using dask to run python code remotely.
            
            """
            if isinstance(cmd, str):
                trec = {
                    'basename': self.basename,
                    'name': f"local_step:{label}",
                    'actions': [(action_wrapper(self, local_exec_cmd),
                                 [self,
                                                   f"{self.basename}:local_step:{label}",
                                                   cmd]
                                 )
                                ],
                    #'doc': f"{self.suffix_task_label}: remote step : {label}",
                    }
            else:
                #cmd is a dask function
                trec = {
                    'basename': self.basename,
                    'name': f"local_step:{label}",
                    'actions': [(action_wrapper(self, local_exec_func),
                                 [self,
                                  f"{self.basename}:local_step:{label}",
                                  cmd]
                                 )
                                ],
                    #'doc': f"{self.suffix_task_label}: remote step : {label}",
                    }


            trec['uptodate'] = kwargs.get('uptodate', [])

            trec['task_dep'] = kwargs.get('task_dep', [])

            if 'teardown' in kwargs:    
                trec['teardown'] = kwargs.get('teardown')
        
            if 'targets' in kwargs:
                trec['targets'] = kwargs.get('targets', [])
                
            if 'file_dep' in kwargs:
                trec['file_dep'] = kwargs.get('file_dep', [])
                
            local_step_trecs.append(trec)

            if self.task_dep:
                trec['task_dep'].extend(self.task_dep)
                self.task_dep = []

                
        def finalize():

            # put the task_dep on the first task
            if self.task_dep:
                local_step_trecs[0]['task_dep'].extend([self.task_dep])
                self.task_dep= []
            # chain the task dependecies
            
            num_tasks = len(local_step_trecs)
            for idx in range(1, num_tasks):
                local_step_trecs[idx]['task_dep'].append(get_ref_name(local_step_trecs[idx-1]))
                
            self.local_step_iter_final_trec = {
                'basename': self.basename,
                'name': 'local_step',
                'actions': None,
                'task_dep': [get_ref_name(local_step_trecs[-1])]

                }
            self.local_step_iter_final_task = f"{self.basename}:local_step"

        self.task_local_step_iter = local_step_trecs
        self.local_step_iter_finalize = finalize


        # dependency of last task iter

        self.final_task = f"{self.basename}:local_step"
        
        return append
    

    def __iter__(self):

        # prefix task must be send
        self.local_step_iter_finalize()
        task_curr = self.local_step_iter_final_task
        yield from self.task_local_step_iter
        yield self.local_step_iter_final_trec
                

        trec = {'basename': self.basename,
                'name': "_leaf_final_",
                'task_dep': [self.final_task
                                 
                             ],
                'actions': None
                }


        yield trec

    def set_super_task_seq(self, allroot_basename,
                           id_args= [], **kwargs):
        """
        task_dep  will be anchored on to prefix task
        """
        self.basename_super = f"""{allroot_basename}"""
        if id_args:
            self.basename_super = f"""{self.basename}:{ "_".join([str(_) for _ in id_args])}"""

        self.basename = self.basename_super
        self.task_remote_step_iter = None
        self.final_task = None
        self.task_failed_abort_execution = False
        self.task_failed_exception = None
        self.ltas_taskseq_labels = [f"{self.basename}:_leaf_final_"]


        # all first task in the rtas
        # should have task dep to the prefix (aka setup) task

        self.task_dep = [f"{allroot_basename}:_root_enter_", *kwargs.get('task_dep', [])]
        # capture the results of remote task execution
        # Note: only the last executed rtas results are maintained
        self.local_task_results = {}
        
    def set_new_subtask_seq(self, id_args= [], **kwargs):
        """
        subtask sequence:  a task sequence on the target node with additional qualifiers

        """
        self.basename = f"""{self.basename_super}:{ "_".join([str(_) for _ in id_args])}"""
        # non doit_taskify relies on task_label to accumalate tasks generated
        # doit_taskify relies on rtas_taskseq_labels
        #self.suffix_task_label = f"{self.basename}::rtas"
        
        self.task_remote_step_iter = None
        self.ltas_taskseq_labels.append(f"{self.basename}:_leaf_final_")
        # all sub-rtas has dependency to the teardown task of
        # the super task
        self.task_dep = [f"{self.basename_super}:_leaf_final_", *kwargs.get('task_dep', [])]
        pass

