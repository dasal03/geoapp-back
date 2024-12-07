from Classes.State import State
from Utils.EventTools import authorized


@authorized
def state(event, context, conn):
    state_class = State(conn)

    methods = {"GET": state_class.get_states}

    method_to_be_executed = methods.get(event["httpMethod"])

    return method_to_be_executed(event)
