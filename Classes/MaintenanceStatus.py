from sqlalchemy import update, insert, select, and_
from Models.Equipment import EquipmentModel
from Models.MaintenanceStatus import MaintenanceStatusModel
from Models.MaintenanceStatusCab import MaintenanceStatusCabModel
from Models.MaintenanceStatusDet import MaintenanceStatusDetModel
from Models.ScheduledMaintenance import ScheduledMaintenanceModel
from Utils.Validations import Validations
from Utils.GeneralTools import get_input_data
from Utils.ExceptionsTools import CustomException

# Constants
SCHEDULED_STATUS_ID = 3


class MaintenanceStatus:
    def __init__(self, db):
        self.db = db
        self.validations = Validations(db)

    def get_maintenance_status(self, event):
        request = get_input_data(event)
        equipment_id = request.get("equipment_id", 0)

        # Build dynamic conditions
        conditions = [MaintenanceStatusCabModel.active == 1]
        if equipment_id:
            conditions.append(
                MaintenanceStatusCabModel.equipment_id == equipment_id
            )

        # Query statement
        stmt = (
            select(
                MaintenanceStatusCabModel,
                EquipmentModel.description,
                EquipmentModel.serial,
                EquipmentModel.model,
                ScheduledMaintenanceModel.scheduled_date,
            )
            .join(
                MaintenanceStatusDetModel,
                MaintenanceStatusDetModel.maintenance_status_cab_id
                == MaintenanceStatusCabModel.maintenance_status_cab_id,
            )
            .join(
                EquipmentModel,
                EquipmentModel.equipment_id ==
                MaintenanceStatusDetModel.equipment_id,
            )
            .join(
                MaintenanceStatusModel,
                MaintenanceStatusModel.maintenance_status_id
                == MaintenanceStatusDetModel.maintenance_status_id,
            )
            .join(
                ScheduledMaintenanceModel,
                and_(
                    ScheduledMaintenanceModel.equipment_id
                    == MaintenanceStatusDetModel.equipment_id,
                    MaintenanceStatusDetModel.maintenance_status_id
                    == SCHEDULED_STATUS_ID,
                    ScheduledMaintenanceModel.active == 1
                ),
                isouter=True,
            )
            .where(
                *conditions,
                EquipmentModel.active == 1,
                MaintenanceStatusModel.active == 1
            )
        )

        # Execute query
        maintenance_status = self.db.query(stmt).as_dict()

        return {
            "statusCode": 200 if maintenance_status else 404,
            "data": maintenance_status or {},
        }

    def change_maintenance_status(self, event):
        request = get_input_data(event)
        user_id = event.get("user_id", 0)
        equipment_id = request.get("equipment_id", 0)
        maintenance_status_id = request.get("maintenance_status_id", 0)
        scheduled_date = request.get("scheduled_date", None)

        # Validate existence of equipment and maintenance status
        self._validate_records(equipment_id, maintenance_status_id)

        # Validate input parameters
        self._validate_params(equipment_id, maintenance_status_id)

        if maintenance_status_id == SCHEDULED_STATUS_ID:
            self._update_scheduled_maintenance(equipment_id, scheduled_date)

        # Inactivate previous statuses and insert new status
        self._inactivate_previous_status(equipment_id)
        maintenance_status_cab_id = self._insert_maintenance_status(
            equipment_id, maintenance_status_id, user_id
        )

        return {
            "statusCode": 200,
            "data": {"maintenance_status_cab_id": maintenance_status_cab_id},
        }

    def _validate_records(self, equipment_id, maintenance_status_id):
        """Validate if equipment and maintenance status exist."""
        self.validations.records(
            conn=self.db,
            model=EquipmentModel,
            pk=equipment_id,
            error_class=CustomException("No se encontró el equipo.", 404),
        )
        self.validations.records(
            conn=self.db,
            model=MaintenanceStatusModel,
            pk=maintenance_status_id,
            error_class=CustomException(
                "No se encontró el estado de mantenimiento.", 404
            ),
        )

    def _validate_params(self, equipment_id, maintenance_status_id):
        """Validate input parameters."""
        validation_result = self.validations.validate(
            [
                self.validations.param("Equipo", int, equipment_id),
                self.validations.param(
                    "Estado de mantenimiento", int, maintenance_status_id
                ),
            ]
        )
        if not validation_result["isValid"]:
            raise CustomException(validation_result["data"])

    def _update_scheduled_maintenance(self, equipment_id, scheduled_date):
        """Update scheduled maintenance status."""
        self.db.update(
            update(ScheduledMaintenanceModel)
            .where(ScheduledMaintenanceModel.equipment_id == equipment_id)
            .values(active=0)
        )
        self.db.add(
            insert(ScheduledMaintenanceModel).values(
                equipment_id=equipment_id, scheduled_date=scheduled_date
            )
        )

    def _inactivate_previous_status(self, equipment_id):
        """Inactivate previous maintenance statuses."""
        maintenance_status_cab_id = self.db.query(
            select(
                MaintenanceStatusCabModel.maintenance_status_cab_id
            ).where(
                MaintenanceStatusCabModel.equipment_id == equipment_id,
                MaintenanceStatusCabModel.active == 1,
            )
        )
        if maintenance_status_cab_id:
            self.db.update(
                update(MaintenanceStatusDetModel)
                .where(
                    MaintenanceStatusDetModel.maintenance_status_cab_id ==
                    maintenance_status_cab_id,
                    MaintenanceStatusDetModel.active == 1,
                )
                .values(active=0)
            )

    def _insert_maintenance_status(
        self, equipment_id, maintenance_status_id, user_id
    ):
        """Insert new maintenance status."""
        maintenance_status_cab_id = self.db.add(
            insert(MaintenanceStatusCabModel).values(
                equipment_id=equipment_id,
                maintenance_status_id=maintenance_status_id
            )
        )
        self.db.add(
            insert(MaintenanceStatusDetModel).values(
                maintenance_status_cab_id=maintenance_status_cab_id,
                equipment_id=equipment_id,
                maintenance_status_id=maintenance_status_id,
                user_id=user_id,
            )
        )
        return maintenance_status_cab_id
