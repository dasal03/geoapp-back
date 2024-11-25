from sqlalchemy import select, insert, update, and_
from Models.Equipment import EquipmentModel
from Models.Location import LocationModel
from Models.MaintenanceStatus import MaintenanceStatusModel
from Models.MaintenanceStatusDet import MaintenanceStatusDetModel
from Models.MaintenanceStatusCab import MaintenanceStatusCabModel
from Utils.Validations import Validations
from Utils.GeneralTools import get_input_data
from Utils.ExceptionsTools import CustomException


class Equipment:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def _response(self, status_code: int, data: dict = None) -> dict:
        """Helper to format HTTP responses."""
        return {"statusCode": status_code, "data": data or {}}

    def _validate_equipment_existence(self, equipment_id: int):
        """Ensure the equipment exists in the database."""
        self.validations.records(
            conn=self.db,
            model=EquipmentModel,
            pk=equipment_id,
            error_class=CustomException("No se encontró el equipo.", 404),
            as_dict=True,
        )

    def get_equipment(self, event: dict) -> dict:
        request = get_input_data(event)
        conditions = {"active": 1}
        all_info = request.get("all_info", False)

        # Add filters dynamically
        conditions.update(
            {
                key: value
                for key, value in request.items()
                if key not in ("all", "all_info")
            }
        )

        stmt = (
            select(
                EquipmentModel,
                LocationModel.zone_name.label("location")
            )
            .filter_by(**conditions)
            .join(
                LocationModel,
                LocationModel.location_id == EquipmentModel.location_id,
                isouter=True,
            )
            .order_by(EquipmentModel.equipment_id)
        )

        if all_info:
            stmt = (
                stmt.join(
                    MaintenanceStatusCabModel,
                    and_(
                        EquipmentModel.equipment_id
                        == MaintenanceStatusCabModel.equipment_id,
                        MaintenanceStatusCabModel.active == 1,
                    ), isouter=True
                )
                .join(
                    MaintenanceStatusDetModel,
                    and_(
                        MaintenanceStatusCabModel.maintenance_status_cab_id ==
                        MaintenanceStatusDetModel.maintenance_status_cab_id,
                        MaintenanceStatusDetModel.active == 1,
                    ), isouter=True
                )
                .join(
                    MaintenanceStatusModel,
                    and_(
                        MaintenanceStatusModel.maintenance_status_id
                        == MaintenanceStatusDetModel.maintenance_status_id,
                        MaintenanceStatusModel.active == 1,
                    ), isouter=True
                )
                .add_columns(
                    MaintenanceStatusModel.maintenance_status_id,
                    MaintenanceStatusModel.description.label(
                        "maintenance_status"
                    )
                )
            )

        equipments = self.db.query(stmt).as_dict()

        return (
            self._response(200, equipments)
            if equipments else self._response(404)
        )

    def create_equipment(self, event: dict) -> dict:
        request = get_input_data(event)
        required_fields = ["description", "serial", "model"]

        # Validate input
        validate = self.validations.validate(
            [
                self.validations.param(
                    field.capitalize(), str, request.get(field, "")
                )
                for field in required_fields
            ],
            cast=True,
        )
        if not validate["isValid"]:
            raise CustomException(validate["data"])

        # Validate if equipment already exists
        # self._validate_serial_exists(request.get("serial", ""))

        # Create equipment
        equipment_id = self.db.add(
            insert(EquipmentModel).values(
                description=request.get("description", ""),
                location=request.get("location", ""),
                serial=request.get("serial", ""),
                model=request.get("model", ""),
                image=request.get("image", ""),
            )
        )

        return (
            self._response(201, {"equipment_id": equipment_id})
            if equipment_id
            else self._response(400)
        )

    def _validate_serial_exists(self, serial: str):
        """Ensure the equipment does not exist in the database."""
        self.validations.records(
            conn=self.db,
            model=EquipmentModel,
            pk=serial,
            error_class=CustomException(
                "Ya existe un equipo con ese serial.", 400),
            as_dict=True,
        )

    def update_equipment(self, event: dict) -> dict:
        request = get_input_data(event)
        equipment_id = request.get("equipment_id", 0)
        request.pop("maintenance_status_id")
        request.pop("maintenance_status")

        # Validate equipment existence
        self._validate_equipment_existence(equipment_id)

        # Validate input
        validate = self.validations.validate(
            [
                self.validations.param(
                    "Descripción", str, request.get("description", "")
                ),
                self.validations.param(
                    "Serial", str, request.get("serial", "")),
                self.validations.param(
                    "Modelo", str, request.get("model", "")),
            ], cast=True,
        )
        if not validate["isValid"]:
            raise CustomException(validate["data"])

        # Update equipment
        self.db.update(
            update(EquipmentModel)
            .where(EquipmentModel.equipment_id == equipment_id)
            .values(**request)
        )

        return self._response(200)

    def delete_equipment(self, event: dict) -> dict:
        request = get_input_data(event)
        equipment_id = request.get("equipment_id", 0)

        # Validate equipment existence
        self._validate_equipment_existence(equipment_id)

        # Soft delete equipment
        self.db.update(
            update(EquipmentModel)
            .where(EquipmentModel.equipment_id == equipment_id)
            .values(active=0)
        )

        return self._response(200)
