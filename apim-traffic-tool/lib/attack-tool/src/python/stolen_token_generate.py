# Copyright (c) 2020, WSO2 Inc. (http://www.wso2.org) All Rights Reserved.
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

import ipaddress
import os
import pickle
import random
import string
import sys
from datetime import datetime, timedelta
from multiprocessing import Process, Lock, Value

import numpy as np
import yaml

from constants import *
from utilities import util_methods
from utilities.entity_classes import Config
from utils import log

abs_path = os.path.abspath(os.path.dirname(__file__))
logger = log.setLogger("Stolen_TOKEN")
current_data_points = Value('i', 0)
used_ips = []

# Constants
STOLEN_TOKEN = 'stolen_token'


# noinspection PyProtectedMember
def generate_unique_ip():
    """
    Returns a unique ip address
    :return: an unique ip
    """
    global used_ips

    random.seed()
    max_ipv4 = ipaddress.IPv4Address._ALL_ONES
    temp_ip = ipaddress.IPv4Address._string_from_ip_int(random.randint(0, max_ipv4))
    while temp_ip in used_ips:
        temp_ip = ipaddress.IPv4Address._string_from_ip_int(random.randint(0, max_ipv4))

    used_ips.append(temp_ip)
    return temp_ip


def generate_cookie():
    """
    generates a random cookie
    :return: a randomly generated cookie
    """
    letters_and_digits = string.ascii_lowercase + string.digits
    cookie = 'JSESSIONID='
    cookie += ''.join(random.choice(letters_and_digits) for _ in range(31))
    return cookie


def record_request(timestamp, path, access_token, method, user_ip, cookie, user_agent, dataset_path):
    """
    This function will write the invoke request data to a file
    :param timestamp: Timestamp of the request
    :param path: Invoke path of the request
    :param access_token: Access token of the request
    :param method: Http method of the request
    :param user_ip: User IP of the request
    :param cookie: User cookie of the request
    :param user_agent: User agent of the request
    :param dataset_path: path to the dataset file
    :return: None
    """
    accept = 'application/json'
    content_type = 'application/json'

    request_info = "{},{},{},{},{},{},{},{},{},\"{}\"".format(
        timestamp, user_ip, access_token, method, path, cookie, accept, content_type, user_ip, user_agent
    )
    util_methods.write_to_file(dataset_path, request_info, "a")


def simulate_user(user_data, total_data_point_count, configurations: Config, lock: Lock):
    """
      Simulate the behaviour of a user during the attack duration.
      :param lock:
      :param total_data_point_count:
      :param configurations:
      :param user_data: A dictionary containing the user data
      :return: None
      """

    timestamp = configurations.start_timestamp
    sleep_pattern = configurations.time_patterns[random.choice(list(configurations.time_patterns.keys()))]

    scenario_req_count = 0

    if scenario_req_count < configurations.no_of_data_points:
        for app in user_data.values():

            invoke_pattern_indices = util_methods.generate_method_invoke_pattern(app)

            while True:
                for i in invoke_pattern_indices:

                    if scenario_req_count >= configurations.no_of_data_points:
                        break

                    scenario = app[i]
                    invoke_path = scenario[2]
                    token = scenario[3]
                    http_method = scenario[4]
                    request_path = "{}://{}:{}/{}".format(
                        configurations.protocol, configurations.ip, configurations.port, invoke_path
                    )
                    random_user_agent = random.choice(configurations.user_agents)
                    random_ip = generate_unique_ip()
                    random_cookie = generate_cookie()

                    lock.acquire()
                    record_request(
                        timestamp, request_path, http_method, token, random_ip, random_cookie, random_user_agent,
                        configurations.dataset_path
                    )
                    total_data_point_count.value += 1
                    scenario_req_count += 1
                    lock.release()

                    sleep_time = util_methods.get_normal(sleep_pattern['mean'], sleep_pattern['std'])
                    timestamp += timedelta(seconds=sleep_time)


def main():
    global current_data_points, abs_path, logger

    try:
        with open(
                os.path.abspath(os.path.join(__file__, "../../../../traffic-tool/data/runtime_data/scenario_pool.sav")),
                "rb"
        ) as scenario_file:
            scenario_pool = pickle.load(scenario_file)

        with open(
                os.path.abspath(os.path.join(__file__, "../../../../../config/attack-tool.yaml")),
                "r"
        ) as attack_config_file:
            attack_config = yaml.load(attack_config_file, Loader=yaml.FullLoader)

    except FileNotFoundError as ex:
        logger.error("{}: \'{}\'".format(ex.strerror, ex.filename))
        sys.exit()

    configs: Config = Config()
    # Reading configurations from attack-tool.yaml
    configs.protocol = attack_config[GENERAL_CONFIG][API_HOST][PROTOCOL]
    configs.ip = attack_config[GENERAL_CONFIG][API_HOST][IP]
    configs.port = attack_config[GENERAL_CONFIG][API_HOST][PORT]
    configs.attack_duration = attack_config[GENERAL_CONFIG][ATTACK_DURATION]
    configs.no_of_data_points = attack_config[GENERAL_CONFIG][NO_OF_DATA_POINTS]
    configs.start_timestamp = attack_config[GENERAL_CONFIG][START_TIMESTAMP]
    configs.payloads = attack_config[GENERAL_CONFIG][PAYLOADS]
    configs.user_agents = attack_config[GENERAL_CONFIG][USER_AGENTS]
    configs.compromised_user_count = attack_config[ATTACKS][STOLEN_TOKEN][COMPROMISED_USER_COUNT]
    configs.time_patterns = util_methods.process_time_patterns(attack_config[GENERAL_CONFIG][TIME_PATTERNS])

    # Recording column names in the dataset csv file
    configs.dataset_path = "../../../../../../dataset/attack/stolen_token.csv"
    column_names = "timestamp,ip_address,access_token,http_method,invoke_path,cookie,accept,content_type," \
                   "x_forwarded_for,user_agent"
    util_methods.write_to_file(configs.dataset_path, column_names, "w")

    configs.start_time = datetime.now()

    logger.info("Stolen token attack started")

    if configs.compromised_user_count > len(scenario_pool):
        logger.error("More compromised users than the total users")
        sys.exit()

    compromised_users = np.random.choice(
        list(scenario_pool.values()), size=configs.compromised_user_count, replace=False
    )
    process_list = []
    lock = Lock()

    for user in compromised_users:
        process = Process(target=simulate_user, args=(user, current_data_points, configs, lock))
        process.daemon = False
        process_list.append(process)
        process.start()

        with open(os.path.abspath(os.path.join(__file__, "../../../data/runtime_data/attack_processes.pid")),
                  "a+") as f:
            f.write(str(process.pid) + '\n')

    total_data_points = configs.no_of_data_points * len(process_list)

    while True:
        if current_data_points.value >= total_data_points:
            for process in process_list:
                process.terminate()
            with open(abs_path + '/../../data/runtime_data/traffic_processes.pid', 'w') as file:
                file.write('')

            time_elapsed = datetime.now() - configs.start_time
            logger.info("Attack terminated successfully. Time elapsed: {} seconds".format(time_elapsed.seconds))
            break


# Program Execution
if __name__ == '__main__':
    main()
