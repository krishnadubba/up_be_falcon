# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os, re
from configparser import ConfigParser

def get_config(env='dev', file_path=None):
    """
    :return: a dict parsed from a ConfigParser object, with config values loaded from file_path
    """
    # default env: 'dev'
    if not file_path:
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 '{}.ini'.format(env))

    config_parser = ConfigParser()
    if not config_parser.read(file_path):
        raise IOError('Invalid Config File. ConfigParser could not read config file: {}'.format(file_path))

    config_map = {}
    #os.environ['DOCKER_MACHINE_IP'] = 'localhost'
    for section in config_parser.sections():
        config_map[section] = {}
        for (k, v) in config_parser.items(section):
            matches = re.findall('%\(([A-Z_]+)\)', v)
            if len(matches) > 0:
                env_var = matches[0]
                v = re.sub('%\([A-Z_]+\)\w*', os.environ[env_var], v)
            config_map[section].update({k:v})
            
    return config_map

if __name__ == "__main__":
    config_file = 'docker_compose.ini'
    cfg = get_config(file_path=config_file)