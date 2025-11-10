from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    Tags
)
from ..iam.ecs_role import ECSTaskRoleConstruct
from ..utils import apply_tags


class ECSClusterConstruct(Construct):
    def __init__(self, scope: Construct, id: str, config: dict, env_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc_id = config["vpc_id"]
        availability_zones = config["availability_zones"]
        private_subnet_ids = config["private_subnet_ids"]

        vpc = ec2.Vpc.from_vpc_attributes(
            self, "ImportedVPC",
            vpc_id=vpc_id,
            availability_zones=availability_zones,
            private_subnet_ids=private_subnet_ids
        )

        # Import existing ECS Cluster
        cluster = ecs.Cluster.from_cluster_attributes(
            self, "ImportedCluster",
            cluster_name=config["ecs"]["cluster_name"],
            vpc=vpc
        )

        # ECS Task Role using the dedicated construct
        task_role_construct = ECSTaskRoleConstruct(
            self, "TaskRole",
            config=config,
            env_name=env_name
        )


        # ECS Task Definition
        system_name = config["system_name"]
        task_def_construct_id = f"{env_name}TaskDefinition"
        ecs_task = ecs.Ec2TaskDefinition(self, task_def_construct_id, task_role=task_role_construct.role)

        # Task Container
        image = ecs.ContainerImage.from_asset(config["ecs"]["container"]["image"])
        memory_limit_mib = config["ecs"]["container"]["memory_limit_mib"]
        cpu = config["ecs"]["container"]["cpu"]
        logging = config["ecs"]["container"]["logging"]
        env = config["ecs"]["environment_var"]

        # Container name with system_name pattern
        container_name = f"llm-{env_name}-{system_name}-app-container"
        container = ecs_task.add_container(
           container_name,
           image=image,
           memory_limit_mib=memory_limit_mib,
           cpu=cpu,
           logging=ecs.LogDriver.aws_logs(stream_prefix=logging),
           environment=env
        )

        # Apply dynamic tags to ECS resources
        apply_tags(ecs_task, config, "task-definition")

        # Expose ECS task definition and cluster
        self.ecs_task = ecs_task
        self.cluster = cluster

    @property
    def task_definition(self) -> ecs.TaskDefinition:
        """Returns the created ECS task definition for use in other constructs."""
        return self.ecs_task

    @property
    def task_definition_arn(self) -> str:
        """Returns the ARN of the created ECS task definition."""
        return self.ecs_task.task_definition_arn

    @property
    def ecs_cluster(self) -> ecs.ICluster:
        """Returns the imported ECS cluster for use in other constructs."""
        return self.cluster

    @property
    def cluster_name(self) -> str:
        """Returns the name of the ECS cluster."""
        return self.cluster.cluster_name
