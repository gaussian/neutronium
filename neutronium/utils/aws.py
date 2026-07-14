def get_instance_metadata():
    import os
    from dataclasses import dataclass

    @dataclass
    class InstanceMetadata:
        private_ipv4: str | None = None
        region: str | None = None

    env_region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

    ecs_metadata_uri = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
    if ecs_metadata_uri:
        try:
            import requests

            r = requests.get(f"{ecs_metadata_uri}/task", timeout=2)
            r.raise_for_status()
            task = r.json()

            private_ip = None
            for c in task.get("Containers", []):
                for n in c.get("Networks", []):
                    ipv4s = n.get("IPv4Addresses") or []
                    if ipv4s:
                        private_ip = ipv4s[0]
                        break
                if private_ip:
                    break

            region = env_region
            if not region:
                task_arn = task.get("TaskARN") or ""
                parts = task_arn.split(":")
                if len(parts) > 2:
                    region = parts[2]  # arn:aws:ecs:REGION:...

            return InstanceMetadata(private_ipv4=private_ip, region=region)
        except Exception:
            pass

    try:
        from ec2_metadata import ec2_metadata

        rel = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
        if rel:
            ec2_metadata.SERVICE_URL = f"169.254.170.2{rel}"
            ec2_metadata.DYNAMIC_URL = ec2_metadata.SERVICE_URL + "dynamic/"
            ec2_metadata.METADATA_URL = ec2_metadata.SERVICE_URL + "meta-data/"
            ec2_metadata.USERDATA_URL = ec2_metadata.SERVICE_URL + "user-data/"

        region = getattr(ec2_metadata, "region", None) or env_region
        return InstanceMetadata(
            private_ipv4=getattr(ec2_metadata, "private_ipv4", None),
            region=region,
        )
    except Exception:
        pass

    return InstanceMetadata(region=env_region)
