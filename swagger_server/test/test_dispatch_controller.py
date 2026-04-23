# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.generic_response import GenericResponse  # noqa: E501
from swagger_server.models.request_dispatch import RequestDispatch  # noqa: E501
from swagger_server.models.response_error import ResponseError  # noqa: E501
from swagger_server.test import BaseTestCase


class TestDispatchController(BaseTestCase):
    """DispatchController integration test stubs"""

    def test_post_dispatch(self):
        """Test case for post_dispatch

        Guarda el despacho en la base de datos.
        """
        body = RequestDispatch()
        response = self.client.open(
            '/dispatch',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_dispatch(self):
        """Test case for update_dispatch

        Actualiza el despacho en la base de datos.
        """
        body = RequestDispatch()
        response = self.client.open(
            '/dispatch',
            method='PUT',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
