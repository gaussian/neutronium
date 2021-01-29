import boto3


def get_ssm_parameters_by_path(path: str, recursive: bool = True, with_decryption: bool = True):
    # S3 client
    client = boto3.client("ssm")

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
