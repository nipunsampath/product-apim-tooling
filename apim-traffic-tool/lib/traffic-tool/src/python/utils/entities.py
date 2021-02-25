class Config:
    def __init__(self, **kwargs):
        self.protocol = kwargs.get('protocol')
        self.ip = kwargs.get('ip')
        self.port = kwargs.get('port')
        self.heavy_traffic = kwargs.get('heavy_traffic')
        self.time_patterns = kwargs.get('time_patterns')
        self.start_time = kwargs.get('start_time')
        self.post_data: list = kwargs.get('post_data')
        self.delete_data: list = kwargs.get('delete_data')
        self.end_time = kwargs.get('end_time')
        self.max_connection_refuse_count = kwargs.get('max_connection_refuse_count')
        self.dataset_file = kwargs.get('dataset_file')
        self.initial_timestamp = kwargs.get('initial_timestamp')
        # passing default value since the object is used in both generating traffic and invoking traffic
        self.script_runtime = kwargs.get('script_runtime', 0)
        self.no_of_data_points = kwargs.get('no_of_data_points', 0)
