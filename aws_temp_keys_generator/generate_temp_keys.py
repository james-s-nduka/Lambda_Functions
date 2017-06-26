# pylint: disable=import-error
"""LAMBDA FUNCTION"""
#!/usr/bin/python

import base64
from urlparse import urlparse, urlunparse
import xml.etree.ElementTree as ET
import json
import re
import logging
from bs4 import BeautifulSoup
import boto3
import requests

##########################################################################
# Variables

# region: The default AWS region that this script will connect
# to for all API calls
REGION = 'eu-west-1'

# SSL certificate verification: Whether or not strict certificate
# verification is done, False should only be used for dev/test
SSLVERIFICATION = True

# idpentryurl: The initial url that starts the authentication process.
IDPENTRYURL = \
    'https://sts.global.client.org/adfs/ls/IdpInitiatedSignOn.aspx?loginToRp=urn:amazon:webservices'


def process_creds(user, passwd):
    """Process the user credentials and return a DOC response client adfs site"""
    # Initiate session handle
    session = requests.Session()
    # Programmatically get the SAML assertion
    formresponse = session.get(IDPENTRYURL, verify=SSLVERIFICATION)
    # Capture the idpauthformsubmiturl, which is the final url after all the 302s
    idpauthformsubmiturl = formresponse.url

    # Parse the response and extract all the necessary values
    # in order to build a dictionary of all of the form values the IdP expects

    formsoup = BeautifulSoup(formresponse.text, "html.parser")

    # Construct the POST payload with user credentials
    payload = {u'UserName': user, u'Kmsi': \
    u'true', u'AuthMethod': '', u'Password': passwd}

    # Some IdPs don't explicitly set a form action, but if one is set we should
    # build the idpauthformsubmiturl by combining the scheme and hostname
    # from the entry url with the form action target
    # If the action tag doesn't exist, we just stick with the
    # idpauthformsubmiturl above
    for inputtag in formsoup.find_all(re.compile('(FORM|form)')):
        action = inputtag.get('action')
        loginid = inputtag.get('id')
        if action and loginid == "loginForm":
            parsedurl = urlparse(IDPENTRYURL)
            idpauthformsubmiturl = parsedurl.scheme + "://" + parsedurl.netloc + action

    # Performs the submission of the IdP login form with the above post data
    response = session.post(idpauthformsubmiturl, data=payload, verify=SSLVERIFICATION)
    # Return the response to requesting functions
    return response


def purge_creds():
    """Overwrite and delete the credential variables, just for safety"""
    username = '##############################################'
    password = '##############################################'
    del username
    del password
    return True

def generate_tmp_keys(response, role, account):
    """The main function which prints out the temp AWS details for the user"""
    # Decode the response and extract the SAML assertion
    soup = BeautifulSoup(response.text, "html.parser")
    assertion = ''

    # Look for the SAMLResponse attribute of the input tag (determined by
    # analyzing the debug print lines above)
    for inputtag in soup.find_all('input'):
        if inputtag.get('name') == 'SAMLResponse':
            assertion = inputtag.get('value')

    # error handling required for production use.
    if assertion == '':
        raise Exception('Response did not contain a valid SAML assertion.' + \
         ' Check if payload contains correct details')

    # Parse the returned assertion and extract the authorized roles
    awsroles = []
    root = ET.fromstring(base64.b64decode(assertion))
    for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
        if saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role':
            for saml2attributevalue in \
            saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
                awsroles.append(saml2attributevalue.text)

    # Note the format of the attribute value should be role_arn,principal_arn
    # but lots of blogs list it as principal_arn,role_arn so let's reverse
    # them if needed
    for awsrole in awsroles:
        chunks = awsrole.split(',')
        if'saml-provider' in chunks[0]:
            newawsrole = chunks[1] + ',' + chunks[0]
            index = awsroles.index(awsrole)
            awsroles.insert(index, newawsrole)
            awsroles.remove(awsrole)

    # If I have more than one role, ask the user which one they want,
    # otherwise just proceed
    if len(awsroles) > 1:
        # Declare the role_arn and principal arn
        role_arn = "arn:aws:iam::" + account + ":role/" + role
        principal_arn = "arn:aws:iam::" + account + ":saml-provider/ClientADFS"
        validroles = []
        # Build the list of available roles to the stakeholder
        i = 0
        for awsrole in awsroles:
            validroles.append(awsrole.split(',')[0])
            i += 1
        # Test if the role is valid and available
        if role_arn in validroles:
            logging.info("The Role and Account provided is valid")
        else:
            # Raise an exception back to Lambda
            raise Exception("There was an issue with the role or account provided")
    else:
        raise Exception("There are no roles available for the user to assume")

    # Use the assertion to get an AWS STS token using Assume Role with SAML
    conn = boto3.client('sts', region_name=REGION)

    token = conn.assume_role_with_saml(
        RoleArn=role_arn,
        PrincipalArn=principal_arn,
        SAMLAssertion=assertion
    )

    # Return the AWS Access, Secret, Session Token along with the expiration
    creds = {}
    creds['AccessKey'] = token['Credentials']['AccessKeyId']
    creds['SecretKey'] = token['Credentials']['SecretAccessKey']
    creds['SessionToken'] = token['Credentials']['SessionToken']
    # Return as json
    jsondump = json.dumps(creds, sort_keys=True, indent=4)
    return jsondump

def lambda_handler(event, context):
    """Mandatory lambda_handler function"""
    # A list of the valid roles to choose from
    validroles = ['client-app-tester', 'client-app-productowner', \
    'client-app-developer', 'client-app-admin']
    # We perform a test to see if the provided role is valid
    if event['Role'] in validroles:
        uname = event['Username'] + "@global.client.org"
        pword = event['Password']
        role = event['Role']
        account = event['AccountID']
        # Pass processed payload for def which prints temp AWS keys
        hook_session = process_creds(uname, pword)
        purge_creds()
        return generate_tmp_keys(hook_session, role, account)
    else:
        logging.error("The role '" + event['Role'] + "' is not a valid role")
