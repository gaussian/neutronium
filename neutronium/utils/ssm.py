from ec2_metadata import ec2_metadata


def get_ssm_parameters_by_path(path: str, recursive: bool = True, with_decryption: bool = True):
    import boto3

    # S3 client
    client = boto3.client(
        "ssm",
        region_name=ec2_metadata.region
    )

    # Get parameters from SSM
    parameters = client.get_parameters_by_path(
        Path=path,
        Recursive=recursive,
        WithDecryption=with_decryption
    ).get("Parameters")

    # Turn into dict
    parameters = {
        parameter.get("Name").replace(path, "").lstrip("/"): parameter.get("Value")
        for parameter in parameters
    }

    return parameters
