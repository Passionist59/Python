# -*- coding: utf-8 -*-
"""
this module define all service core for other modules in application
"""
import sys

sys.path.append("/usr/src/app/api")
import importlib
import os
from abc import ABCMeta, abstractmethod

BASE_MODULE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_CONF_DIR = BASE_MODULE + '/conf/'


class Discover(object):
    """
    This class allows to recover all files in an environment
    """

    def __init__(self, env: str = os.getenv('ENV', 'staging'), base_dir: str = None):
        self.env = env.lower()
        if base_dir is not None:
            if not os.path.isdir(base_dir):
                raise NotADirectoryError('This directory {0} not found'.format(base_dir))
            self.base_dir = base_dir
        else:
            self.base_dir = BASE_CONF_DIR

    @staticmethod
    def verify_path(path: list):
        """
        :param path: list of dir path
        """
        for p in path:
            if not os.path.isdir(p):
                raise NotADirectoryError('The default directory {0} not found'.format(p))

    def get_default_directory(self) -> list:
        """
        Return the default path of directory
        """
        path = [os.path.join(self.base_dir, 'default'), ]
        if self.env == 'prod':
            path.append(os.path.join(self.base_dir, 'prod'))
        elif self.env == 'testing':
            path.append(os.path.join(self.base_dir, 'testing'))
        elif self.env == 'staging':
            path.append(os.path.join(self.base_dir, 'staging'))
        else:
            path.append(os.path.join(self.base_dir, 'dev'))

        self.verify_path(path=path)
        return path

    def get_configuration_file(self, path: list = None) -> dict:
        """
        This method makes it possible to recover all the configuration files of a folder
        :param path: path to directory for search
        :return: list de class python
        """
        data = {'PYTHON': []}

        if path is None:
            path = self.get_default_directory()
        for p in path:
            files = self.get_files(path=p)
            data['PYTHON'] += files.get('PYTHON')

        return data

    @staticmethod
    def get_files(path: str) -> dict:
        """
        This method makes it possible to recover all the configuration files of a folder
        :param path: path to directory for search
        :return: tuple of list files config
        """
        py_files = []

        # _path = path if path and os.path.isdir(path) else self.directory
        for _path, dirs, files in os.walk(path):
            for filename in files:
                f = os.path.join(_path, filename)
                if os.path.isfile(f):
                    # _, ext = os.path.splitext(f)

                    if f.endswith('.py') and not filename.startswith('test_') and filename != '__init__.py':
                        _, ext = os.path.splitext(f)
                        py_files.append(str(_).split(BASE_MODULE)[1].replace('/', '.')[1:])

        return {'PYTHON': py_files}


class Config(metaclass=ABCMeta):
    """
    Abstract class for all class configuration
    """

    @staticmethod
    @abstractmethod
    def get_data(files: list) -> dict:
        """
        :param files: list of file
        :return:
        """
        pass


class ConfigPyFile(Config):
    """
    Allows you to retrieve the information contained in an .py configuration file
    the file is imported and the attributes are retrieved and passed into a dict
    """

    @staticmethod
    def get_data(files: list) -> dict:
        """
                loads the whole application and returns the list of services contained in
                the action files of the different modules
                :return: dict
                """

        attributes = dict()
        _module = list()

        for f in files:
            mod = importlib.import_module(f)
            try:
                for name, val in mod.__dict__.items():
                    if not str(name).startswith('__') and str(type(val)) != 'module':
                        attributes.update({name: val})
            except AttributeError as e:
                print(e)

        return attributes
