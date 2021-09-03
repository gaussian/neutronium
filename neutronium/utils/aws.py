import os


def get_ec2_metadata():
    from ec2_metadata import ec2_metadata

    AWS_CONTAINER_CREDENTIALS_RELATIVE_URI = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI ", None)
    if AWS_CONTAINER_CREDENTIALS_RELATIVE_URI:
        ec2_metadata.SERVICE_URL = f"169.254.170.2{AWS_CONTAINER_CREDENTIALS_RELATIVE_URI}"
        ec2_metadata.DYNAMIC_URL = ec2_metadata.SERVICE_URL + "dynamic/"
        ec2_metadata.METADATA_URL = ec2_metadata.SERVICE_URL + "meta-data/"
        ec2_metadata.USERDATA_URL = ec2_metadata.SERVICE_URL + "user-data/"

    return ec2_metadata
