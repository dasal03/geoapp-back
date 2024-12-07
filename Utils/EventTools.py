import os
import jwt
from Utils.Response import Response
from Utils.ExceptionsTools import CustomException, get_and_print_error
from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError
from DataBase.DataBase import DataBase


SECRET_KEY = os.getenv("SECRET_KEY")


def validate_token(event):
    """Validate token and return user_id."""
    token = event.get("headers", {}).get("Authorization")
    if not token:
        raise CustomException("Authorization token is required.", 401)

    try:
        token = token.split(" ")[1]
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token["user_id"]
    except IndexError:
        raise CustomException("Invalid Authorization header format.", 401)
    except jwt.ExpiredSignatureError:
        raise CustomException("Authorization token is expired.", 401)
    except jwt.InvalidTokenError:
        raise CustomException("Authorization token is invalid.", 401)


def handle_response(event, context, data):
    """Format and return response."""
    r = Response(event, data, context)
    return r.getResponse()


def authorized(func):
    """
    Used decorator for authorization in event handlers
    """

    def verify_authorization(event, context):
        conn = None
        try:
            conn = DataBase()

            # Set temporary permissions
            if func.__name__ in (
                "auth", "user", "gender", "document_type",
                "country", "state", "city", "address"
            ):
                data = func(event, context, conn)
                data["auth"] = True
                return handle_response(event, context, data)

            event["user_id"] = validate_token(event)

            data = func(event, context, conn)
            data["auth"] = True

        except CustomException as err:
            data = get_and_print_error(err, err.status_code, err.message)
        except AssertionError as err:
            data = get_and_print_error(err, 400, str(err))
        except (
            KeyError, ValueError, InvalidRequestError, AttributeError
        ) as err:
            data = get_and_print_error(err, 400, str(err))
        except TypeError as err:
            data = get_and_print_error(err, 500, str(err))
        except (SQLAlchemyError, Exception) as err:
            data = get_and_print_error(err, 500, str(err))

        return handle_response(event, context, data)

    return verify_authorization


def response_format(func):
    """
    Decorator used for formatting response
    :param func:
    :return:
    """

    def response(event, context):
        data = func(event, context)
        # Formatting response
        return Response(event, data).getResponse(log=False)

    return response


def api_execution(func):
    """
    Decorator used as a middleware for api gateway authorization
    :param func:
    :return:
    """

    def wrapper(event, context, *args):
        return func(event, context, *args)

    return wrapper
