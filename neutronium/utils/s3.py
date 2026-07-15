import shutil
from gzip import GzipFile
from io import BytesIO
from typing import Optional, List


def _s3_client(aws_access_key_id=None, aws_secret_access_key=None):
    import boto3
    return boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )


def _s3_resource(aws_access_key_id=None, aws_secret_access_key=None):
    import boto3
    return boto3.resource(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )


def upload_dir_to_s3(source_directory: str, s3_path: str, s3_bucket: str = None, archive: bool = True):
    import subprocess
    import shutil
    import os
    import re

    if not archive:
        raise NotImplementedError("Only collected/zipped directories supported for S3 upload")

    # Temp file to store archive (excluding extension)
    temp_filename_base = "/tmp/" + re.compile(r'[\W_]+').sub('', source_directory)
    temp_filename = temp_filename_base + ".tar.gz"

    # Archive the directory
    shutil.make_archive(
        base_name=temp_filename_base,
        format='gztar',
        root_dir=source_directory,
    )

    # Upload to S3
    upload_to_s3(
        filename=temp_filename,
        s3_path=s3_path,
        s3_bucket=s3_bucket,
        compress=False
    )

    # Clean up zip file
    if os.name == 'nt':
        subprocess.run(["del", "/f", temp_filename], shell=True)
    else:
        subprocess.run(["rm", "-f", temp_filename])


def upload_to_s3(s3_path: str,
                 s3_bucket: str,
                 meta: Optional[dict] = None,
                 filename=None,
                 content=None,
                 compress: bool = False,
                 verbose: bool = False,
                 do_not_overwrite: bool = True,
                 aws_access_key_id=None,
                 aws_secret_access_key=None,
                 ) -> Optional[str]:
    """Some inspiration from https://gist.github.com/veselosky/9427faa38cee75cd8e27"""

    # Validation
    if not filename and not content:
        raise ValueError(f"Need filename or content defined to upload to S3, requested path is {s3_path}")

    # S3 client
    s3 = _s3_client(aws_access_key_id, aws_secret_access_key)
    extra_args = dict()
    if meta:
        extra_args["Metadata"] = meta
    if compress:
        extra_args["ContentEncoding"] = "gzip"
    if not content or not isinstance(content, bytes):
        extra_args["ContentType"] = "text/plain"
    extra_args = extra_args or None
    base_params = {
        "Bucket": s3_bucket,
        "Key": s3_path,
    }
    upload_params = base_params.copy()
    upload_params["ExtraArgs"] = extra_args
    put_params = base_params.copy()
    put_params.update(extra_args)

    # If overwriting is not allowed, check for existence (performs HEAD request)
    if do_not_overwrite and _obj_exists(client=s3, **base_params):
        return "exists"

    # Filename was provided - open this file
    if filename:
        if compress:
            with open(filename, "rb") as original_file_obj:
                compressed_file_obj = BytesIO()
                with GzipFile(fileobj=compressed_file_obj, mode="wb") as gz:
                    shutil.copyfileobj(original_file_obj, gz)
                response = s3.put_object(Body=compressed_file_obj.getvalue(), **put_params)
                compressed_file_obj.close()
        else:
            response = s3.upload_file(Filename=filename, **upload_params)

    # Actual content was provided, not the filename
    else:
        if compress:
            binary_content = content if isinstance(content, bytes) else content.encode("utf-8")
            compressed_file_obj = BytesIO()
            with GzipFile(fileobj=compressed_file_obj, mode="wb") as gz:
                gz.write(binary_content)
            response = s3.put_object(Body=compressed_file_obj.getvalue(), **put_params)
            compressed_file_obj.close()
        else:
            response = s3.put_object(Body=content, **put_params)

    if verbose:
        print(f"Uploaded to S3, response: {response}")

    status_code = response.get("ResponseMetadata", dict()).get("HTTPStatusCode", 0)
    if 200 <= status_code <= 300:
        return None
    return str(status_code)


def download_from_s3(s3_path: str,
                     s3_bucket: str,
                     decompress: bool = False,
                     encoding: str = None,
                     aws_access_key_id=None,
                     aws_secret_access_key=None):
    # S3 client
    s3 = _s3_client(aws_access_key_id, aws_secret_access_key)

    # Download
    try:
        response = s3.get_object(
            Bucket=s3_bucket,
            Key=s3_path,
        )
        streaming_body = response.get("Body", None)
        body_bytes = streaming_body.read() if streaming_body else None

    # No object found at this location
    except s3.exceptions.NoSuchKey:
        return None

    # Decompress if needed
    if decompress and body_bytes:
        bytestream = BytesIO(body_bytes)
        body_bytes = GzipFile(None, "rb", fileobj=bytestream).read()

    # Decode if needed
    if encoding and body_bytes:
        body = body_bytes.decode(encoding)
    else:
        body = body_bytes

    return body


def clear_s3_dir_safe(s3_bucket: str, s3_dir: str, aws_access_key_id=None, aws_secret_access_key=None):
    delete_limit = 10

    # S3 resource
    s3 = _s3_resource(aws_access_key_id, aws_secret_access_key)

    # Bucket
    bucket = s3.Bucket(s3_bucket)

    # Count objects to make sure we are not trying to delete too many
    count = 0
    for _ in bucket.objects.filter(Prefix=f"{s3_dir}/"):
        count += 1
        if count >= delete_limit:
            raise ValueError(f"Too many objects to delete in {s3_bucket}/{s3_dir}, will not execute")

    # Delete all S3 objects in this "directory"
    count = 0
    for obj in bucket.objects.filter(Prefix=f"{s3_dir}/"):
        s3.Object(bucket.name, obj.key).delete()
        count += 1

    print(f"Deleted {count} objects in {s3_bucket}/{s3_dir}")


def _obj_exists(client, **kwargs):
    from botocore.exceptions import ClientError

    try:
        client.head_object(**kwargs)

    # No object found at this location (this exception probably doesn't get called)
    except client.exceptions.NoSuchKey:
        return False

    # No object found at this location (this exception definitely gets called)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise

    return True
