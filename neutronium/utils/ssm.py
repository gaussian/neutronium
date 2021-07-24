from ec2_metadata import ec2_metadata


def get_ssm_parameters_by_path(path: str,
                               recursive: bool = True,
                               with_decryption: bool = True,
                               limit: int = 20
                               ) -> dict:
    import boto3

    # S3 client
    client = boto3.client(
        "ssm",
        region_name=ec2_metadata.region
    )

    # Get parameters from SSM
    next_token = None
    parameters = []
    while len(parameters) < limit:
        next_token_kwargs = {"NextToken": next_token} if next_token else dict()
        response = client.get_parameters_by_path(
            Path=path,
            Recursive=recursive,
            WithDecryption=with_decryption,
            **next_token_kwargs
        )
        new_parameters = response.get("Parameters")
        if not new_parameters:
            raise ValueError("No parameters returned by AWS")
        parameters += new_parameters
        next_token = response.get("NextToken", None)
        if not next_token:
            break

    # Turn into dict
    parameters_dict = {
        parameter.get("Name").replace(path, "").lstrip("/"): parameter.get("Value")
        for parameter in parameters
    }

    return parameters_dict
