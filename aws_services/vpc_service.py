from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class VPCService(BaseAWSService):
    """Handler for AWS VPC resources."""

    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('ec2')
        self.service_name = 'vpc'

    def get_resources(self):
        """Get all VPCs."""
        resources = []

        try:
            response = self.client.describe_vpcs()
            
            for vpc in response.get('Vpcs', []):
                vpc_id = vpc['VpcId']
                tags = {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
                
                # Use the Name tag if it exists, otherwise generate a name
                vpc_name = tags.get('Name', f"vpc-{vpc_id}")
                resources.append((vpc_id, vpc_name, tags))

        except ClientError as e:
            print(f"Error listing VPCs: {e}")

        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to a VPC."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            response = self.client.describe_tags(
                Filters=[
                    {'Name': 'resource-id', 'Values': [resource_id]},
                    {'Name': 'key', 'Values': list(tags.keys())}
                ]
            )
            
            # Get tags that don't exist yet
            existing_tag_keys = {tag['Key'] for tag in response.get('Tags', [])}
            new_tags = [{'Key': k, 'Value': v} 
                      for k, v in tags.items() 
                      if k not in existing_tag_keys]
            
            if not new_tags:
                return True
                
            # Only add new tags that don't exist
            self.client.create_tags(
                Resources=[resource_id],
                Tags=new_tags
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging VPC {resource_id}: {e}")
            return False
