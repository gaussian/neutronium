import shutil
from gzip import GzipFile
from io import BytesIO
from typing import Optional

import boto3
from django.conf import settings


def upload_dir_to_s3(source_directory: str, s3_path: str, s3_bucket: str = None, archive: bool = True):
    import subprocess
    import shutil
    import os
    import re

    if not archive:
        raise NotImplementedError("Only collected/zipped directories supported for S3 upload")

    # Temp file to store archive (excluding extension)
    temp_filename_base = "/tmp/" + re.compile('[\W_]+').sub('', source_directory)
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


def upload_to_s3(s3_path: str, s3_bucket: str = None, meta: Optional[dict] = None, filename=None, content=None,
                 compress=False, verbose=False):
    """Some inspiration from https://gist.github.com/veselosky/9427faa38cee75cd8e27"""

    if not filename and not content:
        raise ValueError("Need filename or content defined to upload to S3")

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    extra_args = dict()
    if meta:
        extra_args['Metadata'] = meta
    if compress:
        extra_args['ContentEncoding'] = 'gzip'
    if not content or not isinstance(content, bytes):
        extra_args['ContentType'] = 'text/plain'
    extra_args = extra_args or None
    base_params = {
        'Bucket': s3_bucket or settings.S3_BUCKET_INTERNAL_FILES,
        'Key': s3_path,
    }
    upload_params = base_params.copy()
    upload_params['ExtraArgs'] = extra_args
    put_params = base_params.copy()
    put_params.update(**extra_args)

    # Filename was provided - open this file
    if filename:
        if compress:
            with open(filename, 'rb') as original_file_obj:
                compressed_file_obj = BytesIO()
                with GzipFile(fileobj=compressed_file_obj, mode='wb') as gz:
                    shutil.copyfileobj(original_file_obj, gz)
                response = s3.put_object(Body=compressed_file_obj.getvalue(), **put_params)
                compressed_file_obj.close()
        else:
            response = s3.upload_file(Filename=filename, **upload_params)

    # Actual content was provided, not the filename
    else:
        if compress:
            binary_content = content if isinstance(content, bytes) else content.encode('utf-8')
            compressed_file_obj = BytesIO()
            with GzipFile(fileobj=compressed_file_obj, mode='wb') as gz:
                gz.write(binary_content)
            response = s3.put_object(Body=compressed_file_obj.getvalue(), **put_params)
            compressed_file_obj.close()
        else:
            response = s3.put_object(Body=content, **put_params)

    if verbose:
        print(f"Uploaded to S3, response: {response}")
