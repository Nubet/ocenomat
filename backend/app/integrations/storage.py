import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings


class StorageUnavailable(Exception):
    pass


class ObjectStorage:
    def __init__(self, settings: Settings):
        if not all(
            (
                settings.storage_endpoint,
                settings.storage_access_key,
                settings.storage_secret_key,
            )
        ):
            raise StorageUnavailable("Storage is not configured")
        self.bucket = settings.storage_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=str(settings.storage_endpoint).rstrip("/"),
            aws_access_key_id=settings.storage_access_key.get_secret_value(),
            aws_secret_access_key=settings.storage_secret_key.get_secret_value(),
            region_name="us-east-1",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                connect_timeout=3,
                read_timeout=10,
                retries={"total_max_attempts": 2, "mode": "standard"},
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def initialize_bucket(self) -> None:
        try:
            try:
                self.client.head_bucket(Bucket=self.bucket)
            except ClientError as error:
                if error.response["Error"]["Code"] not in ("404", "NoSuchBucket"):
                    raise
                self.client.create_bucket(Bucket=self.bucket, ACL="private")
            try:
                self.client.get_bucket_policy(Bucket=self.bucket)
            except ClientError as error:
                if error.response["Error"]["Code"] != "NoSuchBucketPolicy":
                    raise
            else:
                raise StorageUnavailable("Bucket policies are not supported")
            acl = self.client.get_bucket_acl(Bucket=self.bucket)
            # RustFS 1.0.6 omits the ID on its default canonical-owner grant.
            grants = acl["Grants"]
            if len(grants) != 1 or not (
                grants[0]["Permission"] == "FULL_CONTROL"
                and grants[0]["Grantee"].get("Type") == "CanonicalUser"
                and grants[0]["Grantee"].get("ID", acl["Owner"]["ID"])
                == acl["Owner"]["ID"]
            ):
                raise StorageUnavailable("Bucket must be private")
        except (BotoCoreError, ClientError):
            raise StorageUnavailable("Storage unavailable") from None

    def put(self, key: str, content: bytes, media_type: str) -> None:
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=media_type,
                ACL="private",
            )
        except (BotoCoreError, ClientError):
            raise StorageUnavailable("Storage unavailable") from None

    def get(self, key: str, size: int) -> bytes:
        try:
            result = self.client.get_object(Bucket=self.bucket, Key=key)
            with result["Body"] as body:
                if result["ContentLength"] != size:
                    raise StorageUnavailable("Stored file is inconsistent")
                content = body.read(size + 1)
            if len(content) != size:
                raise StorageUnavailable("Stored file is inconsistent")
            return content
        except (BotoCoreError, ClientError):
            raise StorageUnavailable("Storage unavailable") from None

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError):
            raise StorageUnavailable("Storage unavailable") from None

    def close(self) -> None:
        self.client.close()


if __name__ == "__main__":
    storage = ObjectStorage(Settings())
    try:
        storage.initialize_bucket()
    except StorageUnavailable:
        raise SystemExit(
            "Private storage initialization failed; check bucket configuration"
        ) from None
    finally:
        storage.close()
