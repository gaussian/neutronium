import tarfile
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
    assert (
        s3.upload_to_s3(
            s3_path="a/b.txt", s3_bucket=BUCKET, content="hello", do_not_overwrite=False
        )
        is None
    )
    assert s3.download_from_s3("a/b.txt", BUCKET) == b"hello"


def test_download_missing_key_returns_none(s3_bucket):
    assert s3.download_from_s3("missing.txt", BUCKET) is None


def test_do_not_overwrite_detects_existing(s3_bucket):
    s3.upload_to_s3(
        s3_path="x.txt", s3_bucket=BUCKET, content="v1", do_not_overwrite=False
    )
    assert (
        s3.upload_to_s3(
            s3_path="x.txt", s3_bucket=BUCKET, content="v2", do_not_overwrite=True
        )
        == "exists"
    )


def test_clear_s3_dir_safe_deletes(s3_bucket):
    s3.upload_to_s3(
        s3_path="dir/1.txt", s3_bucket=BUCKET, content="a", do_not_overwrite=False
    )
    s3.upload_to_s3(
        s3_path="dir/2.txt", s3_bucket=BUCKET, content="b", do_not_overwrite=False
    )
    s3.clear_s3_dir_safe(BUCKET, "dir")
    assert s3.download_from_s3("dir/1.txt", BUCKET) is None


def test_upload_from_filename_uncompressed(s3_bucket, tmp_path):
    """`upload_file` is a managed transfer and returns None on success.

    Regression: the return value used to be treated as an API response, so this
    path raised `AttributeError` *after* the object had already been uploaded.
    """
    source = tmp_path / "payload.txt"
    source.write_bytes(b"hello from a file")

    assert (
        s3.upload_to_s3(
            s3_path="f/plain.txt",
            s3_bucket=BUCKET,
            filename=str(source),
            do_not_overwrite=False,
        )
        is None
    )
    assert s3.download_from_s3("f/plain.txt", BUCKET) == b"hello from a file"


def test_upload_from_filename_compressed(s3_bucket, tmp_path):
    source = tmp_path / "payload.txt"
    source.write_bytes(b"hello compressed")

    assert (
        s3.upload_to_s3(
            s3_path="f/gz.txt",
            s3_bucket=BUCKET,
            filename=str(source),
            compress=True,
            do_not_overwrite=False,
        )
        is None
    )
    assert (
        s3.download_from_s3("f/gz.txt", BUCKET, decompress=True, encoding="utf8")
        == "hello compressed"
    )


def test_upload_dir_to_s3_uploads_restorable_tarball(s3_bucket, tmp_path):
    """`upload_dir_to_s3` goes through the uncompressed filename path."""
    source_dir = tmp_path / "bundle"
    (source_dir / "nested").mkdir(parents=True)
    (source_dir / "nested" / "inner.txt").write_text("nested file")

    s3.upload_dir_to_s3(
        source_directory=str(source_dir),
        s3_path="f/bundle.tar.gz",
        s3_bucket=BUCKET,
    )

    downloaded = tmp_path / "bundle.tar.gz"
    downloaded.write_bytes(s3.download_from_s3("f/bundle.tar.gz", BUCKET))
    with tarfile.open(downloaded, "r:gz") as tar:
        member = next(n for n in tar.getnames() if n.endswith("nested/inner.txt"))
        assert tar.extractfile(member).read() == b"nested file"


def test_upload_dir_to_s3_rejects_uncollected_directories(tmp_path):
    with pytest.raises(NotImplementedError):
        s3.upload_dir_to_s3(
            source_directory=str(tmp_path),
            s3_path="f/nope",
            s3_bucket=BUCKET,
            archive=False,
        )
