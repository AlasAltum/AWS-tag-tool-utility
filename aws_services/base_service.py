from abc import ABC, abstractmethod
from botocore.exceptions import ClientError

class BaseAWSService(ABC):
    """Base class for all AWS service handlers."""
    
    def __init__(self, session):
        self.session = session
        self.client = None
        self.resource = None
    
    @abstractmethod
    def get_resources(self):
        """
        Get all resources of this service type.
        Returns a list of tuples: (resource_id, resource_name, tags_dict)
        """
        pass

    @abstractmethod
    def apply_tags(self, resource_id, tags):
        """Apply the given tags to the specified resource."""
        pass
    
    def get_resource_name(self, resource_id, tags):
        """Get the resource name from tags or generate one."""
        return tags.get('Name', f"{self.service_name}-{resource_id}")
    
    def process_resources(self):
        """Process all resources of this service type."""
        changes = []
        no_changes = []
        
        try:
            resources = self.get_resources()
            for resource_id, resource_name, tags in resources:
                current_name = tags.get('Name', '')
                
                if current_name == resource_name:
                    no_changes.append((self.service_name.upper(), resource_id, 'Name', resource_name))
                else:
                    changes.append((self.service_name.upper(), resource_id, 'Name', resource_name))
                    
        except ClientError as e:
            print(f"Error processing {self.service_name} resources: {e}")
            
        return changes, no_changes
