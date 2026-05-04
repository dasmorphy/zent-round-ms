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
    
    def get_registered_rounds(self, headers, params, internal, external):
        filters = {
            "user": headers.get("user"),
            "start_date": params.get("start_date"),
            "end_date": params.get("end_date"),
        }

        rows = self.round_repository.get_registered_rounds(filters, internal, external)

        results = [
            {
                "id_round_register": c.id_round_register,
                "round_id": c.round_id,
                "out_round": c.out_round,
                "observations": c.observations,
                "created_by": c.created_by,
                "created_at": c.created_at,
                "lat": c.lat,
                "long": c.long,
                "sector_pool_id": c.sector_pool_id,
                "name_sector": name_sector,
                "pool": c.pool,
                "images": images or []
            }
            for c, name_sector, images in rows
        ]

        return results