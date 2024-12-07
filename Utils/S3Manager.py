from base64 import decodebytes
from re import sub, match
from unicodedata import normalize
from Utils.GeneralTools import generate_hash_from_date, as_list
from Utils.Http.StatusCode import StatusCode
from Utils.TypingTools import APIResponseType, Union


class S3Manager:

    __client = None
    __resource = None

    @property
    def client(self):
        if not self.__client:
            from boto3 import client
            self.__client = client("s3")
        return self.__client

    @property
    def resource(self):
        if not self.__resource:
            from boto3 import resource
            self.__resource = resource("s3")
        return self.__resource

    def upload_base64_file(
        self, bucket: str, key_name: str, file: str, bucket_route: str = ''
    ) -> APIResponseType:
        """
        Upload and base64 file, validate and storage any file in s3.
        Args:
            bucket (str): bucket name to upload file.
            key_name (str): name of file.
            file (str): content of file codified in base64.
            bucket_route (str, optional): path for file. Defaults to ''.
        Returns:
            APIResponseType: A dictionary response data.
        """
        filename, extension = self.fixNameFile(key_name)
        tmp_route = f"/tmp/{filename}.{extension}"

        with open(tmp_route, "wb") as file_to_save:
            file_base64 = file.encode("utf-8")
            decoded_image_data = decodebytes(file_base64)
            file_to_save.write(decoded_image_data)

        new_filename = f"{filename}_{generate_hash_from_date()}{extension}"

        return {
            "statusCode": StatusCode(200),
            "data": {
                "hashed_filename": new_filename,
                "s3_route": f"{bucket_route}{new_filename}",
                "file_name": filename,
                "tmp_route": tmp_route,
            },
        }

    def upload_temp_file(
        self, bucket: str, key_name: str, tmp_route: str
    ) -> APIResponseType:
        """
        Upload and base64 file, validate and storage any file in s3.
        Args:
            bucket (str): bucket name to upload file.
            key_name (str): name of file.
            tmp_route (str): temporary route to upload file.
        Returns:
            APIResponseType: A dictionary response data.
        """

        return {
            "statusCode": StatusCode(200),
            "data": {"tmp_route": tmp_route}
        }

    def download_file(
        self,  bucket: str, key_name: str, decode: str = None
    ) -> APIResponseType:
        """
        Download a file from the s3 and keep in memory.
        Args:
            bucket (str): bucket name to upload file.
            key_name (str): name of file.
            decode (str, optional): Dedode format for the
                downloaded file. Defaults to None.
        Returns:
            APIResponseType: A dictionary response data.
        """
        info = {
            'Bucket': bucket,
            'Key': key_name
        }
        response = self.client.get_object(**info)
        payload = response["Body"].read()

        if decode:
            payload = payload.decode(decode)

        return {"statusCode": StatusCode(200), "data": payload}

    def presigned_download_file(
        self,  bucket: str, key_name: str
    ) -> APIResponseType:
        """
        Create a presigned url to Download file from s3 bucket.
        Args:
            bucket (str): bucket name to upload file.
            key_name (str): name of file.
        Returns:
            APIResponseType: A dictionary response data.
        """
        url = self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key_name,
            },
            ExpiresIn=300
        )

        return {"statusCode": StatusCode(200), "data": {"url": url}}

    def download_file_to_tmp(
        self, bucket: str, key_name: str, tmp_route: str = None
    ) -> APIResponseType:
        """
        Gets a file and stores it in a temporary route.
        Args:
            bucket (str): bucket name to upload file.
            key_name (str): name of file.
            tmp_route: (str, optional): The temp route for the
                download the file. Defaults to None.
        Returns:
            APIResponseType: A dictionary response data.
        """
        filename, extension = self.fixNameFile(key_name)

        if not tmp_route:
            tmp_route = (f"/tmp/{filename}_"
                         f"{generate_hash_from_date()}"
                         f".{extension}")

        with open(tmp_route, 'wb') as data:
            self.client.download_fileobj(
                Bucket=bucket,
                Key=key_name,
                Fileobj=data
            )

        return {"statusCode": StatusCode(200), "data": {"url": tmp_route}}

    def presigned_upload_file(
        self, bucket_name: str, object_name: str,
        fields: dict = None, conditions: dict = None, expiration: int = 300
    ) -> APIResponseType:
        """
        Generate a presigned URL S3 POST request to upload a file.
        The response data hasta the following keys:
            url: URL to post to
            fields: Dictionary of form fields and values to submit
        Args:
            bucket_name (str): bucket name to upload file.
            object_name (str): name of file.
            fields (dict, optional): Dictionary of prefilled form fields.
                Defaults to None.
            conditions (dict, optional): List of conditions to include in
                the policy. Defaults to None.
            expiration (int, optional): Time in seconds for the presigned
                URL to expire. Defaults to 300.
        Returns:
            APIResponseType: A dictionary response data.
        """
        # Generate a presigned S3 POST URL
        response = self.client.generate_presigned_post(
            bucket_name, object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration)

        return {"statusCode": StatusCode(200), "data": response}

    def upload_from_presigned_url(
        self, bucket: str, key_name: str, tmp_route: str, presigned: str
    ) -> APIResponseType:
        """
        Download a presigned url and upload the file result to company s3.
        Args:
            bucket (str): The bucket company.
            key_name (str): The file route in s3.
            tmp_route (str): The temp route to save the presigned file.
            presigned (str): The presigned url to get the file.
        Returns:
            APIResponseType: A dictionary response data.
        """
        from requests import get as request_get

        response = request_get(presigned)

        with open(tmp_route, "wb") as file_to_save:
            file_to_save.write(response.content)

        return self.upload_temp_file(bucket, key_name, tmp_route)

    def copy_between_buckets(
        self,
        bucket_source: str,
        bucket_target: str,
        filename: Union[str, list],  # Eg: `folder/file.ext`or `file.ext`
        new_filename: Union[str, list, None] = None,
    ) -> APIResponseType:
        """
        Copy one o more files between buckets.
        Args:
            bucket_source (str): Source bucket name.
            bucket_target (str): Target bucket name.
            filename (str | list): A list or name for the files.
        Returns:
            APIResponseType: conventional API response dict.
        """
        status_code: StatusCode = StatusCode(500)
        data: Union[str, list] = []

        new_filename = as_list(new_filename or filename)
        filename = as_list(filename)

        assert len(filename) == len(new_filename), (
            "filename and new_filename, should be same quantity.")

        for i in range(len(filename)):
            copy_source = {"Bucket": bucket_source, "Key": filename[i]}

            # print(f"COPY SOURCE ======== {copy_source}")

            bucket = self.resource.Bucket(bucket_target)
            bucket.copy(copy_source, new_filename[i])

            status_code = StatusCode(200)
            data.append(new_filename)

        data = data[0] if len(data) == 1 else data

        return {"statusCode": status_code, "data": data}

    def generate_temp_route(self,  name: str, ext: str) -> str:
        return f"/tmp/{name}.{ext}"

    def generate_hash_name(self, name: str, ext: str) -> str:
        return f"{name}_{generate_hash_from_date()}.{ext}"

    @classmethod
    def fixNameFile(cls, filename: str, maxlen: int = 40):
        """
        Set the file name to a safe format, returning a limited file name
        and prepared extension format.
        Args:
            filename (str): name of file to format.
            maxlen (int, optional): maximum file name size. Defaults to 40.
        Returns:
            Tuple: (name, extension)
        """
        extension = ""
        divname = filename.split(".")
        if len(divname) > 1:
            extension = f"{cls.slugify(divname.pop())}"

        name = cls.slugify("".join(divname))[:maxlen]

        return name, extension

    @classmethod
    def slugify(cls, value: str, allow_unicode: bool = False) -> str:
        """
        Taken from:
        - https://github.com/django/django/blob/master/django/utils/text.py
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or
        repeated dashes to single dashes. Remove characters that aren't
        alphanumerics, underscores, or hyphens. Convert to lowercase.
        Also strip leading and trailing whitespace, dashes, and underscores.
        Args:
            value (str): The string to slugify.
            allow_unicode (bool, optional): Check if allow unicode string.
                Defaults to False.
        Returns:
            str: A sluged string.
        """
        value = str(value)
        if allow_unicode:
            value = normalize("NFKC", value)
        else:
            value = normalize("NFKD", value).encode("ascii", "ignore").decode(
                "ascii")
        value = sub(r"[^\w\s-]", "", value.lower())
        return sub(r"[-\s]+", "-", value).strip("-_")

    @staticmethod
    def valBucketRoute(folder_route: str) -> str:
        """
        Validate folder name to the bucket
        Args:
            folder_route (str): folder name to validate.
        Raises:
            KeyError: Error if the folder route is invalid.
        Returns:
            str: string route with format.
        """
        if not match("^[a-zA-Z_-]+", folder_route):
            raise KeyError("Bucket route is not valid")

        return f"{folder_route}/"
