"""
v2: all remote conn work is done by fabric_conn; clustershell will be used for parallelism.

Things to keep in mind:
- ssh_user
- the ssh private key
- consistent naming
- uptodate
"""
from pipeline_constants import *
from doit_rtas_helpers import (log_command_exec_status,
                               ship_file,
                               fetch_file,
                               get_ref_name
                               )
from fabric import Connection
from fabric import Connection, Config
from patchwork.files import exists
import logging
from doit_extntools import RemoteFilesDep

logger = logging.getLogger(__name__)


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
        basename: the task basename
        id_args: a tuple to identify the subtask
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


        # prefix task dependency
        self.task_dep = None
        
        connect_kwargs = {
            "key_filename": f"{cluster_resources_datadir}/{adming_public_key_file}",
        }

        config = Config(overrides={
            'connect_kwargs': connect_kwargs,
            'run': {
                'hide': True,
                'warn': True,
                'echo': True
            },
        })


        self.user_adming_conn = Connection(host=self.ipv6,
                                           user="adming",
                                           config=config
                                           )
        self.user_root_conn = Connection(host=self.ipv6,
                                           user="root",
                                           config=config
                                           )
        
        self.active_conn = self.user_adming_conn #self.user_root_conn
        
        
    def set_ssh_user(self, user="adming"):
        if user == "root":
            self.active_conn = self.user_root_conn
        else:

            self.active_conn = self.user_adming_conn

        
    def __del__(self):
        """
        cleanup resources
        """
        print("Admin connection closed.")
        self.user_adming_conn.close()
        self.user_root_conn.close()
        pass
    
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
            'doc': f"""{self.task_label}: {kwargs.get("doc", "local-step-pre")}"""
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

    def set_task_ship_files_iter(self, files_to_ship, dest_dir):
        self.task_ship_files_prefix = {'basename': self.basename,
                                      'name': f"ship_files_prefix",
                                      'task_dep': [],
                                      'actions': None
                                      
                                      }
        self.task_ship_files_prefix['task_dep'].extend(self.task_dep)

        # once you yield the trec ecord to doit
        # it is unsuable
        task_label_ship_files_prefix = get_ref_name(self.task_ship_files_prefix)
        
        self.task_dep = []

        
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
                    'action': None,
                    
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
                self.task_remote_step["task_dep"].append(task_curr)
            task_curr = get_ref_name(self.task_remote_step)
            yield self.task_remote_step
            
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

    def set_task_label(self, basename, id_args= []):
        self.basename = f"""{basename}:{self.ipv6}:{ "_".join([str(_) for _ in id_args])}"""
        self.task_local_step_pre = None
        self.task_ship_files_iter = None
        self.task_remote_step = None
        self.task_fetch_files_iter = None
        self.task_local_step_post = None
        self.final_task = None
        self.task_label = f"{self.basename}:rtas"
        # prefix task dependency: the prefix task runs before
        # any task in the rtas
        self.task_dep = [f"{basename}_prefix"]
