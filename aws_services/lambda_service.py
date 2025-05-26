from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class LambdaService(BaseAWSService):
    """Handler for AWS Lambda resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('lambda')
        self.service_name = 'lambda'
    
    def get_resources(self):
        """Get all Lambda functions."""
        resources = []

        try:
            paginator = self.client.get_paginator('list_functions')
            for page in paginator.paginate():
                for func in page.get('Functions', []):
                    func_name = func['FunctionName']
                    func_arn = func['FunctionArn']

                    # Get tags for the function
                    try:
                        tags = self.client.list_tags(Resource=func_arn).get('Tags', {})
                    except ClientError:
                        tags = {}

                    resources.append((func_arn, func_name, tags))

        except ClientError as e:
            print(f"Error listing Lambda functions: {e}")

        return resources

    def apply_tags(self, resource_id, tags):
        """Apply tags to a Lambda function."""
        try:
            # Get existing tags
            existing_tags = self.client.list_tags(Resource=resource_id).get('Tags', {})
            
            # Skip AWS reserved tags (starting with 'aws:')
            tags = {k: v for k, v in tags.items() 
                    if not k.startswith('aws:') and k not in existing_tags}
            
            # If no valid tags to apply, return True
            if not tags:
                return True
            
            # Only add new tags that don't exist
            self.client.tag_resource(
                Resource=resource_id,
                Tags=tags
            )
                
            return True
            
        except ClientError as e:
            print(f"Error tagging Lambda function {resource_id}: {e}")
            return False
