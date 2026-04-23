from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.repository.round_repository import RoundRepository


class RoundUseCase:

    def __init__(self, dispatch_repository: RoundRepository):
        self.dispatch_repository = dispatch_repository