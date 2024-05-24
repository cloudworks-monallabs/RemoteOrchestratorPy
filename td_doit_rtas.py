from pipeline_constants import *


unit_worker_id = 0
ipv6 = "45.32.0.19"
rtas = RemoteTaskActionSequence("build_deploy_webapp_bundle",
                     [unit_worker_id],
                     ipv6,
                     )

                     
