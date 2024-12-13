#########################################################################################
# fwloader.py - BL654 Firmware Loader Lambda
#
# AWS Greengrass Lambda to load firmware to Sentrius IG60 Bluetooth 5 Gateway BL654 co-processor
#
# Instructions
# ------------
#
# This Lambda is used to load a firmware image to the Bluetooth module (BL654) on the IG60.
# Use the following procedure to load firmware to your Gateway:
#
# 1. Generate a BL654 bootloader-compatible firmware update package (.UWF) for the
#    BL654 co-processor. (Contact support for details.)
#
# 2. Create a ZIP file containing this file, the "greengrasssdk" folder
#    (v1.4 or later), and a single firmware update image (.UWF).
#    Then, create a Lambda function and upload this ZIP as the contents,
#    and publish a Lambda version.
#
# 3. Create a deployment for your Greengrass group that contains the fwloader.py
#    Lambda.  You may also need to add topic subscriptions and environment
#    variables to your deployment to allow for synchronization between the firmware
#    deployment and other Lambdas (see "Synchronization", below).  Your deployment
#    should have the standard Greengrass containerization, and requires a Resource
#    with read/write access to the BL654 serial port device (/dev/ttyS2).  You
#    should configure a long enough timeout to complete the firmware programming
#    (at least 120 seconds).  Your deployment must also contain the following
#    environment variable:
#
#        DBUS_SYSTEM_BUS_ADDRESS=unix:abstract=__dbus_proxy_socket__
#
# 4. Send the deployment to your Greengrass group.
#
# Syncronization
# --------------
# Because the Firmware Loader Lambda uses the serial port to control
# the embedded BL654 in the Gateway, you must take care to synchronize this script
# with other Lambda functions (for example, if you have a Lambda function that
# communicates with your smartBASIC script over the serial port).
# The Firmware Loader Lambda can use messaging over specified topics to
# synchronize the firmware load with other Lambdas, or with cloud-based services.
#
# Starting Firmware Loading
# ----------------------
# By default, the Firmware Loader Lambda will being loading the firmware immediately
# after its execution begins (either after deployment from the AWS console, or when the
# IG60 reboots).  If you need to control when the firmware loading begins, you can specify
# the following enviroment variables, which determine which topics the Lambda uses to
# sychronize starting the firmware loader:
#
# FW_LOADER_START_REQ_TOPIC - Topic used by the Lambda to request status
#   from an external source
#
# FW_LOADER_START_RESP_TOPIC: Topic used by the Lambda to receive a response
#   from the external source to start the firmare load operation
#
# If these variables are set in the Lambda deployment, the Firmware Loader Lambda
# Lambda will synchronize with other Lambdas/services as follows:
#
#   - At startup, the Lambda will send an empty message ({} in JSON) to the "request"
#     topic (to request status from the external source)
#   - The Lambda will await a message (any payload) on the "response" topic before
#     it begins the firmware load operation
#
# Detecting Firmware Load Complete
# -------------------------
# The Firmware Loaer Lambda provides indication that the firmware loading
# operation is complete using messaging over the following topics:
#
# FW_LOADER_COMPLETE_REQ_TOPIC - Topic used by an external source to request status
#   of the load completion (defaults to "fwloader/complete/<NODE_ID>/req", where <NODE_ID>
#   is the AWS node id of the gateway)
#
# FW_LOADER_COMPLETE_RESP_TOPIC - Topic used by an external source to receive a
#   response that the firmware load operation is complete (defaults to
#   "fwloader/complete/<NODE_ID>/resp", where <NODE_ID> is the AWS node id
#   of the gateway)
#
# The Firmware Loader Lambda will provide indication of the firmware load completion
# as follows:
#
#  - Once the operation is complete, the Lambda will publish an
#    empty message ({} in JSON) to the "response" topic indicating the
#    operation is complete
#  - If the Lambda receives a message (any payload) on the "request" topic,
#    and the operation is completed, the Lambda will publish an
#    empty message ({} in JSON) to the "response" topic; otherwise, the request
#    will be ignored.
#
# Using both the "request" and "response" topics eliminates race conditions, where
# either the Firmware Loader Lambda or the external source may be started before the other
# is ready to publish.
#
# NOTE: In addition to specifying the topics via the environment variables
# described above, you must also add the topic subscriptions to your Greengrass
# deployment (with appropriate source/destinations), otherwise the Lambda
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
FW_LOADER_START_REQ_TOPIC = os.getenv('FW_LOADER_START_REQ_TOPIC')
FW_LOADER_START_RESP_TOPIC = os.getenv('FW_LOADER_START_RESP_TOPIC')
FW_LOADER_COMPLETE_REQ_TOPIC = os.getenv('FW_LOADER_COMPLETE_REQ_TOPIC') or 'fwloader/complete/{}/req'.format(node_id)
FW_LOADER_COMPLETE_RESP_TOPIC = os.getenv('FW_LOADER_COMPLETE_RESP_TOPIC') or 'fwloader/complete/{}/resp'.format(node_id)
FW_LOADER_DEVICE = os.getenv('FW_LOADER_DEVICE') or '/dev/ttyS2'
FW_LOADER_BAUDRATE = os.getenv('FW_LOADER_BAUDRATE') or '115200'
FW_LOADER_EXE = 'btpa_firmware_loader.py'

fwload_complete = False

def load_firmware():
    global fwload_complete
    file = glob.glob('*.uwf')
    if len(file) != 1:
        logging.error('Invalid deployment, must contain exactly one firmware image!')
        return
    logging.info('Loading firmware from: {}'.format(file[0]))
    subprocess.run([FW_LOADER_EXE, FW_LOADER_DEVICE, FW_LOADER_BAUDRATE, file[0], "IG60"])
    fwload_complete = True
    # Publish upload complete indication
    client.publish(topic = FW_LOADER_COMPLETE_RESP_TOPIC, payload = json.dumps({}))

def function_handler(event, context):
    topic = context.client_context.custom['subject']
    if FW_LOADER_START_RESP_TOPIC is not None and topic == FW_LOADER_START_RESP_TOPIC:
        logging.info('Received startup indication; starting firmware load.')
        load_firmware()
    elif topic == FW_LOADER_COMPLETE_REQ_TOPIC:
        if fwload_complete:
            logging.info('Acknowledging completion request on {}:'.format(FW_LOADER_COMPLETE_RESP_TOPIC))
            client.publish(topic = FW_LOADER_COMPLETE_RESP_TOPIC, payload = json.dumps({}))
        else:
            logging.info('Ignoring completion request from {}:'.format(FW_LOADER_COMPLETE_REQ_TOPIC))
    else:
        logging.info('Ignoring message on: {}'.format(topic))

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

# Create a greengrass core sdk client
client = greengrasssdk.client('iot-data')

# Use startup synchronization if configured
if FW_LOADER_START_REQ_TOPIC is not None:
    logging.info('Requesting startup indication via: {}'.format(FW_LOADER_START_REQ_TOPIC))
    client.publish(topic = FW_LOADER_START_REQ_TOPIC, payload = json.dumps({}))

if FW_LOADER_START_RESP_TOPIC is None:
    logging.info('Starting firmware load.')
    load_firmware()
else:
    logging.info('Awaiting startup indication from: {}'.format(FW_LOADER_START_RESP_TOPIC))
