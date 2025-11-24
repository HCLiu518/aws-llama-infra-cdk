from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput
)
from constructs import Construct
import os

class AwsLlamaInfraCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Get variables from Environment
        hf_token = os.environ.get("HF_TOKEN")
        ip_address = os.environ.get("IP_ADDRESS")
        if not hf_token:
            print("WARNING: HF_TOKEN is not set. The container might fail to download the model.")
        if not ip_address:
            print("WARNING: IP_ADDRESS is not set. The ingress rule setting might fail.")

        # 2. Network: Use Default VPC (Simplest setup)
        vpc = ec2.Vpc.from_lookup(self, "VPC", is_default=True)

        # 3. Security Group: Allow SSH (22) and API (8000) from the given ip address
        security_group = ec2.SecurityGroup(self, "LlamaSG",
            vpc=vpc,
            description="Allow SSH and vLLM access",
            allow_all_outbound=True
        )
        security_group.add_ingress_rule(ec2.Peer.ipv4(ip_address + "/32"), ec2.Port.tcp(22), "SSH Access")
        security_group.add_ingress_rule(ec2.Peer.ipv4(ip_address + "/32"), ec2.Port.tcp(8000), "vLLM API Access")

        # 4. Machine Image: Deep Learning AMI (Ubuntu 24.04, x86)
        ami = ec2.MachineImage.lookup(
            name="Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.8 (Ubuntu 24.04)*",
            owners=["amazon"],
            filters={
                "architecture": ["x86_64"] 
            }
        )

        # 5. User Data: The Automation Script
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "mkdir -p /root/.cache/huggingface",
            f"docker run -d \\",
            f"  --name llama3-inference \\",
            f"  --runtime nvidia \\",
            f"  --gpus all \\",
            f"  -v /root/.cache/huggingface:/root/.cache/huggingface \\",
            f"  --env HUGGING_FACE_HUB_TOKEN={hf_token} \\",
            f"  -p 8000:8000 \\",
            f"  --ipc=host \\",
            f"  --restart always \\",
            f"  vllm/vllm-openai:latest \\",
            f"  --model meta-llama/Meta-Llama-3.1-8B-Instruct \\",
            f"  --max-model-len 8192 \\",
            f"  --gpu-memory-utilization 0.95"
        )

        # Get the Key Pair
        key_pair = ec2.KeyPair.from_key_pair_name(self, "KeyPair", "aws-llama-key") # The key pair is created manually

        # Create the Instance: g5.xlarge
        instance = ec2.Instance(self, "Llama3Instance",
            instance_type=ec2.InstanceType("g5.xlarge"),
            machine_image=ami,
            vpc=vpc,
            security_group=security_group,
            key_pair=key_pair,
            user_data=user_data,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume.ebs(100) # 100GB Storage
                )
            ]
        )

        # Output the IP
        CfnOutput(self, "InstancePublicIP", value=instance.instance_public_ip)