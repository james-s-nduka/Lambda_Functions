# Integrate Splunk

In order for the Splunk Add-on for Amazon Web Services to access the data in a Amazon Web Services account, you must assign one or more AWS accounts to an IAM role with the permissions required by those services.

More details here; https://docs.splunk.com/Documentation/AddOns/released/AWS/ConfigureAWSpermissions

The Heavy Forwarder instances will need an access policy as part of its attached role in order to do the "assuming"

```
{
  "Version": "2012-10-17",
  "Statement": [{
      "Action": ["sts:AssumeRole"],
      "Resource": ["arn:aws:iam::111111111111:role/splunk-read"],
      "Effect": "Allow"
    }
  ]
}

```

This Lambda function creates a read role in a stakeholder's account that can be assumed by the Splunk Heavy Forwarders in the Monitoring AWS account.


## Pre-requisites 
A payload with the following data before invoking;

```
{
  "AccessKey": "XXXX",
  "SecretKey": "xxx",
  "SessionToken": "xxxxx",
  "AccountID": "8888888888"
}
```

## Flow Diagram
![Flow Diagram](https://github.dev.global.tesco.org/AWS-CCC/lambda-functions/blob/master/integrate_splunk/flow-diagram.png)

##  Testing
The event.json will act as the test payload which is consumed by the function when running *emulambda*.
Assuming all goes well, you will be presented with your temporary keys presented back to the console.

e.g.
`emulambda integrate_splunk.lambda_handler event.json`

## Versioning & Aliases

In order to keep different versions of the same function we can *Publish a new version* via the command line. We should only change "PROD" alias to a version that has been tested thoroughly. DEV can be pointed to $LATEST version.

#### Creating a new Alias
```
aws lambda create-alias \
--function-name integrate_splunk \
--decription "Sample alias" \
--function-version "\$LATEST" \
--name DEV
```

#### Updating a version
```
aws lambda update-function-code \
--function-name integrate_splunk
--zip-file fileb://$package_file
```

#### Publishing the version
```
aws lambda publish-version \
--function-name integrate_splunk
```

#### Update Alias
```
aws lambda update-alias \
--function-name integrate_splunk
--function-version 2
--name PROD
```

## Policy
Here are the privileges the newly created Splunk read role has;
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sqs:GetQueueAttributes",
                "sqs:ListQueues",
                "sqs:ReceiveMessage",
                "sqs:GetQueueUrl",
                "sqs:SendMessage",
                "s3:ListBucket",
                "s3:GetObject",
                "s3:GetBucketLocation",
                "s3:ListAllMyBuckets",
                "config:DeliverConfigSnapshot",
                "config:DescribeConfigRules",
                "config:DescribeConfigRuleEvaluationStatus",
                "config:GetComplianceDetailsByConfigRule",
                "config:GetComplianceSummaryByConfigRule",
                "iam:GetUser",
                "autoscaling:Describe*",
                "cloudwatch:Describe*",
                "cloudwatch:Get*",
                "cloudwatch:List*",
                "sns:Get*",
                "sns:List*",
                "sns:Publish",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:GetLogEvents",
                "ec2:DescribeInstances",
                "ec2:DescribeReservedInstances",
                "ec2:DescribeSnapshots",
                "ec2:DescribeRegions",
                "ec2:DescribeKeyPairs",
                "ec2:DescribeNetworkAcls",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSubnets",
                "ec2:DescribeVolumes",
                "ec2:DescribeVpcs",
                "ec2:DescribeImages",
                "ec2:DescribeAddresses",
                "lambda:ListFunctions",
                "rds:DescribeDBInstances",
                "cloudfront:ListDistributions",
                "elasticloadbalancing:DescribeLoadBalancers",
                "elasticloadbalancing:DescribeInstanceHealth",
                "inspector:Describe*",
                "inspector:List*"
            ],
            "Resource": "*"
        }
    ]
}
```
## Deployment

Zip the content of the project-dir directory, which is the deployment package.

##### Important
Zip the directory content, not the directory. The contents of the Zip file are available as the current working directory of the Lambda function. For example: /project-dir/codefile.py/lib/yourlibraries

From the command shell run the following;
```
function_name="integrate_splunk"
handler_name="integrate_splunk.lambda_handler"
package_file=integrate_splunk.zip
runtime=python2.7
aws lambda create-function \
  --function-name $function_name \
  --handler $handler_name \
  --runtime $runtime \
  --memory 512 \
  --timeout 60 \
  --description "The function that returns a temporary AWS ACCESS KEY, AWS SECRET KEY & AWS SESSION TOKEN" \
  --environment Variables={SPLUNK_AWS_ACCOUNT=22222222222, ROLE_NAME=tesco-splunk-testing-role} \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/$role \
  --zip-file fileb://$package_file
  --region eu-west-1
```

## Error Logs

If a client specifies the RequestResponse invocation type (that is, synchronous execution), it returns the result to the client that made the invoke call.

For example, the console always use the RequestResponse invocation type, so the console will display the error in the Execution result section as shown:

![Console Exception](https://github.dev.global.tesco.org/AWS-CCC/Lambda_Functions/blob/master/aws_temp_keys_generator/exception-shown-in-console.png)

The same information is also sent to CloudWatch and the Log output section shows the same logs.

![CloudWatch Exception](https://github.dev.global.tesco.org/AWS-CCC/Lambda_Functions/blob/master/aws_temp_keys_generator/exception-shown-in-console20.png)

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
Your code has been rated at 9.83/10
```
