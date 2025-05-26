from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class SQSService(BaseAWSService):
    """Handler for Amazon SQS resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('sqs')
        self.service_name = 'sqs'
    
    def get_resources(self):
        """Get all SQS queues."""
        resources = []
        
        try:
            # Get queue URLs
            response = self.client.list_queues()
            queue_urls = response.get('QueueUrls', [])
            
            for queue_url in queue_urls:
                try:
                    # Get queue attributes including tags
                    queue_attrs = self.client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['QueueArn', 'All']
                    )['Attributes']
                    
                    arn = queue_attrs.get('QueueArn', '')
                    queue_name = queue_url.split('/')[-1]
                    
                    # Get queue tags
                    tags_response = self.client.list_queue_tags(QueueUrl=queue_url)
                    tags = tags_response.get('Tags', {})
                    
                    resources.append((arn, queue_name, tags))
                    
                except ClientError as e:
                    print(f"Error getting info for SQS queue {queue_url}: {e}")
                    
        except ClientError as e:
            print(f"Error listing SQS queues: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an SQS queue."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # For SQS, we need the queue URL, not ARN
            # Extract queue name from ARN (format: arn:aws:sqs:region:account-id:queuename)
            queue_name = resource_id.split(':')[-1]
            account_id = resource_id.split(':')[4]
            region = resource_id.split(':')[3]
            queue_url = f"https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}"
            
            # Get existing tags
            try:
                existing_tags = self.client.list_queue_tags(QueueUrl=queue_url).get('Tags', {})
            except ClientError as e:
                if e.response['Error']['Code'] != 'AWS.SimpleQueueService.NonExistentQueue':
                    raise
                existing_tags = {}
            
            # Only add tags that don't exist
            new_tags = {k: v for k, v in tags.items() if k not in existing_tags}
            
            if not new_tags:
                return True
                
            # Add only new tags
            self.client.tag_queue(
                QueueUrl=queue_url,
                Tags=new_tags
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging SQS queue {resource_id}: {e}")
            return False
