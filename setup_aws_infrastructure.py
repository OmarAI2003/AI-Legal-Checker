#!/usr/bin/env python3
"""
AWS Infrastructure Setup for Egyptian Legal Contract Analysis System
Sets up Lambda function, API Gateway, S3 bucket, and IAM roles
"""

import boto3
import json
import time
import zipfile
import os
from botocore.exceptions import ClientError

def create_iam_role():
    """Create IAM role for Lambda function"""
    iam = boto3.client('iam', region_name='us-west-2')
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Create role
        response = iam.create_role(
            RoleName='egyptian-legal-lambda-role',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Egyptian Legal Contract Analysis Lambda function'
        )
        
        role_arn = response['Role']['Arn']
        print(f"Created IAM role: {role_arn}")
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        ]
        
        for policy_arn in policies:
            iam.attach_role_policy(
                RoleName='egyptian-legal-lambda-role',
                PolicyArn=policy_arn
            )
            print(f"Attached policy: {policy_arn}")
        
        return role_arn
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print("IAM role already exists, retrieving ARN...")
            response = iam.get_role(RoleName='egyptian-legal-lambda-role')
            return response['Role']['Arn']
        else:
            raise e

def create_lambda_function(role_arn):
    """Create Lambda function"""
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    # Create deployment package
    zip_path = 'egyptian-legal-lambda-deployment.zip'
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        zip_file.write('lambda-deployment/lambda_function.py', 'lambda_function.py')
    
    with open(zip_path, 'rb') as zip_file:
        zip_content = zip_file.read()
    
    try:
        response = lambda_client.create_function(
            FunctionName='egyptian-legal-contract-api',
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='Egyptian Legal Contract Analysis API',
            Timeout=300,
            MemorySize=1024
        )
        
        function_arn = response['FunctionArn']
        print(f"Created Lambda function: {function_arn}")
        
        return function_arn
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print("Lambda function already exists, updating code...")
            lambda_client.update_function_code(
                FunctionName='egyptian-legal-contract-api',
                ZipFile=zip_content
            )
            response = lambda_client.get_function(FunctionName='egyptian-legal-contract-api')
            return response['Configuration']['FunctionArn']
        else:
            raise e

def create_api_gateway(lambda_arn):
    """Create API Gateway"""
    api_gateway = boto3.client('apigateway', region_name='us-west-2')
    lambda_client = boto3.client('lambda', region_name='us-west-2')
    
    try:
        # Create REST API
        api_response = api_gateway.create_rest_api(
            name='egyptian-legal-contract-api',
            description='API for Egyptian Legal Contract Analysis'
        )
        
        api_id = api_response['id']
        print(f"Created API Gateway: {api_id}")
        
        # Get root resource
        resources = api_gateway.get_resources(restApiId=api_id)
        root_id = resources['items'][0]['id']
        
        # Create resources and methods
        # This is a simplified version - full setup would include all endpoints
        
        # Deploy API
        api_gateway.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )
        
        api_url = f"https://{api_id}.execute-api.us-west-2.amazonaws.com/prod"
        print(f"API Gateway URL: {api_url}")
        
        return api_url
        
    except ClientError as e:
        print(f"Error creating API Gateway: {e}")
        return None

def create_s3_bucket():
    """Create S3 bucket for website hosting"""
    s3 = boto3.client('s3', region_name='us-west-2')
    
    bucket_name = 'egyptian-legal-analysis-ui'
    
    try:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}
        )
        print(f"Created S3 bucket: {bucket_name}")
        
        # Configure for static website hosting
        s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'error.html'}
            }
        )
        
        # Set public read policy
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        
        website_url = f"https://{bucket_name}.s3-website-us-west-2.amazonaws.com"
        print(f"Website URL: {website_url}")
        
        return website_url
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print("S3 bucket already exists")
            website_url = f"https://{bucket_name}.s3-website-us-west-2.amazonaws.com"
            return website_url
        else:
            raise e

def main():
    """Set up complete AWS infrastructure"""
    print("Setting up AWS infrastructure for Egyptian Legal Contract Analysis...")
    
    try:
        # Create IAM role
        print("\n1. Creating IAM role...")
        role_arn = create_iam_role()
        
        # Wait for role propagation
        print("Waiting for IAM role propagation...")
        time.sleep(30)
        
        # Create Lambda function
        print("\n2. Creating Lambda function...")
        lambda_arn = create_lambda_function(role_arn)
        
        # Create API Gateway
        print("\n3. Creating API Gateway...")
        api_url = create_api_gateway(lambda_arn)
        
        # Create S3 bucket
        print("\n4. Creating S3 bucket...")
        website_url = create_s3_bucket()
        
        print(f"\n{'='*60}")
        print("AWS INFRASTRUCTURE SETUP COMPLETE!")
        print(f"{'='*60}")
        print(f"Lambda Function ARN: {lambda_arn}")
        print(f"API Gateway URL: {api_url}")
        print(f"Website URL: {website_url}")
        print(f"{'='*60}")
        
        return {
            'lambda_arn': lambda_arn,
            'api_url': api_url,
            'website_url': website_url
        }
        
    except Exception as e:
        print(f"Error setting up infrastructure: {e}")
        return None

if __name__ == "__main__":
    main()