# Copyright (c) 2019, WSO2 Inc. (http://www.wso2.org) All Rights Reserved.
#
# WSO2 Inc. licenses this file to you under the Apache License,
# Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
import random
from collections import defaultdict
from constants import *


# To store user details
class User:
    def __init__(self, ip, token, cookie):
        self.ip = ip
        self.token = token
        self.cookie = cookie


# To store API details
class API:
    def __init__(self, protocol, host, port, context, version, name):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.context = context
        self.name = name
        self.version = version
        self.resources = defaultdict(list)
        self.base_url = "{}://{}:{}/{}/{}".format(protocol, host, port, context, version)
        self.users = []
        self.single_user = None

    def add_resource(self, method, path):
        self.resources[method].append(path)

    def set_single_user(self):
        self.single_user = random.choice(self.users)


class Config:
    def __init__(self, **kwargs):
        self.protocol = kwargs.get(PROTOCOL)
        self.ip = kwargs.get(IP)
        self.port = kwargs.get(PORT)
        self.time_patterns = kwargs.get(TIME_PATTERNS)
        self.start_time = kwargs.get(START_TIME)
        self.payloads: list = kwargs.get(PAYLOADS)
        self.user_agents: list = kwargs.get(USER_AGENTS)
        self.start_timestamp = kwargs.get(START_TIMESTAMP)
        self.compromised_user_count = kwargs.get(COMPROMISED_USER_COUNT)
        self.dataset_path = kwargs.get(DATASET_PATH)
        # passing default value since the object is used in both generating traffic and invoking traffic
        self.attack_duration = kwargs.get(ATTACK_DURATION, 0)
        self.no_of_data_points = kwargs.get(NO_OF_DATA_POINTS, 0)
