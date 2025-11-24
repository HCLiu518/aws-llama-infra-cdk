#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_llama_infra_cdk.aws_llama_infra_cdk_stack import AwsLlamaInfraCdkStack


app = cdk.App()
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')
    )
AwsLlamaInfraCdkStack(app, "AwsLlamaInfraCdkStack",
    env=env
    )

app.synth()
