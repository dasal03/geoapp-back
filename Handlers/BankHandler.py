from Classes.Bank import Bank
from Utils.EventTools import authorized


@authorized
def bank(event, context, conn):
    bank_class = Bank(conn)

    methods = {"GET": bank_class.get_banks}

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
