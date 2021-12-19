# -*- coding: utf-8 -*-
"""
this module define all service core for other modules in application
"""

import sys

sys.path.append("/usr/src/app/api")
import requests
from abc import ABCMeta, abstractmethod
from core.settings import config


class RequestConnector(metaclass=ABCMeta):
    """
    this class is a abstraction for all class http request
    """

    def __init__(self):
        self.headers = config['HEADER']

    def get_headers(self) -> dict:
        """

        :return: the headers attribute
        """
        return self.headers

    def set_headers(self, headers: dict):
        """
        override headers attribute with data passed in argument
        :param headers:
        """
        if not isinstance(headers, dict):
            raise ValueError(u'argument expected is dict type')

        self.headers = headers

    def add_headers(self, header: dict):
        """
        insert a key, value in headers attribute
        :param header: key, value
        """
        if not isinstance(header, dict):
            raise ValueError(u'argument expected is dict type')

        self.headers.update(header)

    @abstractmethod
    def get(self, url: str, query: dict = None, headers: dict = None, **kwargs) -> dict:
        """
        this method execute the GET request

        :param query: the query parameters
        :param url:
        :param headers:
        """

        pass

    @abstractmethod
    def post(self, url: str, data: dict, headers: dict = None, **kwargs) -> dict:
        """
        this method execute the POST request

        :param data:
        :param url:
        :param headers:
        """

        pass

    @abstractmethod
    def put(self, url: str, data: dict, headers: dict = None, **kwargs) -> dict:
        """
        this method execute the PUT request

        :param data:
        :param url:
        :param headers:
        """

        pass

    @abstractmethod
    def patch(self, url: str, data: dict, headers: dict = None, **kwargs) -> dict:
        """
        this method execute the PATCH request

        :param data:
        :param url:
        :param headers:
        """

        pass

    @abstractmethod
    def delete(self, url: str, headers: dict = None, **kwargs) -> dict:
        """
        this method execute the DELETE request

        :param url:
        :param headers:
        """

        pass


class HTTPJsonRequest(RequestConnector):
    """
    This class an implementation of RequestConnector based on requests library
    """

    def __init__(self):
        super().__init__()
        self.request = requests

    def execute_request(self, url: str, method: str = 'GET', payload: dict = None,
                        headers: dict = None, **kwargs) -> dict:
        """

        :param method: HTTP Request Method
        :param url: The complete url, if provided it is used for the request
        :param payload: data send to server
        :param headers: HTTP Header
        :return:
        """

        headers = headers if headers else self.get_headers()
        response = None
        if method == "GET":
            response = self.request.get(url=url, headers=headers, params=payload, **kwargs)

        elif method == "POST":
            response = self.request.post(url=url, headers=headers, json=payload, **kwargs)
        elif method == "PUT":
            response = self.request.put(url=url, headers=headers, json=payload, **kwargs)
        elif method == "DELETE":
            response = self.request.delete(url=url, headers=headers, **kwargs)

        data = {
            'code': response.status_code,
            'data': None,
            'errors': None
        }
        if response.status_code == 200:
            response.encoding = 'utf-8'
            data['data'] = response.json()
        else:
            data['errors'] = response.reason

        return data

    def get(self, url: str, query: dict = None, headers: dict = None, **kwargs) -> dict:
        """
        call execute_request for GET request
        :param query:
        :param url:
        :param headers:
        :return: the response of server
        """

        return self.execute_request(url=url, method="GET", payload=query, headers=headers, **kwargs)

    def post(self, url: str, data: dict, headers: dict = None, **kwargs) -> dict:
        """
        call execute_request for POST request
        :param data:
        :param url:
        :param headers:
        :return:
        """

        return self.execute_request(url=url, method="POST", payload=data, headers=headers, **kwargs)

    def put(self, url: str, data: dict, headers: dict = None, **kwargs) -> dict:
        """
        :param data:
        :param url:
        :param headers:
        :return:
        """
        return self.execute_request(url=url, method="PUT", payload=data, headers=headers, **kwargs)

    def patch(self, url: str, data: dict, headers: dict = None, **kwargs) -> dict:
        """
        :param data:
        :param url:
        :param headers:
        :return:
        """
        pass

    def delete(self, url: str, headers: dict = None, **kwargs) -> dict:
        """
        :param url:
        :param headers:
        :return:
        """
        return self.execute_request(url=url, method="DELETE", headers=headers, **kwargs)
