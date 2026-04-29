import getpass
import json
import os
from uuid import uuid4

from loguru import logger
from sqlalchemy import JSON, and_, exists, func, select, case, true
from werkzeug.utils import secure_filename

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db import Base
from swagger_server.models.db.round_images import RoundImages
from swagger_server.models.db.round_register import RoundRegister
from swagger_server.models.db.rounds import Rounds
from swagger_server.models.db.sector_pool import SectorPool
from swagger_server.models.request_round_register_data import RequestRoundRegisterData
from swagger_server.resources.databases.postgresql import PostgreSQLClient

class RoundRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")
        # self.redis_client = RedisClient()

    
    def post_round_register(self, data: RequestRoundRegisterData, images, internal, external):
        saved_files = []

        with self.db.session_factory() as session:
            try:
                round_exists = session.get(Rounds, data.round_id)

                if data.round_id and not round_exists:
                    raise CustomAPIException("La ronda no existe", 404)
                elif data.round_id and round_exists:
                    round_exists.status = "OK"
                    session.add(round_exists)
                
                round_register = RoundRegister(
                    round_id=data.round_id,
                    lat=data.lat,
                    long=data.long,
                    observations=data.observations,
                    out_round=data.out_round,
                    created_by=data.user
                )
                
                session.add(round_register)
                session.flush()

                # Guardar imágenes (máx 3)
                for file in images[:3]:
                    result = self.save_image(file)
                    saved_files.append(result["url"])

                    image = RoundImages(
                        round_id=round_register.id_round_register,
                        image_path=result["url"],
                    )

                    session.add(image)

                session.commit()

            except OSError as e:
                if e.errno == 36:
                    raise CustomAPIException("Nombre de archivo demasiado largo", 400)

            except Exception as exception:
                session.rollback()

                #limpia archivos guardados si falla DB
                for path in saved_files:
                    full_path = os.path.join("/var/www", path.lstrip("/"))
                    if os.path.exists(full_path):
                        os.remove(full_path)

                        
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()

    def save_image(self, file):
        folder = "/var/www/uploads/rounds"
        ALLOWED_EXTENSIONS = {"webp"}
        MAX_FILENAME_LEN = 255
        MAX_BASENAME_LEN = 50

        if not file or file.filename == "":
            raise ValueError("Archivo inválido")

        if not os.path.exists(folder):
            raise CustomAPIException(f"La carpeta root de imágenes no existe {getpass.getuser()} - {os.getuid()} - {os.geteuid()}", 404)
        

        if not os.access(folder, os.W_OK):
            raise CustomAPIException(f"No hay permisos de escritura en la carpeta de imágenes {getpass.getuser()} - {os.getuid()} - {os.geteuid()}", 400)
        
        # ext = file.filename.rsplit(".", 1)[-1].lower()

        # if ext not in ALLOWED_EXTENSIONS:
        #     raise ValueError("Formato no permitido. Solo se acepta WEBP.")

        original_name = secure_filename(file.filename)
        base_name = os.path.splitext(original_name)[0][:MAX_BASENAME_LEN]

        filename = f"{uuid4()}_{base_name}.webp"

        if len(filename.encode("utf-8")) > MAX_FILENAME_LEN:
            filename = f"{uuid4().hex}.webp"

        path = os.path.join(folder, filename)
        file.save(path)

        return {
            "url": f"/uploads/rounds/{filename}"
        }
    
    def get_sectors_pool(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(SectorPool)
                )
                sectors = [
                    {
                        "id_sector": c.id_sector,
                        "name": c.name,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at
                    }
                    for c in result.scalars().all()
                ]
                return sectors
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)