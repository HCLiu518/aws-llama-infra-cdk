# Ephemeral AI Inference Platform (AWS CDK + vLLM)

A scalable, Infrastructure-as-Code (IaC) solution for deploying Large Language Models (LLMs) on AWS. This project provisions ephemeral GPU clusters to host **Meta-Llama-3.1-8B** using **vLLM** for high-throughput inference.

## Architecture

* **Infrastructure:** AWS CDK (Python)
* **Compute:** Amazon EC2 `g5.xlarge` (NVIDIA A10G GPU)
* **Engine:** vLLM (with PagedAttention)
* **Model:** Meta-Llama-3.1-8B-Instruct
* **Security:** VPC-isolated with IP-restricted Security Groups

## Key Features

* **Automated Provisioning:** One-click deploy/destroy cycle using AWS CDK.
* **Memory Optimization:** Solved Llama-3.1's 128k context OOM crash by tuning `--max-model-len` and `--gpu-memory-utilization` flags.
* **Dockerized Deployment:** Uses Cloud-Init (`user_data`) to bootstrap the vLLM container on instance startup.
* **Cost Efficiency:** Architecture designed for ephemeral usage (destroy after use) to minimize GPU hourly costs.

## Prerequisites

* AWS CLI (configured with Admin permissions)
* AWS CDK CLI (`npm install -g aws-cdk`)
* Python 3.8+
* Hugging Face Access Token (Read permissions)

## Deployment Guide

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

* Export your Hugging Face token and target region:

```bash
export HF_TOKEN="hf_your_token_here"
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION="us-east-2"
```

### 3. Deploy

```bash
cdk deploy
```

* The stack will output the `InstancePublicIP` upon completion.

### 4. Test Inference

* Please note that docker will take a while to spin up first time because of downloading the large images.
* Update the IP in `inference_client.py` and run:

```bash
python inference_client.py
```

### 5. Teardown (Stop Billing)

```bash
cdk destroy
```

## Cost Warning
* This project uses `g5.xlarge` instances (~$1.00/hr). **Always run `cdk destroy` when finished to avoid unexpected billing.**

## Performance Benchmarks

The system was stress-tested using `vllm bench serve` to simulate high-concurrency production traffic.

**Test Configuration:**
* **Hardware:** AWS `g5.xlarge` (1x NVIDIA A10G, 24GB VRAM)
* **Model:** Meta-Llama-3.1-8B-Instruct (Quantization: None)
* **Load:** 64 concurrent users sending random requests (128 input / 128 output tokens)

**Results:**
| Metric | Result | Impact |
| :--- | :--- | :--- |
| **Throughput (Total)** | **1,898 tokens/sec** | High capacity for batch processing. |
| **Throughput (Requests)** | **7.45 req/sec** | Handles ~7 concurrent active generations smoothly. |
| **Inter-Token Latency (ITL)** | **49.8 ms** | Fast streaming speed (approx. 20 words/sec) per user. |
| **Time to First Token (TTFT)** | **953 ms** | <1s startup delay even under full load (64 users). |

> **Analysis:** The system successfully handles heavy congestion (64 simultaneous users) while maintaining a strict <50ms typing speed, confirming that the `g5.xlarge` instance is memory-bandwidth bound rather than compute-bound for this workload.