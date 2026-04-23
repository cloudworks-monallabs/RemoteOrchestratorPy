from fabric import Connection, Config
ipv6 = "192.168.0.102"
ip = "192.168.0.102"
# === create rtas with fabric conn for 2 ssh users root and adming ===
cluster_resources_datadir="/home/adming/cluster_resources"
adming_public_key_file = "adming_ssh_rsa_public_key"
connect_kwargs = {
    "key_filename": f"{cluster_resources_datadir}/{adming_public_key_file}",
}
fabric_config = Config(overrides={
    'connect_kwargs': connect_kwargs,
    'run': {
        'hide': True,
        'warn': True,
        'echo': True
    },
})

fabric_conn_adming = Connection(host=ipv6,
                                user="adming",
                                config=fabric_config
                         )

fabric_conn_adming = Connection(host=ip,
                                      user="adming",
                                      config=fabric_config
                                      )
fabric_conn_adming.put("/home/kabira/Development/cloudworks-monallabs/RemoteOrchestratorPy/devel_tests/run_in_background.py", "/tmp")


#result = fabric_conn_adming.run("cd /tmp; python3 run_in_background.py &", hide=True)
command = "nohup python3 /tmp/run_in_background.py > /tmp/run.log 2>&1 &"
result = fabric_conn_adming.run(command, hide=True)
stdout = result.stdout.strip()
stderr = result.stderr.strip()

if not stderr:    
    print("remote command successful:", stdout)

else:
    print("remote command failed:", stderr)

    
#fabric_conn.put(file_to_ship, dest_dir)



