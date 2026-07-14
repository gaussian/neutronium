from neutronium.utils.aws import get_instance_metadata


def get_ssm_parameters_by_path(
    path: str,
    recursive: bool = True,
    with_decryption: bool = True,
    limit: int = 20,
) -> dict:
    import boto3
    import os

    default_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    if default_region:
        region_name = default_region
    else:
        try:
            region_name = get_instance_metadata().region
        except Exception as e:
            region_name = None

    # S3 client
    client = boto3.client("ssm", region_name=region_name)

    # Get parameters from SSM
    next_token = None
    parameters = []
    try:
        while len(parameters) < limit:
            next_token_kwargs = {"NextToken": next_token} if next_token else dict()
            response = client.get_parameters_by_path(
                Path=path,
                Recursive=recursive,
                WithDecryption=with_decryption,
                **next_token_kwargs,
            )
            new_parameters = response.get("Parameters")
            if not new_parameters:
                raise ValueError("No parameters returned by AWS")
            parameters += new_parameters
            next_token = response.get("NextToken", None)
            if not next_token:
                break
    except Exception as e:
        return dict()

    # Turn into dict
    parameters_dict = {
        parameter.get("Name").replace(path, "").lstrip("/"): parameter.get("Value")
        for parameter in parameters
    }

    return parameters_dict
