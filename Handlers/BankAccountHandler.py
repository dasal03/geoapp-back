from Classes.BankAccount import BankAccount
from Utils.EventTools import authorized


@authorized
def bank_account(event, context, conn):
    bank_account_class = BankAccount(conn)

    methods = {"GET": bank_account_class.get_bank_account}

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
