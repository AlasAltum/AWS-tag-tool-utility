#!/usr/bin/env python3
import boto3
import json
import sys
import importlib
from botocore.exceptions import ClientError
from colorama import init, Fore, Style
from typing import List, Tuple, Dict, Any, Optional

# Initialize colorama
init()

class AWSTaggingTool:
    def __init__(self, config_file: str = 'tagging_resources_conf.json'):
        self.session = boto3.Session()
        self.sts = self.session.client('sts')
        self.config = self._load_config(config_file)
        self.changes: List[Tuple[str, str, str, str]] = []
        self.no_changes: List[Tuple[str, str, str, str]] = []
        self.service_handlers = {}

    def _load_config(self, config_file: str) -> Dict[str, bool]:
        """Load the configuration file."""
        try:
            with open(config_file, 'r') as f:
                return {k.lower(): v for k, v in json.load(f).items()}
        except FileNotFoundError:
            print(f"{Fore.RED}Error: Config file '{config_file}' not found.{Style.RESET_ALL}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Invalid JSON in config file.{Style.RESET_ALL}")
            sys.exit(1)

    def get_caller_identity(self) -> None:
        """Display the current AWS account and user information."""
        try:
            identity = self.sts.get_caller_identity()
            account_id = identity.get('Account', 'N/A')
            user_arn = identity.get('Arn', 'N/A')
            print(f"{Fore.CYAN}Using AWS Account ID: {account_id}"){
                "lambda": true,
                "ec2": true,
                "vpc": true,
                "s3": true,
                "eks": true,
                "elb": true,
                "opensearch": true,
                "kinesis": false,
                "rds": false,
                "dynamodb": false,
                "sqs": false,
                "sns": false,
                "apigateway": false
            }
            print(f"User ARN: {user_arn}{Style.RESET_ALL}\n")
        except ClientError as e:
            print(f"{Fore.RED}Error getting caller identity: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def _get_service_handler(self, service_name: str) -> Any:
        """Get the appropriate service handler for the given service name."""
        if service_name not in self.service_handlers:
            try:
                # Dynamically import the service module
                module_name = f"aws_services.{service_name}_service"
                module = importlib.import_module(module_name)
                
                # The class name is expected to be {SERVICENAME}Service (e.g., VPCService, EC2Service)
                # Convert service_name to uppercase for consistency
                class_name = f"{service_name.upper()}Service" if len(service_name) <= 3 else f"{service_name.capitalize()}Service"
                service_class = getattr(module, class_name)
                
                # Create and cache the handler
                self.service_handlers[service_name] = service_class(self.session)
            except (ImportError, AttributeError) as e:
                print(f"{Fore.YELLOW}Warning: Could not load handler for {service_name}: {e}{Style.RESET_ALL}")
                return None
                
        return self.service_handlers.get(service_name)

    def process_resources(self) -> None:
        """Process all resources based on the configuration."""
        for service_name, enabled in self.config.items():
            if not enabled:
                continue
                
            handler = self._get_service_handler(service_name)
            if not handler:
                continue
                
            try:
                changes, no_changes = handler.process_resources()
                self.changes.extend(changes)
                self.no_changes.extend(no_changes)
            except Exception as e:
                print(f"{Fore.YELLOW}Error processing {service_name}: {e}{Style.RESET_ALL}")

    def apply_changes(self) -> None:
        """Apply all pending tag changes."""
        if not self.changes:
            print(f"{Fore.YELLOW}No changes to apply.{Style.RESET_ALL}")
            return

        print("\\nApplying changes...")
        
        # Group changes by resource type for more efficient processing
        changes_by_type = {}
        for change in self.changes:
            resource_type = change[0].lower()
            if resource_type not in changes_by_type:
                changes_by_type[resource_type] = []
            changes_by_type[resource_type].append(change[1:])  # Remove the resource type
        
        # Apply changes by resource type
        for resource_type, resources in changes_by_type.items():
            handler = self._get_service_handler(resource_type)
            if not handler:
                print(f"{Fore.RED}No handler found for resource type: {resource_type}{Style.RESET_ALL}")
                continue
                
            for resource in resources:
                resource_id, tag_key, tag_value = resource
                try:
                    if handler.apply_tags(resource_id, {tag_key: tag_value}):
                        print(f"{Fore.GREEN}Applied tag {tag_key}={tag_value} to {resource_type.upper()} {resource_id}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Error applying tag to {resource_type} {resource_id}: {e}{Style.RESET_ALL}")

    def print_changes(self) -> None:
        """Print the changes that will be made."""
        if self.changes:
            print(f"\\n{Fore.YELLOW}The following changes will be made:{Style.RESET_ALL}")
            self._print_resources(self.changes, Fore.YELLOW)
        
        if self.no_changes:
            print(f"\\n{Fore.GREEN}The following resources are already correctly tagged:{Style.RESET_ALL}")
            self._print_resources(self.no_changes, Fore.GREEN)

    def _print_resources(self, resources: List[Tuple[str, str, str, str]], color: str) -> None:
        """Print resources grouped by resource type."""
        # Group by resource type
        resources_by_type = {}
        for resource in resources:
            resource_type = resource[0]
            if resource_type not in resources_by_type:
                resources_by_type[resource_type] = []
            resources_by_type[resource_type].append(resource[1:])  # Remove the resource type
        
        # Print by resource type
        for resource_type, items in resources_by_type.items():
            print(f"\\n{color}{resource_type} ({len(items)}):{Style.RESET_ALL}")
            for item in items:
                resource_id, tag_key, tag_value = item
                print(f"  {resource_id}: {tag_key} = {tag_value}")

def main():
    print(f"{Fore.CYAN}=== AWS Resource Tagging Tool ==={Style.RESET_ALL}")
    
    tool = AWSTaggingTool()
    tool.get_caller_identity()
    
    print("Scanning resources...")
    tool.process_resources()
    
    tool.print_changes()
    
    if tool.changes:
        apply = input("\\n\nDo you want to apply these changes? (yes/no): ").strip().lower()
        if apply == 'yes':
            tool.apply_changes()
            print(f"{Fore.GREEN}\\nAll changes have been applied successfully!{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}\\nChanges were not applied.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}\\nNo changes required. All resources are properly tagged.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
