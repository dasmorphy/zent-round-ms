from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.request_round_register_data import RequestRoundRegisterData
from swagger_server.repository.round_repository import RoundRepository


class RoundUseCase:

    def __init__(self, round_repository: RoundRepository):
        self.round_repository = round_repository

    def post_round_register(self, data: RequestRoundRegisterData, images, internal_process):
        if len(images) > 3:
            raise CustomAPIException("Máximo 3 imagenes", 500)
        
        internal, external = internal_process

        self.round_repository.post_round_register(data, images, internal, external)

    def get_sectors_pool(self, internal, external):
        return self.round_repository.get_sectors_pool(internal, external)