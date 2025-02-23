from Classes.Management import Management
from Utils.EventTools import authorized


@authorized
def management(event, context, conn):
    management_class = Management(conn)

    methods = {
        "GET": management_class.get_managements,
        "POST": management_class.create_management,
        "PUT": management_class.update_management,
        "DELETE": management_class.delete_management
    }

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
