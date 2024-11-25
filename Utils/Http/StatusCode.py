HTTP_STATUS_CODES_CLASSIFICATION = {
    1: {
        "description": "informational response",
        "codes": {
            100: "Continue",
            101: "Switching Protocols",
            102: "Processing",
            103: "Early Hints",
        },
    },
    2: {
        "description": "success",
        "codes": {
            200: "OK",
            201: "Created",
            202: "Accepted",
            203: "Non-Authoritative Information",
            204: "No Content",
            205: "Reset Content",
            206: "Partial Content",
            207: "Multi-Status",
            208: "Already Reported",
            226: "IM Used",
        },
    },
    3: {
        "description": "redirection",
        "codes": {
            300: "Multiple Choices",
            301: "Moved Permanently",
            302: "Found",
            303: "See Other",
            304: "Not Modified",
            305: "Use Proxy",
            306: "Switch Proxy",
            307: "Temporary Redirect",
            308: "Permanent Redirect",
        },
    },
    4: {
        "description": "client errors",
        "codes": {
            400: "Bad Request",
            401: "Unauthorized",
            402: "Payment Required",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            406: "Not Acceptable",
            407: "Proxy Authentication Required",
            408: "Request Timeout",
            409: "Conflict",
            410: "Gone",
            411: "Length Required",
            412: "Precondition Failed",
            413: "Payload Too Large",
            414: "URI Too Long",
            415: "Unsupported Media Type",
            416: "Range Not Satisfiable",
            417: "Expectation Failed",
            418: "I'm a teapot",
            421: "Misdirected Request",
            422: "Unprocessable Entity",
            423: "Locked",
            424: "Failed Dependency",
            425: "Too Early",
            426: "Upgrade Required",
            428: "Precondition Required",
            429: "Too Many Requests",
            431: "Request Header Fields Too Large",
            451: "Unavailable For Legal Reasons",
        },
    },
    5: {
        "description": "server errors",
        "codes": {
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
            505: "HTTP Version Not Supported",
            506: "Variant Also Negotiates",
            507: "Insufficient Storage",
            508: "Loop Detected",
            510: "Not Extended",
            511: "Network Authentication Required",
        },
    },
}

# put your custom description here
HTTP_STATUS_CODES_CUSTOM_DESCRIPTION = {
    200: "The request was successfull.",
    201: "Resource created successfully.",
    204: "Resource updated successfully.",
    400: "A validation error ocurred.",
    401: "User not authenticated.",
    403: "The user does not have access rights to the content.",
    404: "No results found.",
    500: "",
}


HTTP_STATUS_CLASSES = {
    k: f"{k}xx" for k in HTTP_STATUS_CODES_CLASSIFICATION.keys()}

HTTP_STATUS_CODES = {
    key: value
    for _class in HTTP_STATUS_CODES_CLASSIFICATION.values()
    for key, value in _class["codes"].items()
}

HTTP_STATUS_CLASSES_DESCRIPTION = {
    k: v["description"] for k, v in HTTP_STATUS_CODES_CLASSIFICATION.items()
}

ERRORS_MSSG = {
    1: "status code most is a integer",
    2: "status code value not is know as status code",
    3: "status code most is a integer or string (eg: 200 or 2xx)",
}


class StatusCode:
    """
    A class to represent http code status with simplified operations

    Properties
        description : str
            description of status code
        Class : str
            status code class generalized with 'x's eg: 2xx
        _class : int
            status code class eg: 2

    Methods
        __json__(): for json dumps, combine whit extend JSONDecoder
        for more see docstring each function.

    Operations
        absolute value : abs()
            get valid status code integer
        add : +
            compare 2 SC or one SC with a int getting the most hihger
        append : +=
            compare 2 SC or one SC with a int setting the most hihger
        equal : ==
            compare 2 SC or one SC with a int or strclass (2xx)
        not equal : !=
            ...
        greater : >
        greater equals : >=
        littler : <
        littler equals : <=
    """

    __status_code: int = None

    def __init__(self, status_code: int):
        status_code = self.filter_code(status_code)
        self.__status_code = status_code

    def cast(self, value):
        return (
            abs(value)
            if type(value) is StatusCode
            else int(value) if str(value).isnumeric() else value
        )

    def filter_code(self, value):
        value = self.cast(value)
        assert type(value) is int, ERRORS_MSSG[1]
        assert value in HTTP_STATUS_CODES.keys(), ERRORS_MSSG[2]
        return value

    def filter_code_or_class(self, value):
        value = self.cast(value)
        assert type(value) in (int, str), ERRORS_MSSG[3]
        assert (
            value in HTTP_STATUS_CODES.keys() or
            value in HTTP_STATUS_CLASSES.values()
        ), ERRORS_MSSG[2]
        return value

    @property
    def value(self) -> int:
        return self.__status_code

    @property
    def _class(self) -> int:
        return self.__status_code // 100

    @property
    def Class(self) -> str:
        return f"{self.__status_code // 100}xx"

    @property
    def name(self) -> str:
        return (
            f"{self.__status_code} "
            f"{HTTP_STATUS_CODES[self.__status_code].upper()}"
        )

    @property
    def description(self) -> str:
        return HTTP_STATUS_CODES_CUSTOM_DESCRIPTION.get(
            self.__status_code, HTTP_STATUS_CODES[self.__status_code]
        )

    def __abs__(self) -> int:
        """eg: 200"""
        return self.__status_code

    def __add__(self, other) -> int:
        """eg: <StatusCode 200> + 404 -> <StatusCode 404>"""
        other = StatusCode(other)
        return (
            self.__status_code
            if self.__status_code >= other.__status_code
            else other.__status_code
        )

    def __iadd__(self, other):
        """eg: <StatusCode 200> += 404 update value <StatusCode 404>"""
        self.__status_code = self.__add__(other)
        return self

    def __bool__(self) -> bool:
        """eg: if <StatusCode 404>: False, if <StatusCode 201>: True"""
        return self._class == 2

    def __eq__(self, other) -> bool:
        """eg: <SC 404> == 404: True, <SC 404> == '2xx': False"""
        other = self.filter_code_or_class(other)
        return (
            self.Class == other if type(other) is
            str else self.__status_code == other
        )

    def __ne__(self, other) -> bool:
        """eg: <SC 404> != 404: False, <SC 404> != '2xx': True"""
        other = self.filter_code_or_class(other)
        return (
            self.Class != other if type(other) is
            str else self.__status_code != other
        )

    def __gt__(self, other) -> bool:
        """eg: <SC 404> > 404: False, <SC 404> > '2xx': True"""
        other = self.filter_code_or_class(other)
        return (
            self.Class > other if type(other) is
            str else self.__status_code > other
        )

    def __ge__(self, other) -> bool:
        """eg: <SC 404> >= 404: False, <SC 404> >= '2xx': True"""
        other = self.filter_code_or_class(other)
        return (
            self.Class >= other if type(other) is
            str else self.__status_code >= other
        )

    def __lt__(self, other) -> bool:
        """eg: <SC 404> < 404: False, <SC 404> < '2xx': True"""
        other = self.filter_code_or_class(other)
        return (
            self.Class < other if type(other) is
            str else self.__status_code < other
        )

    def __le__(self, other) -> bool:
        """eg: <SC 404> <= 404: False, <SC 404> <= '2xx': True"""
        other = self.filter_code_or_class(other)
        return (
            self.Class <= other if type(other) is
            str else self.__status_code <= other
        )

    def __str__(self) -> str:
        """eg: '404'"""
        return f"{self.__status_code}"

    def __int__(self) -> int:
        """eg: 404"""
        return self.__status_code

    def __repr__(self):
        """eg: <StatusCode 404>: Not Found"""
        return f"<StatusCode {self.__status_code}>: " f"{self.description}"

    def __json__(self, **options) -> int:
        """eg: \"200\" """
        return self.__status_code
