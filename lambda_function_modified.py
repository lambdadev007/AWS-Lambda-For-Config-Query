import json
import boto3
import logging
import os
import time
import csv



# This is the client to access AWS Config
configClient = boto3.client('config')

account_id = os.getenv("account_id")
region = os.getenv("region")
filename = 'Results-'+ str(time.time()) +'.csv'
filepath = '/tmp/' + filename
csv_output = open(filepath, 'w')
cswriter = csv.writer(csv_output)

aggregator_name =os.getenv("aggregator_name")
expression="SELECT resourceId, resourceType, configuration.instanceType, configuration.placement.tenancy, configuration.imageId, availabilityZone WHERE resourceType = 'AWS::EC2::Instance'"

  # create default account owner/application table
default_owner = {
    "375160352598": ["roopa murli", "shared master payer"],
    "375160352598": ["mural murli", "shared master prod"],
}
  
  # Roll my own pagination -thank you AWS
def get_pages(resource_call):
    results = []
    results = resource_call['Results']
    next_token = resource_call.get('NextToken', None)
    return results, next_token
      
  # This is the client to access AWS Config
configClient = boto3.client('config')
output = []
  
def lambda_handler(event, context):    
    # Query for the AWS Config discovery
    responses = config_client.select_aggregate_resource_config(
        Expression=expression,
        ConfigurationAggregatorName=aggregator_name
        Limit=100,
    next_token = responses['NextToken']
     
    while next_token is not None:   
        resources_call = config_client.select_aggregate_resource_config(
            Expression=expression,
            ConfigurationAggregatorName=aggregator_name
            Limit=100,
        current_batch, next_token = get_pages(resource_call)
        output.extend(current_batch)
          
    header = ["unique_id", "resource_type", "owner", "application", "ip_address", "account_id", "state"]  
    cswriter.writerow(header)  
    for json_string in output:
        aws_item = json.loads(json_string)
        account = aws_item['accountId']
        unique_id = aws_item['resourceId']
        resource_type = aws_item['resourceType']
        owner = None
        application  = None
        ip_address = "Not Applicable"
        state =  "Not Applicable"
         # Tag special processing
        # Attempt to find a value if the resource has tags
        if aws_item['tags']:
            for tag in aws_item['tags']:
                  # Top entries will get over-written byu subsequest ones
                  # Fix these once people start getting standardized on the tag names
                if tag ['key'] == 'department_name':
                    owner = tag['value']
                if tag ['key'] == 'BusinessOwner':
                    owner = tag['value']   
                if tag ['key'] == 'department_owner':
                    owner = tag['value'] 
                if tag ['key'] == Application':
                    application = tag['value']  
         # If no owner then lookup default value from account table
        if owner is None:
            owner = default_owner.get(account)[0]
        # If no application then lookup default value from account table
        if application is None:
            application= default_owner.get(account)[1]    
           # State and IP special processing
        if aws_item['resourceType'] == 'AWS::EC2::Instance':
            ip_address = aws_item['configuration']['privateIpAddress']
            state = aws_item['configuration']['state']['name']
        if aws_item['resourceType'] == 'AWS::EC2::Volume':
            state = aws_item['configuration']['state']['value']
        if aws_item['resourceType'] == 'AWS::EC2::VPC':
            state = aws_item['configuration']['state']['value']        
        if aws_item['resourceType'] == 'AWS::Lambda::Function':
            state = aws_item['configuration']['state']['value']  
        row = [imoqie_id, resource-type, owner, application, ip_address, account, state]  
        csvwriter.writerow(row)
           
     save_results(responses)  
     
def save_results(responses):
    # This is the client to access S3
    s3_client = boto3.client('s3')
    # This is the name for the S3 bucket
    s3_client = boto3.client('s3')
    s3_bucket = f'security-config-query-results-{region}-{account}'
    try:
        s3Client.upload_file(filepath, Bucket=s3Bucket, Key=filename,
                              ExtraArgs={'ACL': 'bucket-owner-full-control'})
    except Exception as e:
        print(e)
    else:
        print("Json object has been added to S3")
                             