from Classes.Gender import Gender
from Utils.EventTools import authorized


@authorized
def gender(event, context, conn):
    gender_class = Gender(conn)

    methods = {"GET": gender_class.get_genders}

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
