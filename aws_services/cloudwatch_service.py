from botocore.exceptions import ClientError
from .base_service import BaseAWSService

class CloudWatchService(BaseAWSService):
    """Handler for Amazon CloudWatch resources."""
    
    def __init__(self, session):
        super().__init__(session)
        self.client = session.client('cloudwatch')
        self.logs_client = session.client('logs')  # For CloudWatch Logs
        self.service_name = 'cloudwatch'
    
    def get_resources(self):
        """Get all CloudWatch Alarms and Log Groups."""
        resources = []
        
        try:
            # Get all CloudWatch Alarms
            paginator = self.client.get_paginator('describe_alarms')
            for page in paginator.paginate():
                for alarm in page.get('MetricAlarms', []):
                    alarm_arn = alarm['AlarmArn']
                    alarm_name = alarm['AlarmName']
                    
                    # Get alarm tags
                    try:
                        tags = self.client.list_tags_for_resource(ResourceARN=alarm_arn).get('Tags', [])
                        tags_dict = {tag['Key']: tag['Value'] for tag in tags}
                    except ClientError as e:
                        print(f"Error getting tags for CloudWatch Alarm {alarm_name}: {e}")
                        tags_dict = {}
                    
                    resources.append((alarm_arn, alarm_name, tags_dict))
            
            # Get all CloudWatch Log Groups
            log_paginator = self.logs_client.get_paginator('describe_log_groups')
            for page in log_paginator.paginate():
                for log_group in page.get('logGroups', []):
                    log_group_name = log_group['logGroupName']
                    log_group_arn = f"arn:aws:logs:{self.session.region_name}:{self.session.client('sts').get_caller_identity().get('Account')}:log-group:{log_group_name}"
                    
                    # Get log group tags
                    try:
                        tags = self.logs_client.list_tags_log_group(logGroupName=log_group_name).get('tags', {})
                        tags_dict = {k: str(v) for k, v in tags.items()}
                    except ClientError as e:
                        print(f"Error getting tags for CloudWatch Log Group {log_group_name}: {e}")
                        tags_dict = {}
                    
                    resources.append((log_group_arn, log_group_name, tags_dict))
                    
        except ClientError as e:
            print(f"Error listing CloudWatch resources: {e}")
            
        return resources
    
    def apply_tags(self, resource_id, tags):
        """Apply tags to a CloudWatch resource (Alarm or Log Group)."""
        try:
            # Skip AWS reserved tags
            tags = {k: v for k, v in tags.items() if not k.startswith('aws:')}
            
            if ':alarm:' in resource_id:
                # Handle CloudWatch Alarm
                try:
                    # Get existing tags
                    existing_tags = self.client.list_tags_for_resource(ResourceARN=resource_id).get('Tags', [])
                    existing_tag_keys = {tag['Key'] for tag in existing_tags}
                    
                    # Only add tags that don't exist
                    new_tags = [{'Key': k, 'Value': v} 
                               for k, v in tags.items() 
                               if k not in existing_tag_keys]
                    
                    if not new_tags:
                        return True
                        
                    # Add only new tags
                    self.client.tag_resource(
                        ResourceARN=resource_id,
                        Tags=new_tags
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceNotFound':
                        raise
                    print(f"CloudWatch Alarm {resource_id} not found")
                    return False
                    
            elif ':log-group:' in resource_id:
                # Handle CloudWatch Log Group
                log_group_name = resource_id.split(':log-group:')[-1].rstrip(':*')
                
                # Get existing tags
                try:
                    existing_tags = self.logs_client.list_tags_log_group(logGroupName=log_group_name).get('tags', {})
                    
                    # Only add tags that don't exist
                    new_tags = {k: str(v) for k, v in tags.items() if k not in existing_tags}
                    
                    if not new_tags:
                        return True
                        
                    # Add only new tags
                    self.logs_client.tag_log_group(
                        logGroupName=log_group_name,
                        tags=new_tags
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceNotFoundException':
                        raise
                    print(f"CloudWatch Log Group {log_group_name} not found")
                    return False
            else:
                print(f"Unsupported CloudWatch resource type: {resource_id}")
                return False
                
            return True
            
        except ClientError as e:
            print(f"Error tagging CloudWatch resource {resource_id}: {e}")
            return False
