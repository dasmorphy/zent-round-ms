import getpass
import json
import os
from uuid import uuid4

from loguru import logger
from sqlalchemy import JSON, and_, exists, func, select, case, true
from werkzeug.utils import secure_filename

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db import Base
from swagger_server.models.db.access_control_materials import AcessControlMaterials
from swagger_server.models.db.biomar_access_images import BiomarAccessImages
from swagger_server.models.db.biomar_entry_report import BiomarAccessControl
from swagger_server.models.db.biomar_materials_access import BiomarMaterialsAccess
from swagger_server.models.db.destiny_intern import DestinyIntern
from swagger_server.models.db.dispatch import Dispatch
from swagger_server.models.db.dispatch_images import DispatchImages
from swagger_server.models.db.dispatch_products import DispatchProducts
from swagger_server.models.db.dispatch_reception import DispatchReception
from swagger_server.models.db.dispatch_reception_detail import DispatchReceptionDetail
from swagger_server.models.db.dispatch_skus import DispatchSkus
from swagger_server.models.db.products_sku import ProductsSku
from swagger_server.models.db.vehicle_type import VehicleType
from swagger_server.models.db.area_visit import AreaVisit
from swagger_server.models.db.staff_charge import StaffCharge
from swagger_server.models.db.dispatch_status import DispatchStatus
from swagger_server.models.entry_control_data import EntryControlData
from swagger_server.models.reception_data import Receptiondata
from swagger_server.models.request_dispatch_dispatch_data import RequestDispatchDispatchData
from swagger_server.models.request_reception import RequestReception
from swagger_server.models.request_sku_data import RequestSkuData
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


    def update_dispatch(self, data: RequestDispatchDispatchData, id_disp: int, images, internal, external):
        saved_files = []
        
        with self.db.session_factory() as session:
            try:
                
                dispatch_exist = session.get(Dispatch, id_disp)

                if not dispatch_exist:
                    raise CustomAPIException("Despacho no encontrado", 404)
                
                update_fields = {
                    "vehicle_type_id": data.vehicle_type,
                    "destiny_id": data.destiny,
                    "driver": data.driver,
                    "observations": data.observations,
                    "weight": data.weight,
                    "truck_license": data.truck_license,
                    "status_id": data.status_id,
                }

                for field, value in update_fields.items():
                    if value is not None:
                        setattr(dispatch_exist, field, value)

                dispatch_exist.updated_by = data.user
                dispatch_exist.updated_at = func.now()
                
                session.add(dispatch_exist)

                # Guardar imágenes (máx 10)
                for file in (images or [])[:10]:
                    try:
                        result = self.save_image(file)
                        saved_files.append(result["url"])

                        image = DispatchImages(
                            dispatch_id=dispatch_exist.id_dispatch,
                            image_path=result["url"],
                            process="update_dispatch"
                        )

                        session.add(image)
                    except OSError as e:
                        if e.errno == 36:
                            raise CustomAPIException("Nombre de archivo demasiado largo", 400)
                        
                        logger.error('Error: {}', str(e), internal=internal, external=external)
                        raise CustomAPIException("Error al subir las imágenes", 500)

                session.commit()

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


    def saveDispatch(self, session, data: RequestDispatchDispatchData, internal, external):
        try:

            vehicle_exists = session.execute(
                select(
                    exists().where(
                        VehicleType.id_vehicle_type == data.vehicle_type
                    )
                )
            ).scalar()

            if not vehicle_exists:
                raise CustomAPIException("El tipo de vehículo no existe", 404)
            
            destiny_exists = session.execute(
                select(
                    exists().where(
                        DestinyIntern.id_destiny == data.destiny
                    )
                )
            ).scalar()

            if not destiny_exists:
                raise CustomAPIException("El destino no existe", 404)
            
            dispatch = Dispatch(
                order_number=data.order_number,
                vehicle_type_id=data.vehicle_type,
                destiny_id=data.destiny,
                driver=data.driver,
                observations=data.observations,
                weight=data.weight,
                truck_license=data.truck_license,
                created_by=data.user,
                updated_by=data.user,
                status_id=1
            )
            
            session.add(dispatch)
            session.flush()

            return dispatch

        except Exception as exception:
            logger.error('Error: {}', str(exception), internal=internal, external=external)
            if isinstance(exception, CustomAPIException):
                raise exception
            
            raise CustomAPIException("Error al guardar el despacho en la base de datos", 500)
        

    def saveSku(self, session, data, internal, external) -> DispatchSkus:
        try:
            dispatch_skus = DispatchSkus(
                created_by=data["user"],
                updated_by=data["user"],
                type_sku=data["type_sku"],
                dispatch_id=data["dispatch_id"]
            )
            
            session.add(dispatch_skus)
            session.flush()

            return dispatch_skus
            
        except Exception as exception:
            logger.error('Error: {}', str(exception), internal=internal, external=external)
            if isinstance(exception, CustomAPIException):
                raise exception
            
            raise CustomAPIException("Error al guardar el sku en la base de datos", 500)
        

    def saveProductSku(self, session, sku_id: int, data, internal, external):
        try:
            product_exists = session.execute(
                select(
                    exists().where(
                        DispatchProducts.id_product == data["id_product"]
                    )
                )
            ).scalar()

            if not product_exists:
                raise CustomAPIException("El producto no existe", 404)
            
            product_sku = ProductsSku(
                product_id=data["id_product"],
                quantity=data["quantity"],
                sku_id=sku_id
            )
            
            session.add(product_sku)

        except Exception as exception:
            logger.error('Error: {}', str(exception), internal=internal, external=external)
            if isinstance(exception, CustomAPIException):
                raise exception
            
            raise CustomAPIException("Error al guardar el producto sku en la base de datos", 500)


    def saveImages(self, session, data, internal, external):
        try:
            
            images = DispatchImages(

            )
            
            session.add(images)

        except Exception as exception:
            logger.error('Error: {}', str(exception), internal=internal, external=external)
            if isinstance(exception, CustomAPIException):
                raise exception
            
            raise CustomAPIException("Error al buscar en la base de datos", 500)
        
    def get_all_dispatch_products(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(DispatchProducts)
                )
                products = [
                    {
                        "id_product": c.id_product,
                        "name": c.name,
                        "price": c.price,
                        "stock": c.stock,
                        "presentation_type": c.presentation_type,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at,
                        "created_by": c.created_by,
                        "updated_by": c.updated_by,
                    }
                    for c in result.scalars().all()
                ]
                return products
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener los productos en la base de datos", 500)
            
    def get_vehicle_types(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(VehicleType)
                )
                vehicle_types = [
                    {
                        "id_vehicle_type": c.id_vehicle_type,
                        "name": c.name,
                        "created_at": c.created_at,
                        "updated_at": c.updated_at,
                        "created_by": c.created_by,
                        "updated_by": c.updated_by,
                    }
                    for c in result.scalars().all()
                ]
                return vehicle_types
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener los tipos de vehículos en la base de datos", 500)
            
    def get_status_dispatch(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(DispatchStatus)
                )
                status = [
                    {
                        "id_status": c.id_status,
                        "name": c.name,
                        "created_at": c.created_at
                    }
                    for c in result.scalars().all()
                ]
                return status
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener los estados de despacho en la base de datos", 500)
            
    def get_all_dispatch(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:

                images_subq = (
                    select(
                        DispatchImages.dispatch_id,
                        func.json_agg(
                            func.json_build_object(
                                "image_path", DispatchImages.image_path,
                                "process", DispatchImages.process
                            )
                        )
                        .filter(DispatchImages.image_path.isnot(None))
                        .label("images")
                    )
                    .group_by(DispatchImages.dispatch_id)
                    .subquery()
                )

                products_sku_subq = (
                    select(
                        ProductsSku.sku_id,
                        func.json_agg(
                            func.json_build_object(
                                "id_product", ProductsSku.product_id,
                                "id_product_sku", ProductsSku.id_product_sku,
                                "name", DispatchProducts.name,
                                "quantity", ProductsSku.quantity
                            )
                        ).label("products_sku")
                    )
                    .join(
                        DispatchProducts,
                        DispatchProducts.id_product == ProductsSku.product_id
                    )
                    .group_by(ProductsSku.sku_id)
                    .subquery()
                )

                skus_subq = (
                    select(
                        DispatchSkus.dispatch_id,
                        func.json_agg(
                            func.json_build_object(
                                "id_sku", DispatchSkus.id_sku,
                                "type_sku", DispatchSkus.type_sku,
                                "products", func.coalesce(products_sku_subq.c.products_sku, '[]')
                            )
                        ).label("skus")
                    )
                    .outerjoin(
                        products_sku_subq,
                        products_sku_subq.c.sku_id == DispatchSkus.id_sku
                    )
                    .group_by(DispatchSkus.dispatch_id)
                    .subquery()
                )

                reception_details_subq = (
                    select(
                        DispatchReceptionDetail.reception_id,
                        func.json_agg(
                            func.json_build_object(
                                "reception_id", DispatchReceptionDetail.reception_id,
                                "expected_quantity", DispatchReceptionDetail.expected_quantity,
                                "received_quantity", DispatchReceptionDetail.received_quantity,
                                "observations", DispatchReceptionDetail.observations,
                                "product_sku_id", DispatchReceptionDetail.product_sku_id,
                                "name_product_sku", DispatchProducts.name,
                                "created_at", DispatchReceptionDetail.created_at,
                            )
                        ).label("details")
                    )
                    .outerjoin(
                        DispatchProducts,
                        DispatchProducts.id_product == DispatchReceptionDetail.product_sku_id
                    )
                    .group_by(DispatchReceptionDetail.reception_id)
                    .subquery()
                )

                reception_subq = (
                    select(
                        DispatchReception.dispatch_id,
                        DispatchReception.id_reception,
                        DispatchReception.is_correct,
                        DispatchReception.observations,
                        DispatchReception.created_at,
                        func.coalesce(reception_details_subq.c.details, '[]').label("reception_detail")
                    )
                    .outerjoin(
                        reception_details_subq,
                        reception_details_subq.c.reception_id == DispatchReception.id_reception
                    )
                    .subquery()
                )

                stmt = (
                    select(
                        Dispatch,
                        DispatchStatus,
                        DestinyIntern.name.label("name_destiny"),
                        VehicleType.name.label("name_vehicle_type"),
                        func.coalesce(skus_subq.c.skus, '[]').label("skus"),
                        func.coalesce(images_subq.c.images, '[]').label("images"),
                        case(
                            (
                                reception_subq.c.id_reception.isnot(None),
                                func.json_build_object(
                                    "id_reception", reception_subq.c.id_reception,
                                    "is_correct", reception_subq.c.is_correct,
                                    "observations", reception_subq.c.observations,
                                    "created_at", reception_subq.c.created_at,
                                    "reception_detail", reception_subq.c.reception_detail
                                )
                            ),
                            else_=None
                        ).label("reception")
                    )
                    .join(
                        DestinyIntern,
                        DestinyIntern.id_destiny == Dispatch.destiny_id
                    )
                    .join(
                        DispatchStatus,
                        DispatchStatus.id_status == Dispatch.status_id
                    )
                    .join(
                        VehicleType,
                        VehicleType.id_vehicle_type == Dispatch.vehicle_type_id
                    )
                    .outerjoin(
                        images_subq,
                        images_subq.c.dispatch_id == Dispatch.id_dispatch
                    )
                    .outerjoin(
                        skus_subq,
                        skus_subq.c.dispatch_id == Dispatch.id_dispatch
                    )
                    .outerjoin(
                        reception_subq,
                        reception_subq.c.dispatch_id == Dispatch.id_dispatch
                    )
                )

                filters = []

                if filtersBase.get("user"):
                    filters.append(Dispatch.created_by == filtersBase.get("user"))

                if filtersBase.get("start_date"):
                    filters.append(Dispatch.created_at >= filtersBase.get("start_date"))

                if filtersBase.get("end_date"):
                    filters.append(Dispatch.created_at <= filtersBase.get("end_date"))

                if filters:
                    stmt = stmt.where(and_(*filters))
                
                stmt = stmt.order_by(Dispatch.created_at.desc())

                result = session.execute(stmt).all()
                return result

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener los despachos en la base de datos", 500)
            
    def post_reception(self, body: Receptiondata, images, internal, external) -> None:
        saved_files = []

        with self.db.session_factory() as session:
            try:
                dispatch_exists = session.get(Dispatch, body.dispatch_id)

                if not dispatch_exists:
                    raise CustomAPIException("Despacho no encontrado", 404)
                
                reception_data = DispatchReception(
                    dispatch_id=body.dispatch_id,
                    is_correct=body.is_correct,
                    observations=body.observations,
                    created_by=body.user
                )
                
                session.add(reception_data)
                session.flush()

                if not body.is_correct and body.reception_details:
                    for detail in body.reception_details:
                        product_sku_exists = session.execute(
                            select(
                                exists().where(
                                    ProductsSku.id_product_sku == detail["product_sku_id"]
                                )
                            )
                        ).scalar()

                        if not product_sku_exists:
                            raise CustomAPIException("Un producto no existe", 404)
                        
                        reception_detail = DispatchReceptionDetail(
                            reception_id=reception_data.id_reception,
                            expected_quantity=detail["expected_quantity"],
                            received_quantity=detail["received_quantity"],
                            product_sku_id=detail["product_sku_id"],
                            observations=detail["observations"]
                        )
                        session.add(reception_detail)

                elif not body.is_correct and not body.reception_details:
                    raise CustomAPIException("El comentario de un producto con discrepancia no puede ser vacío", 400)


                dispatch_status = session.execute(
                    select(DispatchStatus).where(
                        DispatchStatus.name == "Ingresado en bodega"
                    )
                ).scalar_one_or_none()

                if not dispatch_status:
                    raise CustomAPIException("Estado de ingresado en bodega no existe", 500)

                dispatch_exists.status_id = dispatch_status.id_status
                dispatch_exists.updated_by = body.user
                dispatch_exists.updated_at = func.now()

                session.add(dispatch_exists)

                for file in images[:10]:
                    result = self.save_image(file)
                    saved_files.append(result["url"])

                    image = DispatchImages(
                        dispatch_id=body.dispatch_id,
                        image_path=result["url"],
                        process="save_reception"
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
                
                raise CustomAPIException("Error al guardar la recepción en la base de datos", 500)
            
    def post_entry_control(self, body: EntryControlData, images, internal, external):
        saved_files = []

        with self.db.session_factory() as session:
            try:
                area_exists = session.get(AreaVisit, body.area_visit)

                if not area_exists:
                    raise CustomAPIException("Área de visita no encontrada", 404)
                
                staff_exists = session.get(StaffCharge, body.person_charge)

                if not staff_exists:
                    raise CustomAPIException("Personal a cargo no encontrado", 404)
                
                access_control = BiomarAccessControl(
                    dni=body.dni,
                    names_visit=body.names_visit,
                    reason_visit=body.reason_visit,
                    area_visit_id=body.area_visit,
                    staff_charge_id=body.person_charge,
                    observations_entry=body.observations,
                    created_by=body.user,
                    updated_by=body.user,
                    status="Pendiente Salida"
                )
                
                session.add(access_control)
                session.flush()

                for material in body.material_entry:
                    self.saveMaterialAccessControl(
                        session,
                        access_control.id_access_control,
                        material,
                        internal,
                        external
                    )

                for file in (images or [])[:10]:
                    try:
                        result = self.save_image(file)
                        saved_files.append(result["url"])

                        image = BiomarAccessImages(
                            access_control_id=access_control.id_access_control,
                            image_path=result["url"],
                            type_process="entry"
                        )

                        session.add(image)
                    except OSError as e:
                        if e.errno == 36:
                            raise CustomAPIException("Nombre de archivo demasiado largo", 400)
                        
                        logger.error('Error: {}', str(e), internal=internal, external=external)
                        raise CustomAPIException("Error al subir las imágenes", 500)

                session.commit()
            
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
                
                raise CustomAPIException("Error al guardar el ingreso en la base de datos", 500)

    def saveMaterialAccessControl(self, session, access_control_id: int, data, internal, external):
        try:
            material_exists = session.execute(
                select(
                    exists().where(
                        BiomarMaterialsAccess.id_material == data["id_material"]
                    )
                )
            ).scalar()

            if not material_exists:
                raise CustomAPIException("El material no existe", 404)
            
            material_control = AcessControlMaterials(
                access_control_id=access_control_id,
                quantity=data["quantity"],
                material_id=data["id_material"]
            )
            
            session.add(material_control)

        except Exception as exception:
            logger.error('Error: {}', str(exception), internal=internal, external=external)
            if isinstance(exception, CustomAPIException):
                raise exception
            
            raise CustomAPIException("Error al guardar el material del ingreso en la base de datos", 500)
            
    def save_image(self, file):
        folder = "/var/www/uploads/dispatches"
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
            "url": f"/uploads/dispatches/{filename}"
        }


    def get_materials(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(BiomarMaterialsAccess)
                )
                materials = [
                    {
                        "id_material": c.id_material,
                        "name": c.name,
                        "created_at": c.created_at
                    }
                    for c in result.scalars().all()
                ]
                return materials
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener los materiales en la base de datos", 500)
            
            
    def get_areas(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(AreaVisit)
                )
                areas = [
                    {
                        "id_area": c.id_area,
                        "name": c.name,
                        "created_at": c.created_at
                    }
                    for c in result.scalars().all()
                ]
                return areas
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener las áreas de despacho en la base de datos", 500)
            
            
    def get_staff_charge(self, internal, external):
        with self.db.session_factory() as session:
            try:
                result = session.execute(
                    select(StaffCharge)
                )
                staff = [
                    {
                        "id_staff": c.id_staff,
                        "name": c.name,
                        "created_at": c.created_at
                    }
                    for c in result.scalars().all()
                ]
                return staff
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener el personal a cargo de despacho en la base de datos", 500)
            
    def get_entry_access(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                images_subq = (
                    select(
                        BiomarAccessImages.access_control_id,
                        func.json_agg(
                            func.json_build_object(
                                "image_path", BiomarAccessImages.image_path,
                                "type_process", BiomarAccessImages.type_process
                            )
                        )
                        .filter(BiomarAccessImages.image_path.isnot(None))
                        .label("images")
                    )
                    .group_by(BiomarAccessImages.access_control_id)
                    .subquery()
                )

                materials_subq = (
                    select(
                        AcessControlMaterials.access_control_id,
                        func.json_agg(
                            func.json_build_object(
                                "id_material", AcessControlMaterials.material_id,
                                "name", BiomarMaterialsAccess.name,
                                "quantity", AcessControlMaterials.quantity
                            )
                        ).label("materials")
                    )
                    .join(
                        BiomarMaterialsAccess,
                        BiomarMaterialsAccess.id_material == AcessControlMaterials.material_id
                    )
                    .group_by(AcessControlMaterials.access_control_id)
                    .subquery()
                )

                stmt = (
                    select(
                        BiomarAccessControl,
                        AreaVisit,
                        StaffCharge,
                        func.coalesce(materials_subq.c.materials, '[]').label("materials"),
                        func.coalesce(images_subq.c.images, '[]').label("images")
                    )
                    .join(
                        AreaVisit,
                        AreaVisit.id_area == BiomarAccessControl.area_visit_id
                    )
                    .join(
                        StaffCharge,
                        StaffCharge.id_staff == BiomarAccessControl.staff_charge_id
                    )
                    .outerjoin(
                        images_subq,
                        images_subq.c.access_control_id == BiomarAccessControl.id_access_control
                    )
                    .outerjoin(
                        materials_subq,
                        materials_subq.c.access_control_id == BiomarAccessControl.id_access_control
                    )
                )

                filters = []

                if filtersBase.get("user"):
                    filters.append(BiomarAccessControl.created_by == filtersBase.get("user"))

                if filtersBase.get("start_date"):
                    filters.append(BiomarAccessControl.created_at >= filtersBase.get("start_date"))

                if filtersBase.get("end_date"):
                    filters.append(BiomarAccessControl.created_at <= filtersBase.get("end_date"))

                if filters:
                    stmt = stmt.where(and_(*filters))
                
                stmt = stmt.order_by(BiomarAccessControl.created_at.desc())

                result = session.execute(stmt).all()
                return result

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener los ingresos en la base de datos", 500)
            

    def update_entry_access(self, data, id_entry: int, images, internal, external):
        saved_files = []
        
        with self.db.session_factory() as session:
            try:
                
                entry_exist = session.get(BiomarAccessControl, id_entry)

                if not entry_exist:
                    raise CustomAPIException("Ingreso no encontrado", 404)
                
                update_fields = {
                    "observations_out": data.observations,
                    "status": "Finalizado"
                }

                for field, value in update_fields.items():
                    if value is not None:
                        setattr(entry_exist, field, value)

                entry_exist.updated_by = data.user
                entry_exist.updated_at = func.now()

                for file in (images or [])[:10]:
                    try:
                        result = self.save_image(file)
                        saved_files.append(result["url"])

                        image = BiomarAccessImages(
                            access_control_id=entry_exist.id_access_control,
                            image_path=result["url"],
                            type_process="out"
                        )

                        session.add(image)
                    except OSError as e:
                        if e.errno == 36:
                            raise CustomAPIException("Nombre de archivo demasiado largo", 400)
                        
                        logger.error('Error: {}', str(e), internal=internal, external=external)
                        raise CustomAPIException("Error al subir las imágenes", 500)
                
                session.add(entry_exist)
                session.commit()

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
                
                raise CustomAPIException("Error al actualizar el ingreso en la base de datos", 500)

            finally:
                session.close()

    def get_dispatch_count_by_status(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                join_condition = Dispatch.status_id == DispatchStatus.id_status

                if filtersBase.get("user"):
                    join_condition = and_(join_condition, Dispatch.created_by == filtersBase.get("user"))

                if filtersBase.get("start_date"):
                    join_condition = and_(join_condition, Dispatch.created_at >= filtersBase.get("start_date"))

                if filtersBase.get("end_date"):
                    join_condition = and_(join_condition, Dispatch.created_at <= filtersBase.get("end_date"))

                stmt = (
                    select(
                        DispatchStatus.id_status,
                        DispatchStatus.name,
                        func.count(Dispatch.id_dispatch).label("count")
                    )
                    .outerjoin(
                        Dispatch,
                        join_condition  # 🔥 aquí van los filtros
                    )
                    .group_by(DispatchStatus.id_status, DispatchStatus.name)
                    .order_by(DispatchStatus.id_status)
                )

                result = session.execute(stmt).all()

                dispatch_count_by_status = [
                    {
                        "id_status": row[0],
                        "status_name": row[1],
                        "count": row[2]
                    }
                    for row in result
                ]

                return dispatch_count_by_status
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener el resumen de despachos por status en la base de datos", 500)
            
    def get_dispatch_count_with_discrepancy(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:

                # 🔥 condición de discrepancia
                discrepancy_exists = exists().where(
                    and_(
                        DispatchReception.dispatch_id == Dispatch.id_dispatch,
                        DispatchReceptionDetail.reception_id == DispatchReception.id_reception
                    )
                )

                stmt = select(
                    func.count(Dispatch.id_dispatch)
                ).where(discrepancy_exists)

                # 🔥 filtros normales
                filters = []

                if filtersBase.get("user"):
                    filters.append(Dispatch.created_by == filtersBase.get("user"))

                if filtersBase.get("start_date"):
                    filters.append(Dispatch.created_at >= filtersBase.get("start_date"))

                if filtersBase.get("end_date"):
                    filters.append(Dispatch.created_at <= filtersBase.get("end_date"))

                if filters:
                    stmt = stmt.where(and_(*filters))

                result = session.execute(stmt).scalar()

                return {
                    "count_discrepancy": result or 0
                }

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener despachos con discrepancia", 500)
            

    def get_count_entry_status(self, filtersBase, internal, external):
        with self.db.session_factory() as session:
            try:
                filters = true()

                if filtersBase.get("user"):
                    filters = and_(filters, BiomarAccessControl.created_by == filtersBase.get("user"))

                if filtersBase.get("start_date"):
                    filters = and_(filters, BiomarAccessControl.created_at >= filtersBase.get("start_date"))

                if filtersBase.get("end_date"):
                    filters = and_(filters, BiomarAccessControl.created_at <= filtersBase.get("end_date"))

                stmt = (
                    select(
                        BiomarAccessControl.status,
                        func.count().label("count")
                    )
                    .where(filters)
                    .group_by(BiomarAccessControl.status)
                )

                result = session.execute(stmt).all()

                return [
                    {
                        "status_name": row.status,
                        "count": row.count
                    }
                    for row in result
                ]

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener el conteo de ingresos en la base de datos", 500)