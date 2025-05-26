from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class RDSService(BaseAWSService):
    """Handler for Amazon RDS resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('rds')
        self.service_name = 'rds'
    
    def get_resources(self):
        """Get all RDS instances."""
        resources = []
        
        try:
            # Get DB instances
            paginator = self.client.get_paginator('describe_db_instances')
            for page in paginator.paginate():
                for db in page.get('DBInstances', []):
                    arn = db['DBInstanceArn']
                    name = db.get('DBInstanceIdentifier', '')
                    tags = {tag['Key']: tag['Value'] 
                           for tag in self.client.list_tags_for_resource(
                               ResourceName=arn).get('TagList', [])}
                    resources.append((arn, name, tags))
                    
            # Get DB clusters (for Aurora)
            try:
                clusters = self.client.describe_db_clusters()
                for cluster in clusters.get('DBClusters', []):
                    arn = cluster['DBClusterArn']
                    name = cluster.get('DBClusterIdentifier', '')
                    # Only add if not already in resources (to avoid duplicates with instances)
                    if not any(r[0] == arn for r in resources):
                        tags = {tag['Key']: tag['Value'] 
                               for tag in self.client.list_tags_for_resource(
                                   ResourceName=arn).get('TagList', [])}
                        resources.append((arn, name, tags))
            except ClientError as e:
                print(f"Error getting RDS clusters: {e}")
                
        except ClientError as e:
            print(f"Error listing RDS resources: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an RDS resource."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            existing_tags = self.client.list_tags_for_resource(
                ResourceName=resource_id
            ).get('TagList', [])
            
            # Only add tags that don't exist
            existing_tag_keys = {tag['Key'] for tag in existing_tags}
            new_tags = [{'Key': k, 'Value': v} 
                       for k, v in tags.items() 
                       if k not in existing_tag_keys]
            
            if not new_tags:
                return True
                
            # Add only new tags
            self.client.add_tags_to_resource(
                ResourceName=resource_id,
                Tags=new_tags
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging RDS resource {resource_id}: {e}")
            return False
