import io

import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber
from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.storage import ObjectStorage, StorageUnavailable


@pytest.fixture
def storage():
    value = ObjectStorage(
        Settings(
            storage_endpoint="http://localhost:9000",
            storage_access_key="test-only",
            storage_secret_key="test-only",
        )
    )
    try:
        with Stubber(value.client) as stub:
            yield value, stub
            stub.assert_no_pending_responses()
    finally:
        value.close()


def acl(grants=None):
    return {
        "Owner": {"ID": "owner"},
        "Grants": grants
        if grants is not None
        else [
            {
                "Grantee": {"Type": "CanonicalUser", "ID": "owner"},
                "Permission": "FULL_CONTROL",
            }
        ],
    }


@pytest.mark.parametrize("existing", [True, False])
def test_initialization_is_private_and_repeatable(storage, existing):
    value, stub = storage
    params = {"Bucket": value.bucket}
    if existing:
        stub.add_response("head_bucket", {}, params)
    else:
        stub.add_client_error(
            "head_bucket",
            service_error_code="404",
            http_status_code=404,
            expected_params=params,
        )
        stub.add_response("create_bucket", {}, {**params, "ACL": "private"})
    stub.add_client_error(
        "get_bucket_policy",
        service_error_code="NoSuchBucketPolicy",
        expected_params=params,
    )
    stub.add_response("get_bucket_acl", acl(), params)
    value.initialize_bucket()


def test_initialization_accepts_rustfs_default_owner_without_id(storage):
    value, stub = storage
    params = {"Bucket": value.bucket}
    stub.add_response("head_bucket", {}, params)
    stub.add_client_error(
        "get_bucket_policy",
        service_error_code="NoSuchBucketPolicy",
        expected_params=params,
    )
    stub.add_response(
        "get_bucket_acl",
        acl([{"Grantee": {"Type": "CanonicalUser"}, "Permission": "FULL_CONTROL"}]),
        params,
    )
    value.initialize_bucket()


def test_initialization_refuses_bucket_policy_instead_of_overwriting_it(storage):
    value, stub = storage
    params = {"Bucket": value.bucket}
    stub.add_response("head_bucket", {}, params)
    stub.add_response("get_bucket_policy", {"Policy": '{"Statement":[]}'}, params)
    with pytest.raises(StorageUnavailable):
        value.initialize_bucket()


@pytest.mark.parametrize(
    "grantee",
    [
        {"Type": "Group", "URI": "http://acs.amazonaws.com/groups/global/AllUsers"},
        {"Type": "CanonicalUser", "ID": "someone-else"},
    ],
)
def test_initialization_refuses_non_owner_acl(storage, grantee):
    value, stub = storage
    params = {"Bucket": value.bucket}
    stub.add_response("head_bucket", {}, params)
    stub.add_client_error(
        "get_bucket_policy",
        service_error_code="NoSuchBucketPolicy",
        expected_params=params,
    )
    stub.add_response(
        "get_bucket_acl",
        acl([{"Grantee": grantee, "Permission": "FULL_CONTROL"}]),
        params,
    )
    with pytest.raises(StorageUnavailable):
        value.initialize_bucket()


def test_initialization_does_not_create_bucket_on_permission_failure(storage):
    value, stub = storage
    stub.add_client_error(
        "head_bucket",
        service_error_code="AccessDenied",
        http_status_code=403,
        expected_params={"Bucket": value.bucket},
    )
    with pytest.raises(StorageUnavailable):
        value.initialize_bucket()


@pytest.mark.parametrize("method", ["put", "get", "delete"])
def test_s3_failures_are_redacted(storage, method):
    value, stub = storage
    operation = {"put": "put_object", "get": "get_object", "delete": "delete_object"}[
        method
    ]
    stub.add_client_error(
        operation,
        service_error_code="AccessDenied",
        service_message="private service details",
    )
    with pytest.raises(StorageUnavailable) as error:
        if method == "put":
            value.put("opaque-key", b"x", "application/pdf")
        elif method == "get":
            value.get("opaque-key", 1)
        else:
            value.delete("opaque-key")
    assert "private" not in str(error.value)


@pytest.mark.parametrize("actual_size,expected_size", [(1, 1), (2, 1)])
def test_download_is_bounded_and_always_closes_body(
    storage, actual_size, expected_size
):
    value, stub = storage
    stream = io.BytesIO(b"x" * actual_size)
    stub.add_response(
        "get_object",
        {"Body": StreamingBody(stream, actual_size), "ContentLength": actual_size},
        {"Bucket": value.bucket, "Key": "opaque-key"},
    )
    if actual_size == expected_size:
        assert value.get("opaque-key", expected_size) == b"x"
    else:
        with pytest.raises(StorageUnavailable):
            value.get("opaque-key", expected_size)
    assert stream.closed


def test_missing_storage_configuration_is_not_usable():
    with pytest.raises(StorageUnavailable):
        ObjectStorage(Settings())


@pytest.mark.parametrize(
    "endpoint",
    ["http://user:secret@host", "http://host/path", "http://host?key=secret"],
)
def test_storage_endpoint_rejects_credentials_and_paths(endpoint):
    with pytest.raises(ValidationError):
        Settings(storage_endpoint=endpoint)


@pytest.mark.parametrize(
    "bucket", ["x", "../bucket", "UpperCase", "bucket.name", "x" * 64]
)
def test_bucket_name_is_restricted(bucket):
    with pytest.raises(ValidationError):
        Settings(storage_bucket=bucket)
