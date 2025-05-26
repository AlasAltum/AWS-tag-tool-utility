# Initialize aws_services package
from .base_service import BaseAWSService
from .lambda_service import LambdaService
from .ec2_service import EC2Service
from .vpc_service import VPCService
from .s3_service import S3Service
from .eks_service import EKSService
from .opensearch_service import OpenSearchService
from .elb_service import ELBService
from .rds_service import RDSService
from .dynamodb_service import DynamoDBService
from .sqs_service import SQSService
from .sns_service import SNSService
from .apigateway_service import APIGatewayService
from .cloudwatch_service import CloudWatchService

# Service registry maps service names to their handler classes
SERVICE_REGISTRY = {
    'lambda': LambdaService,
    'ec2': EC2Service,
    'vpc': VPCService,
    's3': S3Service,
    'eks': EKSService,
    'elb': ELBService,
    'opensearch': OpenSearchService,
    'rds': RDSService,
    'dynamodb': DynamoDBService,
    'sqs': SQSService,
    'sns': SNSService,
    'apigateway': APIGatewayService,
    'cloudwatch': CloudWatchService
}

def get_service_handler(service_name, session):
    """Factory function to get the appropriate service handler."""
    service_class = SERVICE_REGISTRY.get(service_name.lower())
    if not service_class:
        raise ValueError(f"No handler found for service: {service_name}")
    return service_class(session)
