from copy import deepcopy
from doit.exceptions import TaskError as DoitTaskError
from ClusterShell.NodeSet import NodeSet
from ClusterShell.Task import Task, task_wait,   TaskError as ClushTaskError
from ClusterShell.Event import EventHandler
import doit
from doit.tools import run_once
import os
from pathlib import Path

from fabric import Connection
from patchwork.files import exists
from doit_extntools import RemoteFilesDep
initial_workdir = doit.get_initial_workdir()
if not initial_workdir:
    # we are running outside of pydoit enviorment
    initial_workdir = "./"
print("inital workdir = ", initial_workdir)


class LogEventHandler(EventHandler):
    def __init__(self):
        self.has_errors = False
        self.error_msgs = {}
        self.res_msgs = {}

    def ev_read(self, worker, node, sname, msg):

        if node not in self.res_msgs:
            self.res_msgs[node] = []

        # self.res_msgs[node] = self.res_msgs[node]  msg.decode('utf-8')
        self.res_msgs[node].append(msg)

    def ev_hup(self, worker, node, rc):
        if rc != 0:
            if node not in self.error_msgs:
                self.error_msgs[node] = []
            self.error_msgs[node].append(rc)
            # print(f"{node}: returned with error code {rc}")
            # self.error_msgs = self.error_msgs + \
            #     f"{node}: returned with error code {rc}\n"
            # this is the potential error
            self.has_errors = True


# Step 1: copy passphrase.txt and setup_local_https_deploy_machine.py"

task = Task()

task.set_info(
    'ssh_options', "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null")
task.set_info(
    'ssh_path', 'ssh -i /home/adming/cluster_resources/adming_ssh_rsa_pvt_key')
task.set_info('verbosity', 2)

ssh_user = "root"

task.set_info("ssh_user", "root")


def change_ssh_user(user):
    global ssh_user
    ssh_user = user
    task.set_info("ssh_user", user)


def log_command_exec_status(res_handler, task_label):
    if not res_handler.has_errors:
        with Path(os.path.join(initial_workdir, 'logs', f'{task_label}')).open("wb+") as fh:
            for node, msgs in res_handler.res_msgs.items():
                fh.write(f"IP Address: {node}\n".encode('utf-8'))
                for msg in msgs:
                    fh.write(msg + b"\n")
                fh.write(b"\n" + b"="*40 + b"\n")
        return "Success"
    else:

        with open(os.path.join(initial_workdir, 'errors', f'{task_label}'), "wb+") as fh:
            for node, msgs in res_handler.res_msgs.items():
                fh.write(f"IP Address: {node}\n".encode('utf-8'))
                error_codes = "error codes: " + \
                    ",".join(res_handler.error_msgs)
                error_codes = error_codes.encode('utf-8')
                fh.write(error_codes)
                for msg in msgs:
                    fh.write(msg + b"\n")
                fh.write(b"\n" + b"="*40 + b"\n")

        return "Failed"


def exec_task(cmd: str, task_label: str, nodeset: NodeSet, exit_on_fail=True):
    res_handler = LogEventHandler()
    task.shell(cmd,
               nodes=nodeset,
               handler=res_handler
               )
    task.resume()
    task_wait()
    status = log_command_exec_status(res_handler, task_label)
    if status == 'Failed':
        if exit_on_fail:
            print(f"task {task_label} failed..exiting")
            return ClushTaskError(f"exec_task {task_label} failed")
    return True


def copy_to_remote(src_fp, dest_dir, task_label, nodeset):
    if isinstance(src_fp, list):
        statuses = []
        for fp in src_fp:
            statuses.append(copy_to_remote_single(
                fp, dest_dir, task_label, nodeset))
        return statuses
    else:
        return copy_to_remote_single(src_fp, dest_dir, task_label, nodeset)


def copy_to_remote_single(src_fp, dest_dir, task_label, nodeset):
    res_handler = LogEventHandler()

    assert Path(src_fp).exists()
    task.copy(src_fp,
              dest_dir,
              nodes=nodeset,
              handler=res_handler
              )
    task.resume()
    task_wait()
    status = log_command_exec_status(res_handler, task_label)
    if status == 'Failed':
        return ClushTaskError("Copy to remote failed")

    return True


def copy_from_remote(dest_fp, local_dir, task_label, nodeset):
    if isinstance(dest_fp, list):

        for fp in dest_fp:
            status = copy_from_remote_single(fp,
                                             local_dir,
                                             task_label,
                                             nodeset
                                             )
            if isinstance(status, ClushTaskError):
                return status

        return True
    else:
        return copy_from_remote_single(dest_fp,
                                       local_dir,
                                       task_label,
                                       nodeset
                                       )


def copy_from_remote_single(dest_fp, local_dir, task_label, nodeset):
    res_handler = LogEventHandler()
    # because Clustershell doesn't complain on wrong copy
    task.rcopy(dest_fp,
               local_dir,
               nodes=nodeset,
               handler=res_handler
               )

    task.resume()
    task_wait()
    status = log_command_exec_status(res_handler, task_label)
    if status == 'Failed':
        return ClushTaskError("Copy from remote failed")
    return True


# ============= final apis resulting from merging of clustershell and doit =============
# generate ship file tasks
# generate exec local task
# generate exec remote task


def get_ref_name(trec):
    """
    """
    if isinstance(trec, str):
        return trec

    return f"""{trec['basename']}:{trec['name']}"""


def remote_exec_cmd(target_nodeset, exec_cmd_str, label):
    # PC = pipeline_constants[ipv6]
    if isinstance(exec_cmd_str, str):
        status = exec_task(exec_cmd_str,
                           label,
                           target_nodeset
                           )
        if isinstance(status, ClushTaskError):
            return DoitTaskError(status.args)
    else:

        for cmd_str in exec_cmd_str:
            status = exec_task(cmd_str,
                               label,
                               target_nodeset
                               )
            if isinstance(status, ClushTaskError):
                return DoitTaskError(status.args)


def gen_task_local_exec(func,
                        id_args,
                        args=[],
                        is_dep_task=True,
                        deps=[],
                        label=None,
                        ):
    """
    """

    basename = func.__name__
    if label:
        basename = label

    trec = {
        'name': "_".join([str(_) for _ in id_args]),
        'actions': [(func, [*id_args, *args])],
        'task_dep': [get_ref_name(_) for _ in deps],
        'uptodate': [run_once]
    }

    if is_dep_task:
        trec['basename'] = basename

    if hasattr(func, 'targets'):
        trec['targets'] = func.targets

    if hasattr(func, 'watch'):
        trec['watch'] = func.watch

    if hasattr(func, 'file_dep'):
        trec['file_dep'] = func.file_dep
    return trec


def gen_task_remote_exec(cmdstr,
                         target_nodeset,
                         id_args=[],
                         args=[],
                         label=None,
                         is_dep_task=False,
                         deps=[],
                         fabric_conn=None
                         ):
    """
    assumption:
    cmdstr: is either a string or callable
    1. all id_args are string
    2. func takes id_args as leading/lhs/first args
    3. basename is func.__name__
    4. label: exec_cmd label ; is also name of task if this is subtask 
    5. deps: task records that are part of task_deps
    TODO: add id_args, and args as arguments
    (ipv6, *id_args, *args) should go into cmdstr() call to generate the command string
    ipv6, *id_args : should form the name
    cmdstr.__name__ should form the basename
    """

    name = "_".join([str(_) for _ in id_args])
    if label is None:
        assert callable(cmdstr)
        label = cmdstr.__name__

    if callable(cmdstr):
        cmdstr_value = cmdstr(*id_args, *args)

        if isinstance(cmdstr_value, str):
            pass
        else:
            # cmdstr_value is a generator
            cmdstr_value = [_ for _ in cmdstr_value]

        # use function name as basename/exec_cmd_label
        pass

    rec = {'name': name,
           'actions': [(remote_exec_cmd, [target_nodeset, cmdstr_value, f"{label}_{name}"
                                          ])],
           'uptodate': [run_once]
           }

    if is_dep_task:
        rec['basename'] = label

    if deps:
        rec['task_dep'] = [get_ref_name(_) for _ in deps]

    rec['uptodate'] = []
    if fabric_conn is not None:
        if callable(cmdstr):
            if hasattr(cmdstr, 'remote_targets'):
                def check_remote_files_exists_local(remote_targets, fabric_conn=fabric_conn):
                    for _fs in remote_targets:
                        if not exists(fabric_conn, _fs):
                            print(
                                f"Path {_fs} does not exits")
                            return False

                    return True
                remote_targets = cmdstr.remote_targets
                rec['uptodate'] = [(check_remote_files_exists_local, [remote_targets])
                                   ]

    return rec


def ship_files(target_nodeset, files_to_ship, remote_dir, label):
    status = copy_to_remote(files_to_ship,
                            remote_dir,
                            label,
                            target_nodeset)

    if isinstance(status, ClushTaskError):
        return DoitTaskError(status.args)


def fetch_files(target_nodeset, files_to_fetch, remote_dir, label):
    status = copy_from_remote(files_to_fetch,
                              remote_dir,
                              label,
                              target_nodeset)

    if isinstance(status, ClushTaskError):
        return DoitTaskError(status.args)


def check_remote_files_exists(files_to_ship, remote_dir, fabric_conn):
    for _fs in files_to_ship:
        print("fabric_conn ", fabric_conn)

        if not exists(fabric_conn, f"{remote_dir}/{Path(_fs).name}"):
            print(f"Path {remote_dir}/{Path(_fs).name} does not exits")
            return False

    return True


def gen_task_ship_files(files_to_ship,
                        target_nodeset,
                        label,
                        id_args=[],
                        remote_dir="/tmp",
                        is_dep_task=True,
                        deps=[],
                        fabric_conn=None
                        ):
    """
    create a doit task to ship files to remote machine

    """
    name = "_".join([str(_) for _ in id_args])
    rec = {
        'name': name,
        'actions': [(ship_files, [target_nodeset,
                                  files_to_ship,
                                  remote_dir,
                                  f"{label}_{name}"])
                    ],

        'file_dep': files_to_ship,
        'task_dep': [get_ref_name(_) for _ in deps]
    }

    if is_dep_task == True:
        rec['basename'] = label

    if fabric_conn:

        def check_remote_files_exists_local(files_to_ship, remote_dir, fabric_conn=fabric_conn):
            for _fs in files_to_ship:
                if not exists(fabric_conn, f"{remote_dir}/{Path(_fs).name}"):
                    print(f"Path {remote_dir}/{Path(_fs).name} does not exits")
                    return False

            return True

        rec['uptodate'] = [(check_remote_files_exists_local, [
                            files_to_ship, remote_dir])]

    return rec


def gen_task_fetch_files(files_to_fetch,
                         target_nodeset,
                         label,
                         id_args=[],
                         local_dir="/tmp",
                         is_dep_task=True,
                         deps=[]
                         ):
    """
    create a doit task to ship files to remote machine

    """
    name = "_".join([str(_) for _ in id_args])
    rec = {
        'name': name,
        'actions': [(fetch_files, [target_nodeset,
                                   files_to_fetch,
                                   local_dir,
                                   f"{label}_{name}"])
                    ],
        'targets': [f"{local_dir}/{Path(_).name}" for _ in files_to_fetch

                    ],
        'uptodate': [run_once],
        'task_dep': [get_ref_name(_) for _ in deps]
    }

    if is_dep_task == True:
        rec['basename'] = label

    return rec


# === Moving to higher order notion of remote-task action sequence ===
# RemoteTaskActionSequence : RTAS: a sequence of 5 batches
# describe local_work_pre, ship_files, remote-work, ship-files, local_work_post
# together they form a remote task

def do_nothing():
    pass


def doit_task_generator_for_RTAS(rt_tag,
                                 ipv6,
                                 id_args=[],
                                 remote_work_dir="/tmp",
                                 local_work_dir="/tmp",
                                 target_nodeset=None,
                                 pre_deps=[],
                                 calc_dep=None,
                                 fabric_conn=None
                                 ):
    """
    rt_tag: an identifier for the remote task
    """
    if target_nodeset == None:
        target_nodeset = NodeSet(ipv6)

    # RemoteFiles

    def wrapper(local_steps_pre,
                to_ship_files,
                remote_steps,
                from_ship_files,
                local_steps_post,
                pre_deps=pre_deps,
                ):

        # if there is a need to calc dependency
        # then create a dummy task and add to it.

        if calc_dep:
            dummy_task = {'actions': [do_nothing],
                          'basename': f"{rt_tag}_dummy",
                          'name': "_".join([ipv6, *id_args])
                          }

            dummy_task['calc_dep'] = calc_dep
            yield deepcopy(dummy_task)
            pre_deps.append(get_ref_name(dummy_task))
        deps = []
        if local_steps_pre:
            trec_lsp = gen_task_local_exec(local_steps_pre,
                                           [ipv6, *id_args],
                                           label=f"{rt_tag}_lspre",
                                           deps=[*pre_deps,
                                                 ]

                                           )

            pre_deps = []
            deps = [deepcopy(trec_lsp)]
            yield trec_lsp

        if to_ship_files:
            trec_sf = gen_task_ship_files(to_ship_files,
                                          target_nodeset,
                                          label=f"{rt_tag}_tsf",
                                          id_args=[ipv6, *id_args],
                                          remote_dir=remote_work_dir,
                                          is_dep_task=True,
                                          deps=[*pre_deps, *deps],
                                          fabric_conn=fabric_conn
                                          )
            pre_deps = []
            deps = [deepcopy(trec_sf)]
            yield trec_sf

        if remote_steps:
            trec_rs = gen_task_remote_exec(remote_steps,
                                           target_nodeset,
                                           [ipv6, *id_args],
                                           label=f"{rt_tag}_rs",
                                           is_dep_task=True,
                                           deps=[*pre_deps, *deps],
                                           fabric_conn=fabric_conn
                                           )
            if to_ship_files:
                # make the task dependent on shipped files
                remote_files = [
                    f"{remote_work_dir}/{Path(_fs).name}" for _fs in to_ship_files]
                trec_rs['uptodate'].append(
                    RemoteFilesDep(ipv6, remote_files, ssh_user=ssh_user))

                pass

            pre_deps = []
            deps = [deepcopy(trec_rs)]
            yield trec_rs

        if from_ship_files:
            trec_ff = gen_task_fetch_files(from_ship_files,
                                           target_nodeset,
                                           label=f"{rt_tag}_ff",
                                           id_args=[ipv6, *id_args],
                                           local_dir=local_work_dir,
                                           is_dep_task=True,
                                           deps=[*pre_deps, *deps]
                                           )
            pre_deps = []
            deps = [deepcopy(trec_ff)]
            yield trec_ff

        if local_steps_post:
            trec_lsp = gen_task_local_exec(local_steps_post,
                                           [ipv6, *id_args],
                                           label=f"{rt_tag}_lspost",
                                           deps=[*pre_deps, *deps]
                                           )
            pre_deps = []
            deps = [deepcopy(trec_lsp)]
            yield trec_lsp

        wrapper.final_task = deps[0]
    return wrapper
