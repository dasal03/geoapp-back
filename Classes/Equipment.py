from typing import Any, Dict
from sqlalchemy import select, insert, update, and_
from Models.Equipment import EquipmentModel
from Models.Location import LocationModel
from Models.MaintenanceStatus import MaintenanceStatusModel
from Models.MaintenanceStatusCab import MaintenanceStatusCabModel
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    CREATED_STATUS,
    SUCCESS_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS,
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations


class Equipment:
    "Class to manage equipment."
    fields = {"description": str, "serial": str, "model": str}

    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def _validate_equipment_exists(self, equipment_id: int) -> None:
        """
        Ensure the equipment exists in the database.

        Args:
            equipment_id (int):
            The ID of the equipment to validate.

        Raises:
            CustomException:
            If the equipment is not found.
        """
        self.validations.records(
            conn=self.db,
            model=EquipmentModel,
            pk=equipment_id,
            error_class=CustomException(
                "No se encontró el equipo.", NO_DATA_STATUS
            ),
            as_dict=True,
        )

    def _check_serial_availability(self, serial: str) -> None:
        """
        Ensure the serial is available.

        Args:
            serial (str):
            The serial to check.

        Raises:
            CustomException:
            If the serial is already in use.
        """
        if self.db.query(
            select(EquipmentModel.serial)
            .filter_by(serial=serial, active=ACTIVE)
        ).first():
            raise CustomException(
                "El serial ya está en uso.", ERROR_STATUS
            )

    def get_equipment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get equipment data based on provided parameters.

        Args:
            event (Dict[str, Any]):
            The event data containing the equipment data to retrieve.

        Returns:
            Dict[str, Any]:
            Filtered equipment data.
        """
        conditions = {"active": ACTIVE}
        request = get_input_data(event)
        stmt = (
            select(EquipmentModel, LocationModel.zone_name.label("location"))
            .filter_by(**conditions)
            .join(
                LocationModel,
                LocationModel.location_id == EquipmentModel.location_id,
                isouter=True,
            )
            .order_by(EquipmentModel.equipment_id)
        )

        # Include maintenance info if requested
        if "all_info" in request:
            stmt = (
                stmt.join(
                    MaintenanceStatusCabModel,
                    and_(
                        EquipmentModel.equipment_id
                        == MaintenanceStatusCabModel.equipment_id,
                        MaintenanceStatusCabModel.active == ACTIVE,
                    ), isouter=True,
                )
                .join(
                    MaintenanceStatusModel,
                    and_(
                        MaintenanceStatusModel.maintenance_status_id
                        == MaintenanceStatusCabModel.maintenance_status_id,
                        MaintenanceStatusModel.active == ACTIVE,
                    ), isouter=True,
                )
                .add_columns(
                    MaintenanceStatusModel.maintenance_status_id,
                    MaintenanceStatusModel.description.label(
                        "maintenance_status"
                    ),
                )
            )

        equipments = self.db.query(stmt)
        return (
            _response(SUCCESS_STATUS, equipments.as_dict())
            if equipments
            else _response(NO_DATA_STATUS, "No se encontraron equipos.")
        )

    def create_equipment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new equipment.

        Args:
            event (Dict[str, Any]):
            The event data containing the equipment data to create.

        Returns:
            Dict[str, Any]:
            Created equipment data.
        """
        request = get_input_data(event)
        serial = request.get("serial", "")
        image = request.get("image", None)

        if image:
            self.fields["image"] = str

        self._check_serial_availability(serial)
        self._validate_equipment_data(request, self.fields)

        stmt = insert(EquipmentModel).values(request.get(**self.fields))
        equipment_id = self.db.add(stmt)
        return (
            _response(CREATED_STATUS, {"equipment_id": equipment_id})
            if equipment_id
            else _response(ERROR_STATUS, "No se pudo crear el equipo.")
        )

    def update_equipment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing equipment.

        Args:
            event (Dict[str, Any]):
            The event data containing the equipment data to update.

        Returns:
            Dict[str, Any]:
            Updated equipment data.
        """
        request = get_input_data(event)
        equipment_id = request.pop("equipment_id", 0)
        image = request.pop("image", None)

        if not equipment_id:
            raise CustomException(
                "No se proporcionó el ID del equipo.", ERROR_STATUS
            )

        self._validate_equipment_exists(equipment_id)

        update_values = {
            key: value
            for key, value in request.items()
            if value is not None
        }

        if image:
            self.fields["image"] = str

        if not update_values:
            return _response(ERROR_STATUS, "No hay datos para actualizar.")

        self._validate_equipment_data(update_values, self.fields)

        # Update equipment
        stmt = (
            update(EquipmentModel)
            .where(
                EquipmentModel.equipment_id == equipment_id,
                EquipmentModel.active == ACTIVE,
            )
            .values(**update_values)
        )
        updated = self.db.update(stmt)

        return (
            _response(SUCCESS_STATUS, {"updated": bool(updated)})
            if updated
            else _response(ERROR_STATUS, "Error al actualizar el equipo.")
        )

    def delete_equipment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete an existing equipment.

        Args:
            event (Dict[str, Any]):
            The event data containing the equipment data to delete.

        Returns:
            Dict[str, Any]:
            Deleted equipment data.
            """
        equipment_id = get_input_data(event).get("equipment_id", 0)
        self._validate_equipment_exists(equipment_id)

        stmt = (
            update(EquipmentModel)
            .where(
                EquipmentModel.equipment_id == equipment_id,
                EquipmentModel.active == ACTIVE,
            )
            .values(active=INACTIVE)
        )
        deleted = self.db.update(stmt)

        return (
            _response(SUCCESS_STATUS, {"deleted": bool(deleted)})
            if deleted
            else _response(ERROR_STATUS, "Error al eliminar el equipo.")
        )

    def _validate_equipment_data(
        self,
        request: Dict[str, Any],
        fields: Dict[str, type],
    ) -> None:
        """
        Validate user data based on provided fields and expected types.

        Args:
            request (dict): The user data to be validated.
            fields (Dict[str, type]): The expected types for each field.

        Raises:
            CustomException: If the validation fails.
        """
        for field, expected_type in fields.items():
            validate = self.validations.validate([
                self.validations.param(
                    field, expected_type, request.get(field, "")
                )], cast=True,
            )

            if not validate["isValid"]:
                raise CustomException(validate["data"])
