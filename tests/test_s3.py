from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from neutronium.utils import s3

BUCKET = "test-bucket"


def test_s3_client_passes_optional_creds():
    with patch("boto3.client") as mock_client:
        s3._s3_client("KEY", "SECRET")
    mock_client.assert_called_once_with(
        "s3", aws_access_key_id="KEY", aws_secret_access_key="SECRET"
    )


@pytest.fixture
def s3_bucket(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        boto3.client("s3").create_bucket(Bucket=BUCKET)
        yield


def test_upload_and_download_roundtrip(s3_bucket):
    assert s3.upload_to_s3(
        s3_path="a/b.txt", s3_bucket=BUCKET, content="hello", do_not_overwrite=False
    ) is None
    assert s3.download_from_s3("a/b.txt", BUCKET) == b"hello"


def test_download_missing_key_returns_none(s3_bucket):
    assert s3.download_from_s3("missing.txt", BUCKET) is None


def test_do_not_overwrite_detects_existing(s3_bucket):
    s3.upload_to_s3(s3_path="x.txt", s3_bucket=BUCKET, content="v1", do_not_overwrite=False)
    assert s3.upload_to_s3(
        s3_path="x.txt", s3_bucket=BUCKET, content="v2", do_not_overwrite=True
    ) == "exists"


def test_clear_s3_dir_safe_deletes(s3_bucket):
    s3.upload_to_s3(s3_path="dir/1.txt", s3_bucket=BUCKET, content="a", do_not_overwrite=False)
    s3.upload_to_s3(s3_path="dir/2.txt", s3_bucket=BUCKET, content="b", do_not_overwrite=False)
    s3.clear_s3_dir_safe(BUCKET, "dir")
    assert s3.download_from_s3("dir/1.txt", BUCKET) is None
