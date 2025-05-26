from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class APIGatewayService(BaseAWSService):
    """Handler for Amazon API Gateway resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('apigateway')
        self.service_name = 'apigateway'
    
    def get_resources(self):
        """Get all API Gateway REST APIs."""
        resources = []
        
        try:
            # Get all REST APIs
            apis = self.client.get_rest_apis().get('items', [])
            
            for api in apis:
                api_id = api['id']
                api_name = api.get('name', f'api-{api_id}')
                
                # Get API tags
                try:
                    tags = self.client.get_tags(resourceArn=f"arn:aws:apigateway:{self.session.region_name}::/restapis/{api_id}")
                    tags_dict = tags.get('tags', {})
                except ClientError as e:
                    print(f"Error getting tags for API Gateway {api_id}: {e}")
                    tags_dict = {}
                
                resources.append((api_id, api_name, tags_dict))
                
        except ClientError as e:
            print(f"Error listing API Gateway REST APIs: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an API Gateway REST API."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            try:
                existing_tags = self.client.get_tags(
                    resourceArn=f"arn:aws:apigateway:{self.session.region_name}::/restapis/{resource_id}"
                ).get('tags', {})
            except ClientError as e:
                if e.response['Error']['Code'] != 'NotFoundException':
                    raise
                existing_tags = {}
            
            # Only add tags that don't exist
            new_tags = {k: v for k, v in tags.items() if k not in existing_tags}
            
            if not new_tags:
                return True
                
            # Add only new tags
            self.client.tag_resource(
                resourceArn=f"arn:aws:apigateway:{self.session.region_name}::/restapis/{resource_id}",
                tags=new_tags
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging API Gateway {resource_id}: {e}")
            return False
