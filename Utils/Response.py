from json import dumps as json_dumps
from Utils.Http.StatusCode import StatusCode
from Utils.GeneralTools import get_input_data


class Response:
    """Class responsible for log and response data"""
    def __init__(self, event, data, context=None):
        """Constructor method"""
        self.statusCode = data.get("statusCode", 400)
        self.httpMethod = event.get("httpMethod", "")
        self.request = get_input_data(event)
        self.data = data.get("data", [])
        self.user_id = event.get("user_id", 0)
        self.exception = data.get("exception", None)
        self.qope = data.get("qope", None)
        self.function_name = context.function_name if context else ""

    def getResponse(self) -> dict:
        """
        Generate the json response structure for the api gateway.
        Args:
            log (bool, optional): Activate the log register. Defaults to True.
        Returns:
            dict: The dictionary response.
        """
        # get from Http.StatusCode constants module custom data
        stcd = StatusCode(self.statusCode)

        response = {
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                "Access-Control-Allow-Headers": (
                    "Origin, X-Requested-With, Content-Type, Accept"
                ),
            },
            "statusCode": str(self.statusCode),
            "body": json_dumps(
                {
                    "responseCode": int(stcd),
                    "responseReason": stcd.name,
                    "description": stcd.description,
                    "data": self.data,
                    **(
                        {"tracebackException": self.exception}
                        if self.exception else {}
                    ),
                    **({"qope": self.qope} if self.qope else {}),
                }
            ),
        }

        return response
