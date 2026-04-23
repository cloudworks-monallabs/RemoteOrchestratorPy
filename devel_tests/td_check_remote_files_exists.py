from doit_rtas import RemoteTaskActionSequence, doit_taskify
import sys
from fabric import Connection, Config
from pathlib import Path
import os
from doit.tools import run_once


# === create rtas with fabric conn for 2 ssh users root and adming ===



cluster_resources_datadir="/home/adming/cluster_resources"
adming_public_key_file = "adming_ssh_rsa_public_key"
connect_kwargs = {
    "key_filename": f"{cluster_resources_datadir}/{adming_public_key_file}",
}

ipv6 = "192.168.0.102"

fabric_config = Config(overrides={
    'connect_kwargs': connect_kwargs,
    'run': {
        'hide': True,
        'warn': True,
        'echo': True
    },
})

fabric_conn_root = Connection(host=ipv6,
                              user="root",
                              config=fabric_config
                         )

fabric_conn_adming = Connection(host=ipv6,
                                user="adming",
                                config=fabric_config
                         )

