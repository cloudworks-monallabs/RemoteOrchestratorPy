"""
v2: all remote conn work is done by fabric_conn; clustershell will be used for parallelism.

Things to keep in mind:
- ssh_user
- the ssh private key
- consistent naming
- uptodate
"""


from doit_rtas_helpers import (log_command_exec_status,
                               ship_file,
                               fetch_file,
                               get_ref_name
                               )

from patchwork.files import exists
from doit_extntools import RemoteFilesDep
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def make_task(func):
    """make decorated function a task-creator"""
    #func.create_doit_tasks = func
    # flip
    def another_task_func():
        trec = {'basename': "switched_task",
                'name': "task1",
                'actions': ['echo bye'],
                #'task_dep': [rtas.task_label]
                }
        yield trec

    another_task_func.create_doit_tasks = another_task_func
    return another_task_func


# def doit_taskify(func):
#     """
#     convert a function to a rtas task sequence generator function.
#     prefix and suffix task will be added. 
#     """
#     print ("did we ever got called")
#     rtas_basename = func.__name__
#     def doit_task(rtas):
#         print("create task for rtas with ipv6 = ", rtas.ipv6)
#         trec = {'basename': f"{rtas_basename}_prefix",
#                 'actions': None,
#                 }
#         yield trec
        
#         rtas.set_new_task_seq(rtas_basename)
#         yield from rtas
        
        
#         yield trec
        

#     trec = {'basename': rtas_basename,
#             'actions': None,
#             'task_dep': [rtas.task_label]
#             }
        
#     yield trec
    
#     # make doit read tasks from this function
#     doit_task.create_doit_tasks = doit_task

#     return doit_task
def doit_taskify(all_rtas, **kwargs):
    """
    all_rtas: list of RemoteTaskActionSequence. Each rtas represents a compte node on which to invoke action sequence
    """
    def wrapper(func):
        """
        convert a function to a rtas task sequence generator function.
        prefix and suffix task will be added. 
        """
        rtas_basename = func.__name__
        def doit_task():
            #setup group task
            trec = {'basename': f"{rtas_basename}_prefix",
                    'actions': None,
                    'task_dep': kwargs.get('task_dep', [])

                    }
            yield trec


            
            for rtas in all_rtas:
                rtas.set_super_task_seq(rtas_basename)
                yield from func(rtas)
                

            # the teardown group task:
            # has task dep to all super and sup rtas teardown task 
            trec = {'basename': rtas_basename,
                    'actions': None,
                    'task_dep': rtas.rtas_taskseq_labels
                    }

            yield trec

        doit_task.create_doit_tasks = doit_task
        return doit_task
    return wrapper

    
# def doit_taskify(rtas, **kwargs):
#     #assert rtas is not None
#     def wrapper(func):
#         """
#         convert a function to a rtas task sequence generator function.
#         prefix and suffix task will be added. 
#         """
#         rtas_basename = func.__name__
#         def hook_for_set_new_task(*arg, **kwargs):
#             assert False
            
#         def doit_task():
#             #prefix for rtas task sequence
#             trec = {'basename': f"{rtas_basename}_prefix",
#                     'actions': None,
#                     'task_dep': kwargs.get('task_dep', [])
                    
#                     }
#             yield trec
#             rtas.set_new_task_seq(rtas_basename)
#             #call user func to create rtas tasks
#             func(rtas)
#             # ========================== end =========================
            
#             # disable set_new_seq for now
#             #rtas.set_new_task_seq = None
#             yield from rtas

#             # group task representing rtas
#             trec = {'basename': rtas_basename,
#                     'actions': None,
#                     'task_dep': [rtas.task_label]
#                     }
        
#             yield trec

#         doit_task.create_doit_tasks = doit_task
#         return doit_task
#     return wrapper


def remote_exec_cmd(self,  task_label, *args):

    status = "Success"

    for cmdstr in args:

        result = self.active_conn.run(cmdstr, hide=True)
        
        status = log_command_exec_status(cmdstr,
                                         result,
                                         task_label,
                                         self.ipv6
                                )
        if status == "Failed":
            break

    return status

def check_remote_files_exists(fabric_conn, remote_targets):

    logger.info(f"remote_step: Checking if remote target exists: { remote_targets}")
    
    for _fs in remote_targets:
        if not exists(fabric_conn, _fs):
            logger.info(
                f"Path {_fs} does not exits")
            return False

    logger.info(f"All remote targets  exists")
        
    return True
            
class RemoteTaskActionSequence:
    """
    set the task in sequence:
    - local_step_pre
    - ship_files
    - remote_step
    - fetch_file
    - post
    """
    def __init__(self,
                 ipv6,
                 *args,
                 **kwargs):
        """
        """
        #self.basename = f"""{basename}:{ipv6}:{ "_".join([str(_) for _ in id_args])}"""
        # the label for the group task from this rtas
        # to be used as task_dep 
        #self.task_label = f"{self.basename}:rtas"
        
        self.ipv6 = ipv6
        
        self.task_local_step_pre = None
        self.task_ship_files_iter = None
        self.task_remote_step = None
        self.task_fetch_files_iter = None
        self.task_local_step_post = None
        self.final_task = None

        # to maintain a list of all sub-task sequences label
        # created for a task sequence
        self.rtas_subtask_seq_labels = None

        # prefix task dependency
        self.task_dep = None


        # a set of ssh users on remote target is maintained
        # use set_ssh_user to invoke an action on remote target
        # via choosen user

        self.ssh_users_fabric_conn = {}
        
        # connect_kwargs = {
        #     "key_filename": f"{cluster_resources_datadir}/{adming_public_key_file}",
        # }

        # config = Config(overrides={
        #     'connect_kwargs': connect_kwargs,
        #     'run': {
        #         'hide': True,
        #         'warn': True,
        #         'echo': True
        #     },
        # })


        # self.user_adming_conn = Connection(host=self.ipv6,
        #                                    user="adming",
        #                                    config=config
        #                                    )
        # self.user_root_conn = Connection(host=self.ipv6,
        #                                    user="root",
        #                                    config=config
        #                                    )
        
        # self.active_conn = self.user_adming_conn #self.user_root_conn
        self.active_conn = None
        


    def add_ssh_user(self, user_name, fabric_conn, make_active="False"):
        self.ssh_users_fabric_conn[user_name] = fabric_conn
        if make_active:
            self.active_conn = self.ssh_users_fabric_conn[user_name]
        
    def set_active_user(self, user="adming"):
        assert user in self.ssh_users_fabric_conn
        
        self.active_conn = self.ssh_users_fabric_conn[user]

        
    # def __del__(self):
    #     """
    #     cleanup resources
    #     """
    #     print("Admin connection closed.")
    #     for user, conn in self.ssh_users_fabric_conn:
    #         conn.close()
    #     pass
    
    def set_task_local_step_pre(self,
                           step_func,
                           *args,
                           **kwargs
                           ):
        """
        args  will be passed stepfunc as is.
        **kwargs has task directives like targets etc. 
        """
        trec = {
            'basename': self.basename,
            'name': "local_step_pre",
            'task_dep' : kwargs.get('task_dep', []),
            'actions': [(step_func, args)],
            'doc': f"""{self.task_label}:{kwargs.get("doc", "local-step-pre")}"""
            }
        
        if 'targets' in kwargs:
            trec['targets'] = kwargs.get('targets')

        if 'file_dep' in kwargs:
            trec['file_dep'] = kwargs.get('file_dep')

        if 'uptodate' in kwargs:
            trec['uptodate'] = kwargs.get('uptodate')
            
            


        # update prefix task dep
        trec['task_dep'].extend(self.task_dep)
        self.task_dep = []

        self.task_local_step_pre = trec
        self.final_task = f"{self.basename}:local_step_pre"
        pass

    def set_task_ship_files_iter(self, files_to_ship, dest_dir, **kwargs):
        
        """
        kwargs: task_dep 
        """
        self.task_ship_files_prefix = {'basename': self.basename,
                                      'name': f"ship_files_prefix",
                                      'task_dep': [],
                                      'actions': None
                                      
                                      }
        self.task_ship_files_prefix['task_dep'].extend(self.task_dep)
        self.task_dep = []

        # once you yield the trec ecord to doit
        # it is unsuable
        task_label_ship_files_prefix = get_ref_name(self.task_ship_files_prefix)
        


        if 'task_dep' in kwargs:
            self.task_ship_files_prefix['task_dep'].append(kwargs.get('task_dep')
                                                           )
            
        
        def ship_task_iter():
            for file_to_ship in files_to_ship:
                file_basename = Path(file_to_ship).name
                trec = {
                    'basename': self.basename,

                    'name': f"ship_file:{file_basename}",
                    'actions': [(ship_file, [self.active_conn,
                                             file_to_ship,
                                             dest_dir
                                             ])

                                ],
                    'uptodate': [(check_remote_files_exists,
                                     [self.active_conn, [f"{dest_dir}/{file_basename}"]]
                                     )
                                    
                                 ],
                    'file_dep': [file_to_ship],
                    'doc': f"{self.task_label}: ship local file to remote: {file_to_ship}",
                    'task_dep': [task_label_ship_files_prefix]

                    }


                yield trec

        

        # file path  on remote location
        # to be used as file_dep for next task
        self.shipped_files = [f"{dest_dir}/{Path(file_to_ship).name}" for file_to_ship in files_to_ship
        ]
        # the group task for ship file
        # create a group task for all the shipped files
        trec = {'basename': self.basename,
                    'name': f"ship_files",
                    'task_dep': [f"{self.basename}:ship_file:{Path(file_to_ship).name}" for file_to_ship in files_to_ship
                                 
                                 ],
                'actions': None,
                    'doc': f"{self.task_label}: group task for file ship to remote"
                }

        
        self.task_ship_files_iter  = ship_task_iter()
        self.task_ship_files_group = trec
        self.final_task = f"{self.basename}:ship_files"

    def set_task_remote_step(self, *args, **kwargs):
        """
        args is a list of string
        each a command to be run on remote machine
        kwargs['targets'] impiles remote targets
        
        
        """
        trec = {
            'basename': self.basename,
            'name': "remote_step",
            'actions': [(remote_exec_cmd, [self,
                                           f"{self.basename}:remote_step",
                                           *args])],
            'doc': f"{self.task_label}: remote-step",
            }


        trec['uptodate'] = kwargs.get('uptodate', [])
        trec['task_dep'] = kwargs.get('task_dep', [])

        # file_dep is dependency on local file and not on the files on remote destination 
        if 'local_file_dep' in kwargs:
            trec['file_dep'] = kwargs.get('local_file_dep')
            
        
        #target implies remote targets
        if 'targets' in kwargs:
            trec['uptodate'].append((check_remote_files_exists,
                                     [self.active_conn, kwargs.get('targets')]
                                     )
                                    )
            

        #file_dep implies remote file_dep
        if 'file_dep' in kwargs:
            trec['uptodate'].append(RemoteFilesDep(self.active_conn,
                                                   kwargs.get('file_dep')
                                                   )
                                    )

        # add the shipped files as dependency for remote task
            
        if self.task_ship_files_iter:
            trec['uptodate'].append(RemoteFilesDep(self.active_conn,
                                                   self.shipped_files)
                                    )

        # make task_ship_files as task dep 
        if self.task_ship_files_iter:
            trec['task_dep'].append(f"{self.basename}:ship_files"

                )
            
        self.task_remote_step = trec
        if self.task_dep:
            trec['task_dep'].extend(self.task_dep)
            self.task_dep = []
            
        self.final_task = f"{self.basename}:remote_step"

        pass


    def set_task_remote_step_iter(self):
        """
        """

        # all the task records 
        remote_step_trecs = []
        def append(cmd, label, *args, **kwargs):
            """
            if cmd is string-- then the string is executed via fabric.run
            if cmd is a function -- its assumed that it is using dask to run python code remotely.
            
            """
            if isinstance(cmd, str):
                trec = {
                    'basename': self.basename,
                    'name': f"remote_step:{label}",
                    'actions': [(remote_exec_cmd, [self,
                                                   f"{self.basename}:remote_step:{label}",
                                                   cmd])],
                    'doc': f"{self.task_label}: remote step : {label}",
                    }
            else:
                #cmd is a dask function
                trec = {
                    'basename': self.basename,
                    'name': f"remote_step:{label}",
                    'actions': [(cmd, args)],
                    'doc': f"{self.task_label}: remote step : {label}",
                    }


            trec['uptodate'] = kwargs.get('uptodate', [])
            trec['task_dep'] = kwargs.get('task_dep', [])

            # local_file_dep is dependency on local file and not on the files on remote destination 
            if 'local_file_dep' in kwargs:
                trec['file_dep'] = kwargs.get('local_file_dep')
            
        
            #target implies remote targets
            if 'targets' in kwargs:
                trec['uptodate'].append((check_remote_files_exists,
                                         [self.active_conn, kwargs.get('targets')]
                                         )
                                        )
            

            #file_dep implies remote file_dep
            if 'file_dep' in kwargs:
                trec['uptodate'].append(RemoteFilesDep(self.active_conn,
                                                       kwargs.get('file_dep')
                                                       )
                                        )
            remote_step_trecs.append(trec)

            # not adding the shipped files as dependency
            # done
            


            # #TODO:
            # # make task_ship_files as task dep 
            # if self.task_ship_files_iter:
            #     trec['task_dep'].append(f"{self.basename}:ship_files"

            #                             )
            
            if self.task_dep:
                trec['task_dep'].extend(self.task_dep)
                self.task_dep = []

                
        def finalize():
            assert len(remote_step_trecs) > 1
            # put the task_dep on the first task
            if self.task_dep:
                remote_step_trecs[0]['task_dep'] = [self.task_dep]
                self.task_dep= []
            # chain the task dependecies
            
            num_tasks = len(remote_step_trecs)
            for idx in range(1, num_tasks):
                remote_step_trecs[idx]['task_dep'] = [get_ref_name(remote_step_trecs[idx-1])]
                
            self.remote_step_iter_final_trec = {
                'basename': self.basename,
                'name': 'remote_step',
                'actions': None,
                'task_dep': [get_ref_name(remote_step_trecs[-1])]

                }
            self.remote_step_iter_final_task = f"{self.basename}:remote_step"

        self.task_remote_step_iter = remote_step_trecs
        self.remote_step_iter_finalize = finalize

        # TODO: yield the final task which will have
        # dependency of last task iter

        self.final_task = f"{self.basename}:remote_step"
        
        return append
    
    
        pass

    
    def set_task_fetch_files_iter(self,
                                  files_to_fetch,
                                  local_dir="/tmp"):
        self.task_fetch_files_prefix = {'basename': self.basename,
                                      'name': f"fetch_files_prefix",
                                      'task_dep': [],
                                      'actions': None
                                      
                                      }
        task_label_fetch_files_prefix = get_ref_name(self.task_fetch_files_prefix)
        if self.task_dep:
            self.task_fetch_files_prefix['task_dep'].extend(self.task_dep)
            self.task_dep = []

        def fetch_task_iter():
            for file_to_fetch in files_to_fetch:
                file_basename = Path(file_to_fetch).name
                trec = {
                    'basename': self.basename,

                    'name': f"fetch_file:{file_basename}",
                    'actions': [(fetch_file, [self.active_conn,
                                              file_to_fetch,
                                              local_dir
                                             ])

                                ],
                    'targets': [f"{local_dir}/{Path(file_to_fetch).name}"
                                ],
                    

                    'uptodate': [RemoteFilesDep(self.active_conn,[file_to_fetch])], 
                    'doc': f"{self.task_label}: fetch-file {file_to_fetch}",
                    'task_dep': [task_label_fetch_files_prefix]
                    
                    
                    }

                yield trec

                # create a group task for all the shipped files

        # to add as depency to local_step_post
        trec = {'basename': self.basename,
                    'name': f"fetch_files",
                    'task_dep': [f"{self.basename}:fetch_file:{Path(file_to_fetch).name}" for file_to_fetch in files_to_fetch
                                 
                                 ],
                    'actions': None,
                    
                    'doc': f"{self.task_label}: group-task: fetch-files"
                    }


            
        self.task_fetch_files_group = trec
        self.fetched_files = [f"{local_dir}/{Path(file_to_fetch).name}" for file_to_fetch in files_to_fetch]
        self.task_fetch_files_iter  = fetch_task_iter()
        self.final_task = f"{self.basename}:fetch_files"
        pass
    
        
    def set_task_local_step_post(self, step_func, *args, **kwargs):
        """
        args  will be passed stepfunc as is.
        **kwargs has task directives like targets etc. 
        """
        trec = {
            'basename': self.basename,
            'name': "local_step_post",
            'task_dep' : kwargs.get('task_dep', []),
            'actions': [(step_func, args)],
            'doc': f"{self.task_label}: local_step_post"
            }
        if 'targets' in kwargs:
            trec['targets'] = kwargs.get('targets')
            

        trec['file_dep'] = kwargs.get('file_dep', [])

        if 'uptodate' in kwargs:
            trec['uptodate'] = kwargs.get('uptodate')
            

        # apply rtas's task dependencies
        if self.task_fetch_files_iter:
            trec['file_dep'].extend(self.fetched_files)

        else:
            # put a hard dependency to previous task
            pass
            
        self.task_local_step_post = trec
        self.final_task = f"{self.basename}:local_step_post"
        if self.task_dep:
            trec['task_dep'].extend(self.task_dep)
            self.task_dep = []
        pass


    def __iter__(self):

        # prefix task must be send
    
        task_curr = None
        
        if self.task_local_step_pre:
            task_curr = get_ref_name(self.task_local_step_pre)

            yield self.task_local_step_pre

        if self.task_ship_files_iter:
            if task_curr:
                self.task_ship_files_prefix["task_dep"].append(task_curr

                    )
            task_curr = get_ref_name(self.task_ship_files_group)

                
            yield self.task_ship_files_prefix
            yield from self.task_ship_files_iter
            yield self.task_ship_files_group

            
        if  self.task_remote_step:
            if task_curr:
                # remote step already has dependency on ship files
                # sometimes remote step task dependency can have duplicates
                self.task_remote_step["task_dep"].append(task_curr)
            task_curr = get_ref_name(self.task_remote_step)
            yield self.task_remote_step

        elif self.task_remote_step_iter:
            self.remote_step_iter_finalize()
            
            if task_curr:
                self.task_remote_step_iter[0]['task_dep'].append(task_curr)
            
            task_curr = self.remote_step_iter_final_task
            yield from self.task_remote_step_iter
            yield self.remote_step_iter_final_trec
                
            
        if self.task_fetch_files_iter:
            if task_curr:
                self.task_fetch_files_prefix["task_dep"].append(task_curr

                    )
            task_curr = get_ref_name(self.task_fetch_files_group)

            yield self.task_fetch_files_prefix
            yield from self.task_fetch_files_iter
            yield self.task_fetch_files_group

        if self.task_local_step_post:
            if task_curr:
                self.task_local_step_post["task_dep"].append(task_curr)
            task_curr = None
            yield self.task_local_step_post

        trec = {'basename': self.basename,
                'name': "rtas",
                'task_dep': [self.final_task
                                 
                             ],
                'actions': None
                }


        yield trec

    def set_super_task_seq(self, basename,
                         id_args= []):
        """
        task_dep  will be anchored on to prefix task
        """
        
        self.basename_super = f"""{basename}:{self.ipv6}:{ "_".join([str(_) for _ in id_args])}"""
        self.basename = self.basename_super
        self.task_local_step_pre = None
        self.task_ship_files_iter = None
        self.task_remote_step = None
        self.task_remote_step_iter = None
        self.task_fetch_files_iter = None
        self.task_local_step_post = None
        self.final_task = None

        # The super-rtas and all its sub-rtas are defined
        # by this task label. This is the last task in the group
        self.task_label = f"{self.basename_super}:rtas"

        # all the rtas (super and sub) defined under this rtas
        # will be used as dependency for group task with
        # basename (without the ipv6)
        self.rtas_taskseq_labels = [f"{self.basename_super}:rtas"]


        # all first task in the rtas
        # should have task dep to the prefix (aka setup) task
        self.task_dep = [f"{basename}_prefix"]

    def set_new_subtask_seq(self, id_args= []):
        """
        subtask sequence:  a task sequence on the target node with additional qualifiers

        """
        self.basename = f"""{self.basename_super}:{ "_".join([str(_) for _ in id_args])}"""
        self.task_local_step_pre = None
        self.task_ship_files_iter = None
        self.task_remote_step = None
        self.task_remote_step_iter = None
        self.task_fetch_files_iter = None
        self.task_local_step_post = None
        # these will be added as task_dep to the final group task
        self.rtas_taskseq_labels.append(f"{self.basename}:rtas")
        # all sub-rtas has dependency to the teardown task of
        # the super task
        self.task_dep = [f"{self.basename_super}:rtas"]
        pass
