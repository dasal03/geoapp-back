from Classes.MaintenanceStatus import MaintenanceStatus
from Utils.EventTools import authorized


@authorized
def maintenance_status(event, context, conn):

    maintenance_status_class = MaintenanceStatus(conn)

    methods = {
        "GET": maintenance_status_class.get_maintenance_status,
        "POST": maintenance_status_class.change_maintenance_status
    }

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
