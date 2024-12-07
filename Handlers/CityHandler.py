from Classes.City import City
from Utils.EventTools import authorized


@authorized
def city(event, context, conn):
    city_class = City(conn)

    methods = {"GET": city_class.get_cities}

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
