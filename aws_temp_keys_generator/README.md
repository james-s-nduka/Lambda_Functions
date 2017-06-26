# ADFS SAML AWS Access Token Generation

A Lambda function that returns a temporary AWS access key, AWS secret key & AWS session token.
The function has been run on Python 2.7 and is pointed at the Client ADFS.

## Pre-requisites 

A payload with the following data;

```
{
  "Username": "value1",
  "Password": "value2",
  "Role": "client-app-admin",
  "AccountID": "2223344422"
}

```

##  Testing
The event.json will act as the test payload which is consumed by the function when running *emulambda*.
Assuming all goes well, you will be presented with your temporary keys presented back to the console.

e.g.
`emulambda generate_temp_keys.lambda_handler event.json`

## Versioning & Aliases

In order to keep different versions of the same function we can *Publish a new version* via the command line. We should only change "PROD" alias to a version that has been tested thoroughly. DEV can be pointed to $LATEST version.

#### Creating a new Alias
```
aws lambda create-alias \
--function-name generate_temp_keys \
--decription "Sample alias" \
--function-version "\$LATEST" \
--name DEV
```

#### Updating a version
```
aws lambda update-function-code \
--function-name generate_temp_keys
--zip-file fileb://$package_file
```

#### Publishing the version
```
aws lambda publish-version \
--function-name generate_temp_keys
```

#### Update Alias
```
aws lambda update-alias \
--function-name generate_temp_keys
--function-version 2
--name PROD
```

## Deployment

Zip the content of the project-dir directory, which is the deployment package.

##### Important
Zip the directory content, not the directory. The contents of the Zip file are available as the current working directory of the Lambda function. For example: /project-dir/codefile.py/lib/yourlibraries

From the command shell run the following;
```
function_name="generate_temp_keys"
handler_name="generate_temp_keys.lambda_handler"
package_file=generate_temp_keys.zip
runtime=python2.7
aws lambda create-function \
  --function-name $function_name \
  --handler $handler_name \
  --runtime $runtime \
  --memory 512 \
  --timeout 60 \
  --description "The function that returns a temporary AWS ACCESS KEY, AWS SECRET KEY & AWS SESSION TOKEN" \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/$role \
  --zip-file fileb://$package_file
  --publish 
  --region eu-west-1
```

## Error Logs

If a client specifies the RequestResponse invocation type (that is, synchronous execution), it returns the result to the client that made the invoke call.

For example, the console always use the RequestResponse invocation type, so the console will display the error in the Execution result section as shown:

![Console Exception](https://github.dev.global.client.org/AWS-CCC/Lambda_Functions/blob/refactoring/aws_temp_keys_generator/exception-shown-in-console.png)

The same information is also sent to CloudWatch and the Log output section shows the same logs.

![CloudWatch Exception](https://github.dev.global.client.org/AWS-CCC/Lambda_Functions/blob/refactoring/aws_temp_keys_generator/exception-shown-in-console20.png)

## CloudWatch Alarm

To setup an alarm when the Lambda fails go to your CloudWatch Console:
* Click "Alarms" at the left, and then Create Alarm.
* Click "Lambda Metrics".
* Look for your Lambda name in the listing, and click on the checkbox for the row where the metric name is "Errors". Click "Next".
* Enter a name and description for this alarm.
* Setup the alarm to be triggered whenever "Errors" is above 0, for 1 consecutive period(s).
* Select 1 minute (or the amount of minutes that's reasonable for your use case) in the "Period" dropdown.
* In the "Notification" box, click the Select a notification list dropdown and select the created SNS endpoint.
* Click "Create Alarm".

#### PyLint Rating 
```
Global evaluation
-----------------
Your code has been rated at 9.55/10
```