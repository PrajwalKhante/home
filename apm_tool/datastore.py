class DataStore:
    def __init__(self):
        self.http_metrics = []
        self.resource_metrics = []

    def add_http_metric(self, metric):
        self.http_metrics.append(metric)

    def add_resource_metric(self, metric):
        self.resource_metrics.append(metric)

    def get_http_metrics(self):
        return self.http_metrics

    def get_resource_metrics(self):
        return self.resource_metrics

datastore = DataStore()
