from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class EKSService(BaseAWSService):
    """Handler for Amazon EKS resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('eks')
        self.service_name = 'eks'
    
    def get_resources(self):
        """Get all EKS clusters."""
        resources = []
        
        try:
            # List all EKS clusters
            clusters = self.client.list_clusters()
            
            # Get details for each cluster
            for cluster_name in clusters.get('clusters', []):
                try:
                    cluster = self.client.describe_cluster(name=cluster_name)['cluster']
                    tags = cluster.get('tags', {})
                    resources.append((cluster['arn'], cluster['name'], tags))
                except ClientError as e:
                    print(f"Error describing EKS cluster {cluster_name}: {e}")
                    
        except ClientError as e:
            print(f"Error listing EKS clusters: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to an EKS cluster."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            # Get existing tags
            cluster_name = resource_id.split('/')[-1]
            existing_tags = self.client.describe_cluster(name=cluster_name)['cluster'].get('tags', {})
            
            # Only add tags that don't exist
            new_tags = {k: v for k, v in tags.items() if k not in existing_tags}
            
            if not new_tags:
                return True
                
            # Apply only new tags
            self.client.tag_resource(
                resourceArn=resource_id,
                tags=new_tags
            )
            return True
            
        except ClientError as e:
            print(f"Error tagging EKS cluster {resource_id}: {e}")
            return False
