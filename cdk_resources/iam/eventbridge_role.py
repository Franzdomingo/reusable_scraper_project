from aws_cdk import aws_iam as iam, aws_ecs as ecs, Tags
from constructs import Construct
from ..utils import apply_tags


class EventBridgeRoleConstruct(Construct):
    def __init__(self, scope: Construct, id: str, config: dict, env_name: str, ecs_task: ecs.TaskDefinition, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get configuration and system name
        assumed_by = config["eventbridge"]["event_role"]["assumed_by"]
        actions = config["eventbridge"]["event_role"]["actions"]
        system_name = config["system_name"]

        # EventBridge role to trigger ECS with new naming pattern
        event_role_name = f"llm-{env_name}-{system_name}-eventbridge-role"
        event_role_construct_id = f"{env_name}EventBridgeEcsRole"

        self.event_role = iam.Role(
            self, event_role_construct_id,
            assumed_by=iam.ServicePrincipal(assumed_by),
            role_name=event_role_name
        )

        # Allow starting ECS tasks
        self.event_role.add_to_policy(
            iam.PolicyStatement(
                actions=actions,
                resources=[ecs_task.task_definition_arn]
            )
        )

        # Apply dynamic tags from config
        apply_tags(self.event_role, config, "eventbridge-role")


    @property
    def role(self) -> iam.Role:
        """Returns the created EventBridge IAM role for use in other constructs."""
        return self.event_role

    @property
    def role_arn(self) -> str:
        """Returns the ARN of the created EventBridge IAM role."""
        return self.event_role.role_arn

    @property
    def role_name(self) -> str:
        """Returns the name of the created EventBridge IAM role."""
        return self.event_role.role_name
