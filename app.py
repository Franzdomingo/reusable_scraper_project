#!/usr/bin/env python3
import aws_cdk as cdk
from pathlib import Path
import json
from aws_cdk import Environment
from cdk_resources.llm_metadata_scraper import LLMMetadataScraperStack
import os

app = cdk.App()

env_name = app.node.try_get_context("env") or "stg"
config_file_name = f"{env_name}_config.json"
config_path = (Path(__file__).parent / "config" / config_file_name).resolve()

with open(config_path) as f:
    all_config = json.load(f)

config = all_config[env_name]
region = config["region"]

LLMMetadataScraperStack(
    app,
    f"llm-{env_name}-metadata-scraper",
    config=config,
    env_name=env_name,
    env=Environment(account=config["account"], region=region),
)

app.synth()
