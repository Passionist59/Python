# -*- coding: utf-8 -*-
import sys

sys.path.append("/usr/src/app/api")
import os
from core.config_helpers import Discover, ConfigPyFile


config = {}
"""
 Setup and switch application profile
"""

discover = Discover(env=os.getenv('ENV', 'testing'))
config_files = discover.get_configuration_file()
config.update(ConfigPyFile.get_data(config_files.get('PYTHON')))