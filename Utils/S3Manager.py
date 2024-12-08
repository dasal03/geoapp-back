import os
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from base64 import decodebytes
from re import sub
from unicodedata import normalize
from Utils.GeneralTools import generate_hash_from_date, as_list
from Utils.Http.StatusCode import StatusCode
from Utils.TypingTools import APIResponseType, Union


class S3Manager:
    def __init__(self):
        try:
            config = Config(
                signature_version="s3v4",
                region_name="us-east-2",
            )
            self.s3 = boto3.resource(
                service_name="s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                config=config,
            )
            self.client = self.s3.meta.client
        except (BotoCoreError, ClientError) as e:
            raise ConnectionError(f"Failed to connect to AWS S3: {str(e)}")

    def upload_base64_file(
        self, bucket: str, key_name: str, file: str, bucket_route: str
    ) -> APIResponseType:
        try:
            filename, extension = self.fix_name_file(key_name)
            tmp_route = f"/tmp/{filename}.{extension}"

            with open(tmp_route, "wb") as file_to_save:
                decoded_data = decodebytes(file.encode("utf-8"))
                file_to_save.write(decoded_data)

            new_filename = f"{bucket_route}{filename}.{extension}"
            self.client.upload_file(tmp_route, bucket, new_filename)

            return {
                "statusCode": StatusCode(200),
                "data": {
                    "hashed_filename": new_filename,
                    "s3_route": f"{new_filename}",
                    "file_name": filename,
                    "tmp_route": tmp_route,
                },
            }
        except (BotoCoreError, ClientError, IOError) as e:
            return {
                "statusCode": StatusCode(500),
                "data": {"error": f"File upload failed: {str(e)}"},
            }

    def download_file(
        self, bucket: str, key_name: str, decode: str = None
    ) -> APIResponseType:
        try:
            response = self.client.get_object(Bucket=bucket, Key=key_name)
            payload = response["Body"].read()
            if decode:
                payload = payload.decode(decode)
            return {"statusCode": StatusCode(200), "data": payload}
        except (BotoCoreError, ClientError) as e:
            return {
                "statusCode": StatusCode(500),
                "data": {"error": f"Download failed: {str(e)}"},
            }

    def download_file_to_tmp(
        self, bucket: str, key_name: str, tmp_route: str = None
    ) -> APIResponseType:
        try:
            filename, extension = self.fix_name_file(key_name)
            if not tmp_route:
                tmp_route = (
                    f"/tmp/{filename}_{generate_hash_from_date()}.{extension}"
                )

            with open(tmp_route, "wb") as data:
                self.client.download_fileobj(
                    Bucket=bucket, Key=key_name, Fileobj=data
                )

            return {"statusCode": StatusCode(200), "data": {"url": tmp_route}}
        except (BotoCoreError, ClientError, IOError) as e:
            return {
                "statusCode": StatusCode(500),
                "data": {"error": f"Download to tmp failed: {str(e)}"},
            }

    def presigned_download_file(
        self, bucket: str, key_name: str
    ) -> APIResponseType:
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key_name},
                ExpiresIn=300,
            )
            return {"statusCode": StatusCode(200), "data": {"url": url}}
        except (BotoCoreError, ClientError) as e:
            return {
                "statusCode": StatusCode(500),
                "data": {
                    "error": f"Presigned URL generation failed: {str(e)}"
                },
            }

    def copy_between_buckets(
        self,
        bucket_source: str,
        bucket_target: str,
        filename: Union[str, list],
        new_filename: Union[str, list, None] = None,
    ) -> APIResponseType:
        try:
            data = []
            new_filename = as_list(new_filename or filename)
            filename = as_list(filename)

            assert len(filename) == len(
                new_filename
            ), "Source and target filenames must match in quantity."

            for i in range(len(filename)):
                copy_source = {"Bucket": bucket_source, "Key": filename[i]}
                self.s3.Bucket(bucket_target).copy(
                    copy_source, new_filename[i]
                )
                data.append(new_filename[i])

            return {
                "statusCode": StatusCode(200),
                "data": data if len(data) > 1 else data[0],
            }
        except (BotoCoreError, ClientError, AssertionError) as e:
            return {
                "statusCode": StatusCode(500),
                "data": {"error": f"Copy failed: {str(e)}"},
            }

    @classmethod
    def fix_name_file(cls, filename: str, maxlen: int = 40):
        extension = ""
        divname = filename.split(".")
        if len(divname) > 1:
            extension = f"{cls.slugify(divname.pop())}"
        name = cls.slugify("".join(divname))[:maxlen]
        return name, extension

    @classmethod
    def slugify(cls, value: str, allow_unicode: bool = False) -> str:
        value = str(value)
        if allow_unicode:
            value = normalize("NFKC", value)
        else:
            value = normalize(
                "NFKD", value
            ).encode("ascii", "ignore").decode("ascii")
        value = sub(r"[^\w\s-]", "", value.lower())
        return sub(r"[-\s]+", "-", value).strip("-_")
