from Classes.Address import Address
from Utils.EventTools import authorized


@authorized
def address(event, context, conn):
    address_class = Address(conn)

    methods = {
        "GET": address_class.get_address,
        "POST": address_class.register_address,
        "PUT": address_class.update_address,
        "DELETE": address_class.delete_address
    }

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
