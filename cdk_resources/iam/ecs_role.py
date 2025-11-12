from aws_cdk import aws_iam as iam, Tags
from constructs import Construct
from ..utils import apply_tags


class ECSTaskRoleConstruct(Construct):
    def __init__(self, scope: Construct, id: str, config: dict, env_name: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # ECS Task Role - Using dynamic naming pattern: llm-{env}-{system_name}-{component}
        task_role_assumed_by = config["iam"]["task_role"]["assumed_by"]
        task_role_inline_policies = config["iam"]["task_role"]["inline_policies"]
        system_name = config["system_name"]

        # Naming pattern: llm-{env}-{system_name}-{component}
        role_name = f"llm-{env_name}-{system_name}-task-role"
        construct_id = f"{env_name}TaskRole"

        self.task_role = iam.Role(
            self, construct_id,
            assumed_by=iam.ServicePrincipal(task_role_assumed_by),
            role_name=role_name
        )

        # S3 permissions for output storage
        if config.get("s3", {}).get("bucket_name"):
            self.task_role.add_to_policy(
                iam.PolicyStatement(
                    actions=task_role_inline_policies,
                    resources=[
                        f"arn:aws:s3:::{config['s3']['bucket_name']}",
                        f"arn:aws:s3:::{config['s3']['bucket_name']}/*"
                    ]
                )
            )

        # Apply dynamic tags from config
        apply_tags(self.task_role, config, "iam-role")


    @property
    def role(self) -> iam.Role:
        """Returns the created IAM role for use in other constructs."""
        return self.task_role

    @property
    def role_arn(self) -> str:
        """Returns the ARN of the created IAM role."""
        return self.task_role.role_arn

    @property
    def role_name(self) -> str:
        """Returns the name of the created IAM role."""
        return self.task_role.role_name
