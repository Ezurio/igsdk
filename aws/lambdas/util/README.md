# Utility Lambda Functions
This folder contains various utility Lambda functions for the Sentrius&trade; IG60.

## General Requirements
All of the pre-configured Greengrass Lambda functions have the following requirements:
* **Greengrass Core**: A Sentrius&trade; IG60 supporting AWS Greengrass
* **AWS Account**: An AWS account that can deploy the following AWS services:
  * Amazon S3
  * Amazon CloudFront
  * Amazon IoT Hub
  * Amazon CloudWatch
* **Language**: All Lambda functions are written in Python (compatible with Python 2.7 and 3.7)

## Deployment
All the Lambda functions have the same process for deployment to AWS.  Refer to the AWS Greengrass Documentation for details on how to [package and deploy a Lambda function](https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html).
1. Create a directory that contains the required AWS SDK folders (`greengrasssdk`, etc.).
2. Copy the contents of the IGSDK directory from [here](../python/igsdk) into a top-level folder named `igsdk`.
3. Add the Python source file for the Lambda function you wish to deploy (e.g, `Reboot.py`) into the top-level folder.
4. Create a ZIP file containing all folders and the top-level lambda.
5. Create a Lambda function in the AWS Console and upload the ZIP file containing the source.

## Common Requirements
All of the supported Lambdas require the following environment variable assignment as part of the Lambda deployment, when deploying the Lambda in a container:

    DBUS_SYSTEM_BUS_ADDRESS=unix:abstract=__dbus_proxy_socket__

## Reboot
Reboot.py implements a Lambda function in Python that enables rebooting of the IG60 remotely, via MQTT message.  Once deployed, Reboot will perform an immediate reboot when any message is received on the following topic:

    device/<nodeid>/reboot

where `nodeid` is the ID of the Greengrass core>.

## ConnectLTE
ConnectLTE.py implements a Lambda function in Python that allows the creation and activation of an LTE connection, modifying the priority of the LTE connection, and updating multipe Wi-Fi configs. Once deployed, ConnectLTE will perform an these functions when  a message is received on the following topics:

    device/<nodeid>/connectLTE
    device/<nodeid>/updateAPS

where `nodeid` is the ID of the Greengrass core>.

## UpdateCore
UpdateCore.py implements a Lambda function in Python that allows downloading and updating a new Greengrass core version.
UpdateCore will perform downloading when message containing "url":"<http link to JSON Descriptor of Greengrass Core tarball>", "username":"<username>" and "password":"<password>" is recieved on topic:

    prov/<nodeid>/startCoreDownload

UpdateCore will perform updating when any message is received on topic:

    prov/<modeid>/performCoreUpdate

where `nodeid` is the ID of the Greengrass core>.

