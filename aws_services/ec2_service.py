from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class EC2Service(BaseAWSService):
    """Handler for AWS EC2 instances."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('ec2')
        self.resource = session.resource('ec2')
        self.service_name = 'ec2'
    
    def get_resources(self):
        """Get all EC2 instances."""
        resources = []
        
        try:
            instances = self.resource.instances.all()
            
            for instance in instances:
                instance_id = instance.id
                tags = {tag['Key']: tag['Value'] for tag in instance.tags or []}
                
                # Use the Name tag if it exists, otherwise use the instance ID
                instance_name = tags.get('Name', f"ec2-{instance_id}")
                
                resources.append((instance_id, instance_name, tags))
                
        except ClientError as e:
            print(f"Error listing EC2 instances: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an EC2 instance."""
        try:
            # Skip AWS reserved tags and tags that already exist
            existing_tags = self.client.describe_tags(
                Filters=[
                    {'Name': 'resource-id', 'Values': [resource_id]},
                    {'Name': 'key', 'Values': list(tags.keys())}
                ]
            )
            
            # Get tags that don't exist yet
            existing_tag_keys = {tag['Key'] for tag in existing_tags.get('Tags', [])}
            new_tags = [{'Key': k, 'Value': v} 
                      for k, v in tags.items() 
                      if k not in existing_tag_keys and not k.startswith('aws:')]
            
            if not new_tags:
                return True
                
            self.client.create_tags(
                Resources=[resource_id],
                Tags=new_tags
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging EC2 instance {resource_id}: {e}")
