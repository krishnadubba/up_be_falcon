from prometheus_client import CollectorRegistry, Counter, generate_latest


class PrometheusMiddleware(object):
    def __init__(self):
        self.registry = CollectorRegistry()
        self.requests = Counter(
            'http_total_request',
            'Counter of total HTTP requests',
            ['method', 'path', 'status'],
            registry=self.registry)

    def process_response(self, req, resp, resource, req_succeeded):    
        self.requests.labels(method=req.method, 
                             path=req.path, 
                             status=resp.status).inc()

    def on_get(self, req, resp):
        data = generate_latest(self.registry)
        resp.content_type = 'text/plain; version=0.0.4; charset=utf-8'
        resp.body = str(data.decode('utf-8'))