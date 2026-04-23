from pathlib import Path
import functools
import pickle
from patchwork.files import exists
remote_check_exists_list_picklepath = Path("remote_check_exists_list.pickle")
all_remote_check_exists_filepath_set = None
if remote_check_exists_list_picklepath.exists():
    all_remote_check_exists_filepath_set = pickle.load(remote_check_exists_list_picklepath.open("rb"))
    
    if all_remote_check_exists_filepath_set != None:
        #assert len(all_remote_check_exists_filepath_set) > 0
        if  len(all_remote_check_exists_filepath_set) ==  0:
            # TODO: investigate this 
            #print("TODO: DEBUG why all_remote_check_exists_filepath_set is == 0 ")
            #assert False
            pass
        pass
    #print("pickle load ", all_remote_check_exists_filepath_set)
else:
    #all_remote_check_exists_filepath_set = set()
    pass


precomputed_exists_file_status = None
def precompute_check_remote_files_exists(rtas_by_ip):
    global precomputed_exists_file_status
    
    global all_remote_check_exists_filepath_set
    if all_remote_check_exists_filepath_set == None:
        # filepath_set is not yet populated
        #all_remote_check_exists_filepath_set = set()
        return

    # TODO: fix the logic for all_remote_check_exists_filepath_set being == 0
    if len(all_remote_check_exists_filepath_set) == 0:
        # filepath_set is not yet populated
        #all_remote_check_exists_filepath_set = set()
        return 
    files = []
    rtas = None

    for aitem in all_remote_check_exists_filepath_set:
        files.append(aitem[1])
        rtas = rtas_by_ip[aitem[0]]
    results = {}

    # Run a single 'test' command for all files at once
    #cmd = " && ".join([f"test -e {file} && echo '{file}:1' || echo '{file}:0'" for file in files])

    
    cmd = " && ".join([f"test -e {file.strip()}  && echo '{file.strip()}:1' || echo '{file.strip()}:0'" for file in files])

    result = rtas.active_conn.run(cmd, hide=True)

    if result.stderr.strip():
        raise ValueError(f"precompute_check_remote_files_exists failed with error : {result.stderr.strip()}")


    file_exists_status = {}
    output = result.stdout.strip()

    for check_res in output.split():
        remote_target_fp, status = check_res.split(":")
        file_exists_status[(rtas.ipv6, remote_target_fp)] = status == '1'

    precomputed_exists_file_status = file_exists_status

    
def cache_remote_target_filepath(func):
    global all_remote_check_exists_filepath_set
    
    if all_remote_check_exists_filepath_set == None:
        all_remote_check_exists_filepath_set = set()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        fabric_conn = args[0]
        remote_targets = args[1]

        for remote_target in remote_targets:
            if all_remote_check_exists_filepath_set != None:
                all_remote_check_exists_filepath_set.add((fabric_conn.host, str(remote_target)
                                                      
                                                          )
                                                 )
        if precomputed_exists_file_status != None:
            host_ip = fabric_conn.host
            

            for remote_target in remote_targets:
                if (host_ip, str(remote_target)) in precomputed_exists_file_status:
                    if precomputed_exists_file_status[(host_ip, str(remote_target))] == False:
                        return False
                else:
                    #TODO: move to logging
                    #print(f"remote target ({host_ip}, {str(remote_target)})  not in precomputed result")
                    
                    if not exists(fabric_conn, remote_target):
                        return False
            return True
            
        else:

            return func(*args, **kwargs)

    return wrapper


    
    
def pickle_check_remote_target_set():
    #print("pickled files for remote exists = ", all_remote_check_exists_filepath_set)
    pickle.dump(all_remote_check_exists_filepath_set,
                remote_check_exists_list_picklepath.open("wb"))
    
