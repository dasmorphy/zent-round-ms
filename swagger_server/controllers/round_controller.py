import json
from timeit import default_timer
from flask import request

import connexion
from flask.views import MethodView
from loguru import logger

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.request_round_register_data import RequestRoundRegisterData
from swagger_server.repository.round_repository import RoundRepository
from swagger_server.uses_cases.round_use_case import RoundUseCase
from swagger_server.utils.transactions.transaction import generate_internal_transaction_id

class RoundView(MethodView):
    def __init__(self):
        self.logger = logger
        round_repository = RoundRepository()
        self.round_use_case = RoundUseCase(round_repository)


    def post_round_register(self):  # noqa: E501
        """Guarda el despacho en la base de datos.

        Guardado de despacho # noqa: E501

        :param body: 
        :type body: dict | bytes

        :rtype: GenericResponse
        """
        internal_process = (None, None)
        function_name = "post_round_register"
        response = {}
        status_code = 500
        try:
            if request.content_type.startswith("multipart/form-data"):
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())

                dispatch_file = request.files.get("dispatch_data")
                if not dispatch_file:
                    raise CustomAPIException("Campo dispatch_data no enviado", 400)

                dispatch_raw = dispatch_file.read().decode("utf-8")
                dispatch_dict = json.loads(dispatch_raw)
                dispatch_data = RequestRoundRegisterData.from_json(dispatch_dict)
                
                external_transaction_id = dispatch_dict['external_transaction_id']
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {dispatch_dict['channel']}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                files = request.files.getlist("images")
                self.round_use_case.post_dispatch(dispatch_data, files, internal_process)
                response["error_code"] = 0
                response["message"] = "Registro de ronda creado correctamente"
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=dispatch_dict['external_transaction_id'])
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_rounds_register(self):  # noqa: E501
        """Obtiene todos los despachos

        Devuelve todos los despachos de la base # noqa: E501

        :param external_transaction_id: 
        :type external_transaction_id: str
        :param channel: 
        :type channel: str

        :rtype: GenericResponse
        """
        internal_process = (None, None)
        function_name = "get_rounds_register"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                headers = {k.lower(): v for k, v in request.headers.items()}
                results = self.round_use_case.get_all_dispatch(headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Despachos obtenidos correctamente"
                response["data"] = results
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code
    
    def get_resume_graphs(self):
        internal_process = (None, None)
        function_name = "get_resume_graphs"
        response = {}
        status_code = 500
        try:
            if connexion.request.headers:
                start_time = default_timer()
                internal_transaction_id = str(generate_internal_transaction_id())
                external_transaction_id = request.headers.get('externalTransactionId')
                internal_process = (internal_transaction_id, external_transaction_id)
                response["internal_transaction_id"] = internal_transaction_id
                response["external_transaction_id"] = external_transaction_id
                message = f"start request: {function_name}, channel: {request.headers.get('channel')}"
                logger.info(message, internal=internal_transaction_id, external=external_transaction_id)
                headers = {k.lower(): v for k, v in request.headers.items()}
                result = self.round_use_case.get_resume_graphs(headers, request.args, internal_transaction_id, external_transaction_id)
                response["error_code"] = 0
                response["message"] = "Datos obtenidos correctamente"
                response["data"] = result
                end_time = default_timer()
                logger.info(f"Fin de la transacción, procesada en : {end_time - start_time} milisegundos",
                            internal=internal_transaction_id, external=external_transaction_id)
                status_code = 200
        except Exception as ex:
            response, status_code = CustomAPIException.check_exception(ex, function_name, internal_process)
            
        return response, status_code