# AWS CCC Lambda Functions

This repository will store the Lambda Functions associated with the AWS Cloud Capability Centre Portal

## Recommended Use

Use `emulambda` to emulate the AWS Lambda API locally. It provides a Python "harness" that you can use to wrap your
function and run/analyze it.

Use Vagrant to run the Lambda functions isolated from your workstation. (VagrantFile in project directory)

## Usage

In the root of this folder;

```
vagrant up
vagrant ssh
cd /vagrant/<lambda+folder>
```

From the function root directory, run:
`emulambda -v example.example_handler example.json`


You should see output similar to the following:
```
Executed example.example_handler
Estimated...
...execution clock time:		 277ms (300ms billing bucket)
...execution peak RSS memory:	 368M (386195456 bytes)
----------------------RESULT----------------------
value1
```

Once tested in Dev & Pre-Prod - The required function should be deployed via the AWS CLI to the Production account.

## Security

NEVER store credentials and sensitive data in the event file.