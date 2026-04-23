# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.generic_response import GenericResponse  # noqa: E501
from swagger_server.models.response_error import ResponseError  # noqa: E501
from swagger_server.test import BaseTestCase


class TestCatalogsController(BaseTestCase):
    """CatalogsController integration test stubs"""

    def test_get_status_dispatch(self):
        """Test case for get_status_dispatch

        Obtiene todos los estados de despacho
        """
        headers = [('external_transaction_id', 'external_transaction_id_example'),
                   ('channel', 'channel_example')]
        response = self.client.open(
            '/status-dispatch',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
