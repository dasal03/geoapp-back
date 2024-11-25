from xlsxwriter import Workbook
from typing import Any, Union, List, Dict, Optional
from typing_extensions import TypedDict
from io import BytesIO
from Utils.Functions import valBucketRoute, generate_hash_from_date
from boto3 import client as boto3_client

# Typing customs definitions
ExcelManagerFile = Union[str, bytes, None]
ExcelManagerRow = List[Any]
ExcelManagerColumn = Union[str, Any]


class ExcelManagerSheetData(TypedDict):
    column_names: Optional[List[ExcelManagerColumn]]
    data: Union[Dict[str, Any], List[ExcelManagerRow]]


ExcelManagerData = Dict[str, ExcelManagerSheetData]


class ExcelManagerResponse(TypedDict):
    success: bool
    file_route: ExcelManagerFile
    message: str


class ExcelManager:
    """
    Class to ease excel generation
    """

    DEFAULT_FILE_EXT = ".xlsx"
    DEFAULT_S3_BUCKET = ""

    def __init__(self, filename: str = "", **extra: Any):
        """
        Args:
            filename: The filename (excluding extension)
            extra: The possible args are:
                - str: file_route: The specified route where the file while be
                created (before uploaded in S3 if required)
                - bool: in_memory: Defines a temporary file should be
                created
                - str: s3_route: The bucket route where the file will be stored
                - str: bucket_name: The s3 bucket name
                - bool: same_data_length: If provided validates column_names
                and rows have the same ammount of columns

                Note: s3 parameters are optional. If no s3 parameters are
                provided, the file will be stored in file_route
        """
        # Encoding filename
        self.__filename = f"{filename}_{generate_hash_from_date()}"
        file_route: str = extra.get("file_route", "/tmp/")

        self.__in_memory_mode = extra.get("in_memory", False)
        self.__s3_route = extra.get("s3_route", None)
        self.__s3_client = None

        if self.__s3_route:  # Validating s3 route
            valBucketRoute(self.__s3_route)
            self.__bucket_name = extra.get("bucket_name", self.DEFAULT_S3_BUCKET)
            # Initializing s3 client
            self.__s3_client = boto3_client("s3")

        self.__full_route = file_route + self.__filename + self.DEFAULT_FILE_EXT

        # Selecting creation mode
        if self.__in_memory_mode:
            self.__binaries = BytesIO()
            self.__workbook = Workbook(
                self.__binaries,
                {"in_memory": True, "default_date_format": "yyyy-mm-dd hh:mm:ss"},
            )

        else:
            self.__workbook = Workbook(
                self.__full_route, {"default_date_format": "yyyy-mm-dd hh:mm:ss"}
            )

        # Title format
        self.title_format = self.__workbook.add_format(
            {
                "size": extra.get("title_size", 13),
                "align": extra.get("title_align", "center"),
                "bold": extra.get("title_bold", True),
                "border": extra.get("title_border", 1),
                "text_wrap": True,
            }
        )

        # Cell format
        self.cell_format = self.__workbook.add_format(
            {
                "size": extra.get("cell_size", 12),
                "align": extra.get("cell_align", "center"),
                "border": extra.get("cell_border", 1),
                "text_wrap": True,
            }
        )

        # Optional
        self.same_data_length = extra.get("same_data_length", True)

    def generate_regular_file(
        self, file_data: ExcelManagerData
    ) -> ExcelManagerResponse:
        """Generates a file with the provided data and returns the file route
        if success
        Args:
            file_data: A dictionary with the ExcelManagerData structure
            - e.g.:
                {
                    'Page1': {
                        'column_names': ['One', 'Two', 'Three'],
                        'data': [
                            [1, 2, 3]
                        ]
                    },
                    'Page2': {
                        'column_names': ['One', 'Two', 'Three'],
                        'data': [
                            [4, 5, 6]
                        ]
                    }, ...
                }
            - NOTE: 'column_names' parameter is optional if data is sent as a
            list of dictionaries. In that case, column names will be set as the
            dictionary keys of the first data element
        Returns:
            A dictionary with ExcelManagerResponse structure
        """
        success: bool = True
        message: str = "Ok"
        file_route: ExcelManagerFile = None

        try:
            with self.__workbook as workbook:
                # Retrieving data
                for sheet_name, content in file_data.items():
                    worksheet = workbook.add_worksheet(name=sheet_name)

                    data = content["data"]
                    column_names: list = content.get("column_names", None)

                    if not column_names:
                        column_names = list(data[0].keys())

                    self.validate_sheet_content(column_names, data)

                    column_width = self.get_columns_width(column_names, data)

                    title_column_number: int = 0
                    # Adding title row
                    for name in column_names:
                        worksheet.write(0, title_column_number, name, self.title_format)

                        worksheet.set_column(
                            title_column_number,
                            title_column_number,
                            column_width[title_column_number],
                        )

                        title_column_number += 1

                    data_row_number: int = 0
                    # Adding data rows
                    for row in data:

                        if type(row) is dict:
                            row = list(row.values())

                        data_row_number += 1
                        data_column_number: int = 0

                        for value in row:

                            # Validating row content
                            self.validate_sheet_row(column_names, row)

                            # Writing in cell
                            worksheet.write(
                                data_row_number,
                                data_column_number,
                                value,
                                self.cell_format,
                            )

                            data_column_number += 1

                    # Adding auto-filter
                    worksheet.autofilter(0, 0, len(data) - 1, len(column_names) - 1)

            if self.__in_memory_mode:  # Only if file is not required in memory
                file_route = self.__binaries.getvalue()  # Getting binaries
            else:
                file_route = self.__full_route

            if self.__s3_route:
                # Sending file to S3
                file_route = self.__upload_file_to_s3(file_route)

        except (AssertionError, Exception) as e:
            success = False
            message = str(e)

        return {"success": success, "file_route": file_route, "message": message}

    def validate_sheet_content(self, column_names: list, data: list) -> None:
        """Validates sheet content is formatted and built correctly
        Args:
            column_names:
            content:
        Returns:
            Void
        """
        if not len(column_names):
            raise AssertionError("'column_names' cannot be empty")

        if not len(data):
            raise AssertionError("'data' cannot be empty")

        return

    def validate_sheet_row(self, column_names: list, row: list) -> None:
        """Validates sheet row is formatted and built correctly
        Args:
            column_names:
            row:
        Returns:
            Void
        """
        if self.same_data_length and len(column_names) != len(row):
            raise Exception("Column names and data length must be the same")

    def __upload_file_to_s3(self, file: ExcelManagerFile) -> str:
        """Uploads the provided file into pre-defined s3
        Args:
            file: A bytes string or file
        Returns:
            The s3 bucket url to download the file
        """
        if not self.__in_memory_mode:
            file = open(file, "rb")

        key_name = f"{self.__s3_route}{self.__filename}{self.DEFAULT_FILE_EXT}"

        self.__s3_client.put_object(
            Body=file,
            Bucket=self.__bucket_name,
            Key=key_name,
        )

        # Generating download URL
        url = self.__s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.__bucket_name,
                "Key": key_name,
            },
            ExpiresIn=300,
        )

        return url

    @staticmethod
    def get_columns_width(column_names, data):
        """Gets the maximum columns' width
        Args:
            column_names:
            data:
        Returns:
            A list with the maximum columns' width
        """
        # Casting data to list of lists
        data = [(list(row.values()) if type(row) is dict else row) for row in data]

        offset: int = 5
        columns_width = [
            max(
                # The len for all row column values
                [len(str(row[col])) for row in data]
                # The len for the column name
                + [len(column_names[col])]
            )
            + offset
            for col in range(len(column_names))
        ]

        return columns_width
