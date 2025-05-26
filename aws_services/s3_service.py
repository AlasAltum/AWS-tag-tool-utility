from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class S3Service(BaseAWSService):
    """Handler for AWS S3 buckets."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('s3')
        self.service_name = 's3'
    
    def get_resources(self):
        """Get all S3 buckets."""
        resources = []
        
        try:
            response = self.client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket tags
                    tag_response = self.client.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagSet', [])}
                except ClientError:
                    # No tags set yet
                    tags = {}
                
                # Use the bucket name as the resource name
                bucket_name_display = bucket_name
                
                resources.append((bucket_name, bucket_name_display, tags))
                
        except ClientError as e:
            print(f"Error listing S3 buckets: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an S3 bucket."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            try:
                existing_tags = self.client.get_bucket_tagging(Bucket=resource_id)
                existing_tag_dict = {tag['Key']: tag['Value'] for tag in existing_tags.get('TagSet', [])}
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchTagSet':
                    raise
                existing_tag_dict = {}
            
            # Only add tags that don't exist
            new_tags = {k: v for k, v in tags.items() if k not in existing_tag_dict}
            
            if not new_tags:
                return True
                
            # Merge with existing tags
            all_tags = {**existing_tag_dict, **new_tags}
            
            # Convert to tag set format
            tag_set = [{'Key': k, 'Value': v} for k, v in all_tags.items()]
            
            self.client.put_bucket_tagging(
                Bucket=resource_id,
                Tagging={'TagSet': tag_set}
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging S3 bucket {resource_id}: {e}")
            return False
