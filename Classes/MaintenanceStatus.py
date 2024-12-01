from typing import Any, Dict
from sqlalchemy import update, insert, select, and_
from Models.Equipment import EquipmentModel
from Models.MaintenanceStatus import MaintenanceStatusModel
from Models.MaintenanceStatusCab import MaintenanceStatusCabModel
from Models.MaintenanceStatusDet import MaintenanceStatusDetModel
from Models.ScheduledMaintenance import ScheduledMaintenanceModel
from Utils.Constants import (
    ACTIVE,
    INACTIVE,
    SUCCESS_STATUS,
    CREATED_STATUS,
    ERROR_STATUS,
    NO_DATA_STATUS
)
from Utils.ExceptionsTools import CustomException
from Utils.GeneralTools import get_input_data
from Utils.Response import _response
from Utils.Validations import Validations

# Constants
OPERATION_STATUS_ID = 1
MAINTENANCE_STATUS_ID = 2
SCHEDULED_STATUS_ID = 3


class MaintenanceStatus:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def get_maintenance_status(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get maintenance status data based on provided parameters.

        Args:
            event (Dict[str, Any]):
                The event data containing the
                maintenance status data to retrieve.

        Returns:
            Dict[str, Any]:
                Filtered maintenance status data.
        """
        request = get_input_data(event)
        conditions = {"active": ACTIVE, **request}
        equipment_id = request.get("equipment_id", 0)

        if equipment_id:
            conditions.append({"equipment_id": equipment_id})

        # Query statement
        stmt = (
            select(
                MaintenanceStatusCabModel,
                EquipmentModel.description,
                EquipmentModel.serial,
                EquipmentModel.model,
                ScheduledMaintenanceModel.scheduled_date,
            ).filter_by(**conditions)
            .join(
                MaintenanceStatusDetModel,
                MaintenanceStatusDetModel.maintenance_status_cab_id ==
                MaintenanceStatusCabModel.maintenance_status_cab_id,
            )
            .join(
                EquipmentModel,
                EquipmentModel.equipment_id ==
                MaintenanceStatusDetModel.equipment_id,
            )
            .join(
                MaintenanceStatusModel,
                MaintenanceStatusModel.maintenance_status_id ==
                MaintenanceStatusDetModel.maintenance_status_id,
            )
            .join(
                ScheduledMaintenanceModel,
                and_(
                    ScheduledMaintenanceModel.equipment_id ==
                    MaintenanceStatusDetModel.equipment_id,
                    MaintenanceStatusDetModel.maintenance_status_id ==
                    SCHEDULED_STATUS_ID,
                    ScheduledMaintenanceModel.active == ACTIVE,
                ), isouter=True,
            )
            .where(
                EquipmentModel.active == ACTIVE,
                MaintenanceStatusModel.active == ACTIVE,
            )
        )

        # Execute query
        maintenance_status = self.db.query(stmt)
        return (
            _response(maintenance_status.as_dict(), SUCCESS_STATUS)
            if maintenance_status
            else _response({}, NO_DATA_STATUS)
        )

    def change_maintenance_status(
        self, event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update maintenance status data in the database.

        Args:
            event (Dict[str, Any]):
                The event data containing the
                maintenance status data to update.

        Returns:
            Dict[str, Any]:
                A response indicating the success or failure
                of the update operation.
        """
        request = get_input_data(event)
        user_id = event.get("user_id", 0)
        equipment_id = request.get("equipment_id", 0)
        maintenance_status_id = request.get("maintenance_status_id")
        scheduled_date = request.get("scheduled_date", None)

        fields = {
            "equipment_id": int,
            "maintenance_status_id": int,
            "user_id": int
        }

        if maintenance_status_id == SCHEDULED_STATUS_ID:
            fields["scheduled_date"] = str

        self.validations.validate_data(request, fields)
        self._validate_records(equipment_id, maintenance_status_id)

        # Get current status
        current_status = self._current_maintenance_status(equipment_id)
        current_status = current_status.get("maintenance_status_id")

        if current_status:
            self._validate_state_transition(
                current_status, maintenance_status_id
            )

            # Handle scheduled status
            if maintenance_status_id == SCHEDULED_STATUS_ID:
                scheduled_maintenance = self._update_scheduled_maintenance(
                    equipment_id, scheduled_date
                )

                if not scheduled_maintenance:
                    raise CustomException(
                        "No se pudo crear la programación de mantenimiento."
                    )

            # Inactivate previous statuses
            self._inactivate_previous_status(equipment_id)

        # Insert new maintenance status
        maintenance_status_cab_id = self._insert_maintenance_status(
            equipment_id, maintenance_status_id, user_id
        )

        return (
            _response(
                {"maintenance_status_cab_id": maintenance_status_cab_id},
                CREATED_STATUS
            )
            if maintenance_status_cab_id
            else _response(
                "No se pudo crear el estado de mantenimiento.", ERROR_STATUS
            )
        )

    def _current_maintenance_status(
        self, equipment_id: int
    ) -> Dict[str, Any]:
        """
        Get current maintenance status for an equipment.

        Args:
            equipment_id (int): The ID of the equipment.

        Returns:
            Dict[str, Any]:
                The current maintenance status for the equipment.
        """
        return self.db.query(
            select(MaintenanceStatusCabModel.maintenance_status_id)
            .where(
                MaintenanceStatusCabModel.equipment_id == equipment_id,
                MaintenanceStatusCabModel.active == ACTIVE,
            )
        ).first().as_dict()

    def _validate_records(
        self, equipment_id: int, maintenance_status_id: int
    ) -> None:
        """
        Validate if equipment and maintenance status exist.

        Args:
            equipment_id (int): The ID of the equipment.
            maintenance_status_id (int): The ID of the maintenance status.

        Raises:
            CustomException:
            If the equipment or maintenance status is not found.
        """
        self.validations.records(
            conn=self.db,
            model=EquipmentModel,
            pk=equipment_id,
            error_class=CustomException(
                "No se encontró el equipo.", NO_DATA_STATUS
            ),
        )

        self.validations.records(
            conn=self.db,
            model=MaintenanceStatusModel,
            pk=maintenance_status_id,
            error_class=CustomException(
                "No se encontró el estado de mantenimiento.", NO_DATA_STATUS
            ),
        )

    def _validate_state_transition(
        self, current_status: int, new_status: int
    ) -> None:
        """
        Validate allowed state transitions.

        Args:
            current_status (int): The current maintenance status.
            new_status (int): The new maintenance status.

        Raises:
            CustomException: If the transition is not allowed.
        """
        valid_transitions = {
            OPERATION_STATUS_ID: [MAINTENANCE_STATUS_ID, SCHEDULED_STATUS_ID],
            MAINTENANCE_STATUS_ID: [OPERATION_STATUS_ID, SCHEDULED_STATUS_ID],
            SCHEDULED_STATUS_ID: [OPERATION_STATUS_ID, MAINTENANCE_STATUS_ID],
        }
        if new_status not in valid_transitions.get(current_status, []):
            raise CustomException("Transición de estado inválida.")

    def _update_scheduled_maintenance(
        self, equipment_id: int, scheduled_date: str
    ) -> int:
        """
        Update or deactivate scheduled maintenance based on the state.
        """
        # Check for existing schedule
        existing_schedule = self.db.query(
            select(ScheduledMaintenanceModel.scheduled_maintenance_id)
            .where(
                ScheduledMaintenanceModel.equipment_id == equipment_id,
                ScheduledMaintenanceModel.active == ACTIVE
            )
        ).first()

        if existing_schedule:
            # Deactivate the current schedule
            self.db.update(
                update(ScheduledMaintenanceModel)
                .where(
                    ScheduledMaintenanceModel.scheduled_maintenance_id ==
                    existing_schedule["scheduled_maintenance_id"],
                    ScheduledMaintenanceModel.active == ACTIVE,
                )
                .values(active=INACTIVE)
            )

        # Insert new schedule
        schedule_maintenance_id = self.db.add(
            insert(ScheduledMaintenanceModel)
            .values(
                equipment_id=equipment_id,
                scheduled_date=scheduled_date,
                active=ACTIVE,
            )
        )

        return schedule_maintenance_id

    def _inactivate_previous_status(self, equipment_id: int) -> None:
        """
        Inactivate the previous maintenance status record in both
        the cabecera and detalle tables.
        """
        current_cab = self.db.query(
            select(MaintenanceStatusCabModel.maintenance_status_cab_id)
            .where(
                MaintenanceStatusCabModel.equipment_id == equipment_id,
                MaintenanceStatusCabModel.active == ACTIVE,
            )
        ).first()

        if current_cab:
            cab_id = current_cab.maintenance_status_cab_id

            # Deactivate the current cab
            self.db.update(
                update(MaintenanceStatusCabModel)
                .where(
                    MaintenanceStatusCabModel.maintenance_status_cab_id ==
                    cab_id
                )
                .values(active=INACTIVE)
            )

            # Deactivate the related detalle records
            self.db.update(
                update(MaintenanceStatusDetModel)
                .where(
                    MaintenanceStatusDetModel.maintenance_status_cab_id ==
                    cab_id,
                    MaintenanceStatusDetModel.active == ACTIVE,
                )
                .values(active=INACTIVE)
            )

    def _insert_maintenance_status(
        self, equipment_id: int, maintenance_status_id: int, user_id: int
    ) -> int:
        """
        Insert a new maintenance status record.
        """
        # Create a new cabecera
        new_cab_id = self.db.add(
            insert(MaintenanceStatusCabModel)
            .values(
                equipment_id=equipment_id,
                maintenance_status_id=maintenance_status_id
            )
        )

        # Create a new detalle for the cabecera
        self.db.add(
            insert(MaintenanceStatusDetModel).values(
                maintenance_status_cab_id=new_cab_id,
                equipment_id=equipment_id,
                maintenance_status_id=maintenance_status_id,
                user_id=user_id
            )
        )

        # Handle scheduled state (3)
        if maintenance_status_id == SCHEDULED_STATUS_ID:
            self._update_scheduled_maintenance(
                equipment_id, scheduled_date=None
            )

        return new_cab_id
