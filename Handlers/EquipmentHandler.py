from Classes.Equipment import Equipment
from Utils.EventTools import authorized


@authorized
def equipment(event, context, conn):
    equipment_class = Equipment(conn)

    methods = {
        "GET": equipment_class.get_equipment,
        "POST": equipment_class.create_equipment,
        "PUT": equipment_class.update_equipment,
        "DELETE": equipment_class.delete_equipment
    }

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
