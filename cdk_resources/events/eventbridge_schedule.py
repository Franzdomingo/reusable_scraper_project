from constructs import Construct
from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_ecs as ecs,
    aws_iam as iam,
    Tags
)
from ..utils import apply_tags

class EventBridgeScheduleConstruct(Construct):

    def __init__(self, scope: Construct, id: str, config: dict, ecs_task: ecs.TaskDefinition, cluster: ecs.ICluster, env_name: str, event_role: iam.Role, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get EventBridge specific config
        eventbridge_config = config["eventbridge"]

        # Define the EventBridge rule (schedule) with new naming pattern
        rule_construct_id = f"{env_name}TriggerECSCluster"
        rule = events.Rule(self, rule_construct_id,
            schedule=events.Schedule.cron(
                minute=eventbridge_config["minute"],
                hour=eventbridge_config["hour"],
                month=eventbridge_config["month"],
                week_day=eventbridge_config["week_day"],
                year=eventbridge_config["year"]
            )
        )


        # Add ECS task as target
        rule.add_target(targets.EcsTask(
            cluster=cluster,
            task_definition=ecs_task,
            task_count=1,
            launch_type=ecs.LaunchType.EC2,
            role=event_role
        ))

        # Apply dynamic tags to EventBridge rule
        apply_tags(rule, config, "eventbridge-rule")

        # Store rule as instance variable for property access
        self.rule = rule

    @property
    def eventbridge_rule(self) -> events.Rule:
        """Returns the created EventBridge rule for use in other constructs."""
        return self.rule

    @property
    def rule_arn(self) -> str:
        """Returns the ARN of the created EventBridge rule."""
        return self.rule.rule_arn

    @property
    def rule_name(self) -> str:
        """Returns the name of the created EventBridge rule."""
        return self.rule.rule_name
