from Classes.Contact import Contact
from Utils.EventTools import authorized


@authorized
def contact(event, context, conn):
    contact_class = Contact(conn)

    methods = {"POST": contact_class.send_contact_msg}

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
