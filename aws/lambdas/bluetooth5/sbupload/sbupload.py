#########################################################################################
# sbupload.py - smartBASIC Script Upload Lambda
#
# AWS Greengrass Lambda to upload smartBASIC scripts to Sentrius IG60 Bluetooth 5 Gateway
#
# Instructions
# ------------
#
# This Lambda is used to upload one or more compiled smartBASIC scripts to the
# Bluetooth module (BL654) on the IG60.  Use the following procedure to deploy
# smartBASIC script(s) to your Gateway:
#
# 1. Compile all smartBASIC source (.sb) scripts into binary (.uwc) using the
#    XCompiler that matches the smartBASIC firmware loaded into the IG60.  (Contact
#    support for details.)
#
# 2. Create a Python 3.7 Lambda function (as described in the Greengrass documentation)
#    containing this file, the "greengrasssdk" folder (v1.4 or later), and all the
#    compiled modules (.uwc) in the root of the ZIP file.  Then, create a Lambda function
#    by uploading this ZIP and publishing a Lambda version.
#
# 3. Create a deployment for your Greengrass group that contains the sbupload.py
#    Lambda.  You may also need to add topic subscriptions and environment
#    variables to your deployment to allow for synchronization between the script
#    deployment and other Lambdas (see "Synchronization", below).  Your deployment
#    should have the standard Greengrass containerization, and requires a Resource
#    with read/write access to the BL654 serial port device (/dev/ttyS2).  You
#    should configure a long enough timeout to complete the upload operation
#    (at least 60 seconds).
#
# 4. Send the deployment to your Greengrass group.
#
# Syncronization
# --------------
# Because the smartBASIC Script Upload Lambda uses the serial port to control
# the embedded BL654 in the Gateway, you must take care to synchronize this script
# with other Lambda functions (for example, if you have a Lambda function that
# communicates with your smartBASIC script over the serial port).
# The smartBASIC Script Upload Lambda can use messaging over specified topics to
# synchronize the upload with other Lambdas, or with cloud-based services.
#
# Starting Script Upload
# ----------------------
# By default, the smartBASIC Script Deployment Lambda will being uploading immediately
# after its execution begins (either after deployment from the AWS console, or when the
# IG60 reboots).  If you need to control when the script upload begins, you can specify
# the following enviroment variables, which determine which topics the Lambda uses to
# sychronize starting the upload:
#
# SB_UPLOAD_START_REQ_TOPIC - Topic used by the upload Lambda to request status
#   from an external source
#
# SB_UPLOAD_START_RESP_TOPIC: Topic used by the upload Lambda to receive a response
#   from the external source to start the script upload operation
#
# If these variables are set in the Lambda deployment, the smartBASIC Script Upload
# Lambda will synchronize with other Lambdas/services as follows:
#
#   - At startup, the Lambda will send an empty message ({} in JSON) to the "request"
#     topic (to request status from the external source)
#   - The Lambda will await a message (any payload) on the "response" topic before
#     it begins the script upload operation
#
# Detecting Upload Complete
# -------------------------
# The smartBASIC Script Upload Lambda provides indication that the script upload
# operation is complete using messaging over the following topics:
#
# SB_UPLOAD_COMPLETE_REQ_TOPIC - Topic used by an external source to request status
#   of the upload completion (defaults to "sbupload/complete/<NODE_ID>/req", where <NODE_ID>
#   is the AWS node id of the gateway)
#
# SB_UPLOAD_COMPLETE_RESP_TOPIC - Topic used by an external source to receive a
#   response that the script upload operation is complete (defaults to
#   "sbupload/complete/<NODE_ID>/resp", where <NODE_ID> is the AWS node id
#   of the gateway)
#
# The smartBASIC Script Upload Lambda will provide indication of the upload completion
# as follows:
#
#  - Once the upload operation is complete, the upload Lambda will publish an
#    empty message ({} in JSON) to the "response" topic indicating the upload
#    operation is complete
#  - If the upload Lambda receives a message (any payload) on the "request" topic,
#    and the upload operation is completed, the upload Lambd will publish an
#    empty message ({} in JSON) to the "response" topic; otherwise, the request
#    will be ignored.
#
# Using both the "request" and "response" topics eliminates race conditions, where
# either the upload Lambda or the external source may be started before the other
# is ready to publish.
#
# NOTE: In addition to specifying the topics via the environment variables
# described above, you must also add the topic subscriptions to your Greengrass
# deployment (with appropriate source/destinations), otherwise the upload Lambda
# will not be able to send or receive the synchronization messages.
#########################################################################################
import greengrasssdk
import logging
import os
import signal
import sys
import json
import subprocess
import glob

node_id = os.getenv('AWS_IOT_THING_NAME') or 'NO_THING_NAME'
SB_UPLOAD_START_REQ_TOPIC = os.getenv('SB_UPLOAD_START_REQ_TOPIC')
SB_UPLOAD_START_RESP_TOPIC = os.getenv('SB_UPLOAD_START_RESP_TOPIC')
SB_UPLOAD_COMPLETE_REQ_TOPIC = os.getenv('SB_UPLOAD_COMPLETE_REQ_TOPIC') or 'sbupload/complete/{}/req'.format(node_id)
SB_UPLOAD_COMPLETE_RESP_TOPIC = os.getenv('SB_UPLOAD_COMPLETE_RESP_TOPIC') or 'sbupload/complete/{}/resp'.format(node_id)
SB_UPLOAD_DEVICE = os.getenv('SB_UPLOAD_DEVICE') or '/dev/ttyS2'
SB_UPLOAD_BAUDRATE = os.getenv('SB_UPLOAD_BAUDRATE') or '115200'
SB_UPLOAD_EXE = 'btpa_utility.py'

upload_complete = False

def upload_scripts():
    global upload_complete
    l = glob.glob('*.uwc')
    logging.info('Uploading {} compiled scripts.'.format(len(l)))
    for filename in l:
        script_name, ext = os.path.splitext(os.path.basename(filename))
        # Delete any existing file with the same name
        logging.info('Deleting script {}...'.format(script_name))
        subprocess.run([SB_UPLOAD_EXE, SB_UPLOAD_DEVICE, SB_UPLOAD_BAUDRATE, "delete", script_name, "--force"])
        # Upload the file without the '.uwc' extension
        logging.info('Uploading file {} as {}...'.format(filename, script_name))
        subprocess.run([SB_UPLOAD_EXE, SB_UPLOAD_DEVICE, SB_UPLOAD_BAUDRATE, "upload", script_name, filename])
    upload_complete = True
    # Publish upload complete indication
    if SB_UPLOAD_COMPLETE_RESP_TOPIC is not None:
        client.publish(topic = SB_UPLOAD_COMPLETE_RESP_TOPIC, payload = json.dumps({}))

def function_handler(event, context):
    topic = context.client_context.custom['subject']
    if SB_UPLOAD_START_RESP_TOPIC is not None and topic == SB_UPLOAD_START_RESP_TOPIC:
        logging.info('Received startup indication; starting script upload.')
        upload_scripts()
    elif SB_UPLOAD_COMPLETE_REQ_TOPIC is not None and topic == SB_UPLOAD_COMPLETE_REQ_TOPIC:
        if upload_complete:
            logging.info('Acknowledging completion request on {}:'.format(SB_UPLOAD_COMPLETE_RESP_TOPIC))
            client.publish(topic = SB_UPLOAD_COMPLETE_RESP_TOPIC, payload = json.dumps({}))
        else:
            logging.info('Ignoring completion request from {}:'.format(SB_UPLOAD_COMPLETE_REQ_TOPIC))
    else:
        logging.info('Ignoring message on: {}'.format(topic))

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

# Create a greengrass core sdk client
client = greengrasssdk.client('iot-data')

# Use startup synchronization if configured
if SB_UPLOAD_START_REQ_TOPIC is not None:
    logging.info('Requesting startup indication via: {}'.format(SB_UPLOAD_START_REQ_TOPIC))
    client.publish(topic = SB_UPLOAD_START_REQ_TOPIC, payload = json.dumps({}))

if SB_UPLOAD_START_RESP_TOPIC is None:
    logging.info('Starting script upload.')
    upload_scripts()
else:
    logging.info('Awaiting startup indication from: {}'.format(SB_UPLOAD_START_RESP_TOPIC))
