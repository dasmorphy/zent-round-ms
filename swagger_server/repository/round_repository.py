import getpass
import json
import os
from uuid import uuid4

from loguru import logger
from sqlalchemy import JSON, and_, exists, func, select, case, true
from werkzeug.utils import secure_filename

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db import Base
from swagger_server.resources.databases.postgresql import PostgreSQLClient

class RoundRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")
        # self.redis_client = RedisClient()

    
    def post_dispatch(self, data: RequestDispatchDispatchData, images, internal, external):
        saved_files = []

        with self.db.session_factory() as session:
            try:
                
                dispatch_saved = self.saveDispatch(session, data, internal, external)

                for sku in data.sku:
                    new_sku = {
                        "user": data.user,
                        "type_sku": sku["type_sku"],
                        "dispatch_id": dispatch_saved.id_dispatch
                    }
                    sku_saved = self.saveSku(session, new_sku, internal, external)
                    for product in sku["products"]:
                        self.saveProductSku(
                            session,
                            sku_saved.id_sku,
                            product,
                            internal,
                            external
                        )

                # Guardar imágenes (máx 10)
                for file in images[:10]:
                    result = self.save_image(file)
                    saved_files.append(result["url"])

                    image = DispatchImages(
                        dispatch_id=dispatch_saved.id_dispatch,
                        image_path=result["url"],
                        process="save_dispatch"
                    )

                    session.add(image)

                # self.saveImages(session, images, internal, external)
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