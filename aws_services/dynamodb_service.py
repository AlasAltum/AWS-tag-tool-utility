from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class DynamoDBService(BaseAWSService):
    """Handler for Amazon DynamoDB resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('dynamodb')
        self.service_name = 'dynamodb'
    
    def get_resources(self):
        """Get all DynamoDB tables."""
        resources = []
        
        try:
            # Get all tables
            paginator = self.client.get_paginator('list_tables')
            for page in paginator.paginate():
                for table_name in page.get('TableNames', []):
                    try:
                        table_info = self.client.describe_table(TableName=table_name)['Table']
                        arn = table_info['TableArn']
                        tags = self.client.list_tags_of_resource(ResourceArn=arn).get('Tags', [])
                        tags_dict = {tag['Key']: tag['Value'] for tag in tags}
                        resources.append((arn, table_name, tags_dict))
                    except ClientError as e:
                        print(f"Error getting info for DynamoDB table {table_name}: {e}")
                        
        except ClientError as e:
            print(f"Error listing DynamoDB tables: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to a DynamoDB table."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            existing_tags = self.client.list_tags_of_resource(ResourceArn=resource_id).get('Tags', [])
            existing_tag_keys = {tag['Key'] for tag in existing_tags}
            
            # Only add tags that don't exist
            new_tags = [{'Key': k, 'Value': v} 
                       for k, v in tags.items() 
                       if k not in existing_tag_keys]
            
            if not new_tags:
                return True
                
            # Add only new tags
            self.client.tag_resource(
                ResourceArn=resource_id,
                Tags=new_tags
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging DynamoDB table {resource_id}: {e}")
            return False
