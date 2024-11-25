from Utils.Http.StatusCode import StatusCode
from traceback import TracebackException
from os.path import basename as path_basename
from json import dumps as json_dumps


def get_arrow_resume_stack(list_tracebacks: list) -> str:
    """Internal method to simplify a list of exception traces in a resume.

    Args:
        list_tracebacks (List[dict]): List of dict of exception trace.

    Returns:
        str: resume of exception trace joined with arrows.
    """
    return [
        " -> ".join(
            [
                f"{path_basename(trace['filename'])}:{trace['lineno']}"
                for trace in err["error_lines"]
            ]
        )
        + f" in <{err['error_lines'][-1]['code']}>"
        for err in list_tracebacks
    ]


def list_traceback(exc_value: BaseException) -> list:
    """get response from error and status code and printing the traceback error

    Args:
        exc_value (Exception): Exception catched from try-except block

    Returns:
        List[Dict['type', 'message', 'error_lines': list]]:
        dict format except trace
    """

    result = list()

    # get previous fails, so errors are appended by order of execution
    if exc_value.__context__:
        result += list_traceback(exc_value.__context__)

    # convert Exception into TracebackException
    tbe = TracebackException.from_exception(exc_value)

    # get stacktrace (cascade methods calls)
    error_lines = list()
    for frame_summary in tbe.stack:
        summary_details = {
            "filename": frame_summary.filename,
            "method": frame_summary.name,
            "lineno": frame_summary.lineno,
            "code": frame_summary.line,
        }
        error_lines.append(summary_details)

    # append error, by order of execution
    result.append(
        {
            "type": tbe.exc_type.__name__,
            "message": str(tbe),
            "error_lines": error_lines
        }
    )
    return result


def get_and_print_error(
    exc_value: BaseException,
    status_code=500,
    data=None,
    bypass=None,
    **kwargs,
):
    """
    Get response from error and status code and printing the traceback error
    Args:
        exc_value (BaseException): Exception catched from try-except block.
        status_code (Union[int, StatusCode], optional): http status code.
            Defaults to 500.
        data (Any, optional): Use as aditional data for put in exception
            response. Defaults to None.
        **kwargs (Any=Any): Use as aditional data for put in exception response
    Returns:
        APIResponseType: dict format to response
    """
    result = list_traceback(exc_value)
    exception_trace = {
        "exception": {
            "trace": result,
            "resume": get_arrow_resume_stack(result),
            **kwargs,
        }
    }
    # PRINT exception trace
    print(json_dumps(exception_trace))

    return (
        bypass
        if bypass
        else {
            "statusCode": StatusCode(status_code),
            "data": data,
            **(exception_trace),
        }
    )


# CUSTOMS: exceptions
class CustomException(Exception):
    """
    Custom exception general for extend any other exceptions.
        Args:
            - message (str): message error.
                Mandatory.
            - status_code (StatusCode or int): status code.
                Defaults to 400.
    """

    def __init__(self, message: str, status_code: StatusCode = 400):
        self.message: str = message
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self):
        return self.message
