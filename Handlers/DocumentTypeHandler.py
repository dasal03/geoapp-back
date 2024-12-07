from Classes.DocumentType import DocumentType
from Utils.EventTools import authorized


@authorized
def document_type(event, context, conn):
    document_type_class = DocumentType(conn)

    methods = {"GET": document_type_class.get_document_types}

    method_to_be_executed = methods.get(event["httpMethod"])
    return method_to_be_executed(event)
