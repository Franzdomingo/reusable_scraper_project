from aws_cdk import Stack
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs
)
from constructs import Construct
from cdk_resources.events.eventbridge_schedule import EventBridgeScheduleConstruct
from cdk_resources.ecs.ecs_cluster import ECSClusterConstruct
from cdk_resources.iam.eventbridge_role import EventBridgeRoleConstruct

class LLMMetadataScraperStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, env_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ECS Cluster Construct
        ecs_cluster = ECSClusterConstruct(
            self,
            "ECSCluster",
            config=config,
            env_name=env_name
        )

        # EventBridge Role Construct
        eventbridge_role = EventBridgeRoleConstruct(
            self,
            "EventBridgeRole",
            config=config,
            env_name=env_name,
            ecs_task=ecs_cluster.ecs_task
        )

        # EventBridge Construct
        eventbridge = EventBridgeScheduleConstruct(
            self,
            "EventBridgeSchedule",
            config=config,
            ecs_task=ecs_cluster.ecs_task,
            cluster=ecs_cluster.cluster,
            env_name=env_name,
            event_role=eventbridge_role.role
        )
