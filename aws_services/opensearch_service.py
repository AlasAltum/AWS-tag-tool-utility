from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class OpenSearchService(BaseAWSService):
    """Handler for Amazon OpenSearch Service domains."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('opensearch')
        self.service_name = 'opensearch'

    def get_resources(self):
        """Get all OpenSearch domains."""
        resources = []
        
        try:
            # List all OpenSearch domains
            domains = self.client.list_domain_names()
            
            # Get details for each domain
            for domain in domains.get('DomainNames', []):
                domain_name = domain['DomainName']
                try:
                    domain_info = self.client.describe_domain(DomainName=domain_name)['DomainStatus']
                    arn = domain_info.get('ARN', f"arn:aws:es:{self.session.region_name}:{self.session.client('sts').get_caller_identity().get('Account')}:domain/{domain_name}")
                    tags_response = self.client.list_tags(ARN=arn)
                    tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
                    resources.append((arn, domain_name, tags))
                except ClientError as e:
                    print(f"Error describing OpenSearch domain {domain_name}: {e}")
                    
        except ClientError as e:
            print(f"Error listing OpenSearch domains: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an OpenSearch domain."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            existing_tags = self.client.list_tags(ARN=resource_id).get('TagList', [])
            existing_tags_dict = {tag['Key']: tag['Value'] for tag in existing_tags}
            
            # Only add tags that don't exist
            new_tags = {k: v for k, v in tags.items() if k not in existing_tags_dict}

            if not new_tags:
                return True
                
            # Convert new tags to the format expected by add_tags
            tag_list = [{'Key': k, 'Value': v} for k, v in new_tags.items()]
            
            # Add only new tags
            self.client.add_tags(
                ARN=resource_id,
                TagList=tag_list
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging OpenSearch domain {resource_id}: {e}")
            return False
