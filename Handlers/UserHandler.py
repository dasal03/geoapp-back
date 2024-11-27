from Classes.User import User
from Utils.EventTools import authorized


@authorized
def user(event, context, conn):
    user_class = User(conn)

    methods = {
        "GET": user_class.get_user_data,
        "POST": user_class.register_user,
        "PUT": user_class.update_user,
        "DELETE": user_class.delete_user
    }

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)


@authorized
def user_data_by_token(event, context, conn):
    user_class = User(conn)

    methods = {"GET": user_class.user_data_by_token}

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
