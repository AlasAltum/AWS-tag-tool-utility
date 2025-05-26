from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class SNSService(BaseAWSService):
    """Handler for Amazon SNS resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('sns')
        self.service_name = 'sns'
    
    def get_resources(self):
        """Get all SNS topics."""
        resources = []
        
        try:
            # Get all topics
            paginator = self.client.get_paginator('list_topics')
            for page in paginator.paginate():
                for topic in page.get('Topics', []):
                    topic_arn = topic['TopicArn']
                    topic_name = topic_arn.split(':')[-1]
                    
                    # Get topic tags
                    try:
                        tags_response = self.client.list_tags_for_resource(ResourceArn=topic_arn)
                        tags = {tag['Key']: tag['Value'] for tag in tags_response.get('Tags', [])}
                    except ClientError as e:
                        print(f"Error getting tags for SNS topic {topic_arn}: {e}")
                        tags = {}
                    
                    resources.append((topic_arn, topic_name, tags))
                    
        except ClientError as e:
            print(f"Error listing SNS topics: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an SNS topic."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            try:
                existing_tags = self.client.list_tags_for_resource(ResourceArn=resource_id).get('Tags', [])
                existing_tag_keys = {tag['Key'] for tag in existing_tags}
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFound':
                    raise
                existing_tag_keys = set()
            
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
            print(f"Error tagging SNS topic {resource_id}: {e}")
            return False
