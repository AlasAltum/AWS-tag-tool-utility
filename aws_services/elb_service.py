from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class ELBService(BaseAWSService):
    """Handler for AWS Elastic Load Balancing resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.elbv2 = session.client('elbv2')  # For Application and Network Load Balancers
        self.elb = session.client('elb')      # For Classic Load Balancers
        self.service_name = 'elb'
    
    def get_resources(self):
        """Get all load balancers (Application, Network, and Classic)."""
        resources = []
        
        try:
            # Get Application and Network Load Balancers (v2 API)
            paginator = self.elbv2.get_paginator('describe_load_balancers')
            for page in paginator.paginate():
                for lb in page.get('LoadBalancers', []):
                    arn = lb['LoadBalancerArn']
                    name = lb['LoadBalancerName']
                    tags_response = self.elbv2.describe_tags(ResourceArns=[arn])
                    tags = {}
                    if 'TagDescriptions' in tags_response and tags_response['TagDescriptions']:
                        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0].get('Tags', [])}
                    resources.append((arn, name, tags))
            
            # Get Classic Load Balancers
            classic_lbs = self.elb.describe_load_balancers()
            for lb in classic_lbs.get('LoadBalancerDescriptions', []):
                name = lb['LoadBalancerName']
                try:
                    tags_response = self.elb.describe_tags(LoadBalancerNames=[name])
                    tags = {}
                    if 'TagDescriptions' in tags_response and tags_response['TagDescriptions']:
                        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0].get('Tags', [])}
                    resources.append((f"classic/{name}", name, tags))
                except ClientError as e:
                    print(f"Error getting tags for Classic Load Balancer {name}: {e}")
                    
        except ClientError as e:
            print(f"Error listing load balancers: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to a load balancer."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            if resource_id.startswith('classif'):
                # Handle Classic Load Balancer
                lb_name = resource_id.split('/')[1]
                # Get existing tags
                existing_tags = self.elb.describe_tags(LoadBalancerNames=[lb_name])
                existing_tags_dict = {}
                if 'TagDescriptions' in existing_tags and existing_tags['TagDescriptions']:
                    existing_tags_dict = {tag['Key']: tag['Value'] for tag in existing_tags['TagDescriptions'][0].get('Tags', [])}
                
                # Only add tags that don't exist
                new_tags = {k: v for k, v in tags.items() if k not in existing_tags_dict}
                
                if not new_tags:
                    return True
                
                # Convert to the format expected by add_tags
                tag_list = [{'Key': k, 'Value': v} for k, v in new_tags.items()]
                
                # Add only new tags
                self.elb.add_tags(
                    LoadBalancerNames=[lb_name],
                    Tags=tag_list
                )
            else:
                # Handle Application/Network Load Balancer (v2)
                # Get existing tags
                existing_tags = self.elbv2.describe_tags(ResourceArns=[resource_id])
                existing_tags_dict = {}
                if 'TagDescriptions' in existing_tags and existing_tags['TagDescriptions']:
                    existing_tags_dict = {tag['Key']: tag['Value'] for tag in existing_tags['TagDescriptions'][0].get('Tags', [])}
                
                # Only add tags that don't exist
                new_tags = {k: v for k, v in tags.items() if k not in existing_tags_dict}
                
                if not new_tags:
                    return True
                
                # Convert to the format expected by add_tags
                tag_list = [{'Key': k, 'Value': v} for k, v in new_tags.items()]
                
                # Add only new tags
                self.elbv2.add_tags(
                    ResourceArns=[resource_id],
                    Tags=tag_list
                )
            
            return True
            
        except ClientError as e:
            print(f"Error tagging load balancer {resource_id}: {e}")
            return False
