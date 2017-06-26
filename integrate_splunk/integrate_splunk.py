# pylint: disable=import-error
"""LAMBDA FUNCTION"""

import json
import sys
import os
import logging
import boto3
from botocore.exceptions import ClientError

# These global variables will be set as the function env variables
# if not set, use default coded values
SPLUNK_ACC = os.environ.get("SPLUNK_AWS_ACCOUNT")
ROLE_NAME = os.environ.get("ROLE_NAME", "client-readsplunk-role")
BUCKET = os.environ.get("S3_BUCKET", "client-roles-arns")
POLICYNAME = 'client-splunk-read-all'

# Create the Client Read All Policy in the target account
def create_policy(access, secret, session):
    """definition for creating the policy"""
    # Use the aws creds of the stakeholder making the request
    iam = boto3.client(
        'iam',
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        aws_session_token=session
    )

    # Obtain a list of all the policies in order to check id already exists
    listofpolicies = iam.list_policies()
    for policy in listofpolicies['Policies']:
        # Now check if it exists already
        # UPDATE TO CONST defined & CHANGE TO client-read-all ROLE
        if policy['PolicyName'] == POLICYNAME:
            logging.warning("The client-splunk-policy and role already exists")
            sys.exit(0)

    # Use the policy outlined in the json file provided
    policydoc = json.load(open('client-splunk-read.json'))
    response = iam.create_policy(PolicyName=POLICYNAME, \
    PolicyDocument=json.dumps(policydoc), \
    Description='The policy attached to the Splunk read all role')

    # Return the Policy arn used to attach it to the role
    logging.warning("The Policy " + response['Policy']['Arn'] + " has been created")
    return response['Policy']['Arn']

# Create the Client Read Role in the target account
def create_role(access, secret, session, policy):
    """definition for creating the role"""
    iam = boto3.client(
        'iam',
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        aws_session_token=session
    )

    # Obtain a list of all the roles in order to check existence
    listofroles = iam.list_roles()
    for role in listofroles['Roles']:
        # Now check if it exists already, exit if does
        if role['RoleName'] == ROLE_NAME:
            logging.warning("The client-splunk-read role already exists")
            sys.exit(0)

    # Obtain the contents of the assume policy JSON document
    assumejson = json.load(open('assumepolicy.json'))
    # Convert json to string
    assumedoc = json.dumps(assumejson)
    # Replace the splunk account placeholder with account number
    updateddoc = assumedoc.replace("<SPLUNK_ACCOUNT>", SPLUNK_ACC)

    # Create the Role with yielded values
    response = iam.create_role(RoleName=ROLE_NAME, \
    AssumeRolePolicyDocument=updateddoc)

    # Attach the created role to the Policy
    iam.attach_role_policy(RoleName=ROLE_NAME, \
    PolicyArn=policy)
    logging.warning('\n----------------------------------------------------------------')
    logging.warning("The Role " + response['Role']['Arn'] + " has been created")
    return response['Role']['Arn']

# Generate File with the new Role ARN and push to S3
def log_new_account(rolearn, account):
    """Send the newly integrated acc details to s3"""
    storage = boto3.client('s3')
    newfile = open('/tmp/' + account, "wb+")
    newfile.write(rolearn)
    newfile.close()
    # obtain the bucket and upload file
    storage.upload_file(newfile.name, BUCKET, account)
    logging.warning("\nA new entry has been added in " + BUCKET)
    return True

# The handler function kicked off from a lambda event source
def lambda_handler(event, context):
    """Mandatory lambda_handler function"""
    accesskey = event['AccessKey']
    secretkey = event['SecretKey']
    sessiontoken = event['SessionToken']
    account = event['AccountID']
    role_arn = ""
    # Handle any client errors raised when creating policy + role
    try:
        # First create the policy in the target account
        policy_arn = create_policy(accesskey, secretkey, sessiontoken)
        role_arn = create_role(accesskey, secretkey, sessiontoken, policy_arn)
    except ClientError as iamerr:
        return 'IAM ERROR: Please ensure the event payload has correct admin ' + \
        'Access & Secret Keys and Token: \n' + iamerr.response['Error']['Message']
    # Handle any client errors raised when attempting to upload to S3
    try:
        # Attempt to upload new arn details to S3
        log_new_account(role_arn, account)
    except ClientError as bucketerr:
        return 'S3 ERROR: Problem uploading to S3. Check permissions: ' + \
        bucketerr.response['Error']['Message']

    return 'Successfully integratred ' + account + ' with Splunk'
