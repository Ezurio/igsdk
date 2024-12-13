# AWS Support for Sentrius&trade; IG60
This folder contains support for Amazon Web Services (AWS) for the Sentrius&trade; IG60.

## Contents
`lambdas` - Contains pre-configured Lambda functions for AWS Greengrass

## General Requirements
All of the pre-configured Greengrass Lambda functions have the following requirements:
* **Greengrass Core**: A Sentrius&trade; IG60 supporting AWS Greengrass
* **AWS Account**: An AWS account that can deploy the following AWS services:
  * Amazon S3
  * Amazon CloudFront
  * Amazon IoT Hub
  * Amazon CloudWatch
* **Language**: All Lambda functions are written in Python 2.7

## Deployment
All the Lambda functions have the same process for deployment to AWS.  Refer to the AWS Greengrass Documentation for details on how to [package and deploy a Lambda function](https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html).
1. Create a directory that contains the required AWS SDK folders (`greengrasssdk`, etc.).
2. Copy the contents of the IGSDK directory from [here](../python/igsdk) into a top-level folder named `igsdk`.
3. Add the Python source file for the Lambda function you wish to deploy (e.g, `ModbusTraceLambda.py`) into the top-level folder.
4. Create a ZIP file containing all folders and the top-level lambda.
5. Create a Lambda function in the AWS Console and upload the ZIP file containing the source.
