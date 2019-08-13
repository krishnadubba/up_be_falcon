import logging
import logstash
from jaeger_client import Config
from statsd import StatsClient

from uggipuggi.constants import SERVER_RUN_MODE


def init_statsd(prefix=None, host='statsd', port=8125):
    statsd = StatsClient(host, port, prefix=prefix)
    return statsd


def init_logger(log_level=logging.INFO):
    logger = logging.getLogger()
    logger.addHandler(logstash.TCPLogstashHandler('logstash', 5000, version=1))
    if SERVER_RUN_MODE == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(log_level)
    return logger


def init_tracer(service):
    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'local_agent': {
                'reporting_host': "jaeger",
                'reporting_port': 5775,
            },
            'logging': True,
            'reporter_batch_size': 1,
        },

        service_name=service,
    )

    # this call also sets opentracing.tracer
    return config.initialize_tracer()
