from Classes.PaymentCard import PaymentCard
from Utils.EventTools import authorized


@authorized
def payment_card(event, context, conn):
    payment_card_class = PaymentCard(conn)

    methods = {
        "GET": payment_card_class.get_user_cards,
        "POST": payment_card_class.add_payment_card,
        "PUT": payment_card_class.update_payment_card,
        "DELETE": payment_card_class.delete_payment_card,
    }

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
