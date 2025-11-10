from aws_cdk import Tags
from constructs import IConstruct


def apply_tags(construct: IConstruct, config: dict, resource_type: str):
    """Apply tags to AWS resources from config.

    Args:
        construct: The CDK construct to tag
        config: Configuration dictionary containing tags
        resource_type: Type of resource being tagged (for logging/tracking)
    """
    if "tags" in config:
        for key, value in config["tags"].items():
            Tags.of(construct).add(key, value)
