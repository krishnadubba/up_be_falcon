# -*- coding: utf-8 -*-
import os
import falcon
import json
from uggipuggi.helpers.build_info import BuildInfo
from uggipuggi.helpers.logs_metrics import init_statsd

statsd = init_statsd('up.ping')

class Ping(object):
    """
    Can someone connect to us?
    Light weight connectivity test for other service's liveness and readiness probes.
    Return 200 OK if we got this far, framework will fail or not respond
    otherwise
    """
    @statsd.timer('get_ping_get')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        info = BuildInfo()
        run_env = os.environ.get('UGGIPUGGI_BACKEND_ENV', 'docker_compose')
        result = dict(id=0,
                      repoName=info.repo_name,
                      commitHash=info.commit_hash,
                      serviceType=info.service_type,
                      serviceName=info.service_name,
                      serviceVersion=info.version,
                      buildDate=info.build_date,
                      runEnv=run_env,
                      buildEpochSec=info.build_epoch_sec
                     )
        resp.body = json.dumps(result)