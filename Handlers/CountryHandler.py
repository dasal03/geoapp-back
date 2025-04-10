from Classes.Country import Country
from Utils.EventTools import authorized


@authorized
def country(event, context, conn):
    country_class = Country(conn)

    methods = {"GET": country_class.get_countries}

    method_to_be_executed = methods.get(event["httpMethod"])

    return method_to_be_executed(event)
