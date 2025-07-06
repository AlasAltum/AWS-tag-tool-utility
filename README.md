# AWS Resource Tagging Tool

A command-line tool to automatically tag AWS resources with a 'Name' tag based on their existing resource name or ID. This helps with better cost allocation and resource management.

## Features

- Automatically tags AWS resources with a 'Name' tag when they don't have already that name
- Supports multiple resource types (EC2, Lambda, VPC, S3, etc.)
- Preview changes before applying them
- Color-coded output for better readability
- Safe execution with confirmation prompt
- Works with your existing AWS credentials

## Prerequisites

- Python 3.7 or higher
- AWS CLI configured with appropriate credentials
- Required Python packages (install using `pip install -r requirements.txt`)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd AWS-tag-tool-utility
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit the `tagging_resources_conf.json` file to specify which resource types should be tagged:

```json
{
    "lambda": true,
    "vpc": true,
    "ec2": true,
    "s3": true,
    "rds": false,
    "dynamodb": false,
    "sqs": false,
    "sns": false,
    "apigateway": false
}
```

Set to `true` for resource types you want to tag, and `false` for those you want to skip.

## Usage

```bash
python tagging_tool.py
```

The tool will:
1. Show your AWS account information
2. Scan the specified resources
3. Show a preview of changes (resources to be tagged and already tagged resources)
4. Ask for confirmation before applying changes

## How It Works

1. The tool uses your AWS credentials from the default AWS CLI configuration
2. It scans the specified resource types in your AWS account
3. For each resource:
   - If it already has a 'Name' tag with the correct value, it's marked as "no change"
   - If it's missing a 'Name' tag or has an incorrect value, it's marked for update
4. After showing the preview, it asks for confirmation before making any changes

## Supported Resource Types

- [x] AWS Lambda Functions
- [x] EC2 Instances
- [x] VPCs
- [x] S3 Buckets
- [X] RDS Instances
- [X] DynamoDB Tables
- [X] SQS Queues
- [X] SNS Topics
- [X] API Gateway

## Security

- The tool only requires read/write permissions for the resource types you want to tag
- It runs locally on your machine and doesn't store any AWS credentials
- It shows a preview of all changes before applying them

## License

MIT


## Coding

Coded mostly with SWE-1. I am just a solutions architect :)
