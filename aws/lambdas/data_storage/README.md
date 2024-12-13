# Text File Data Storage Lambda Function
This folder contains the AWS Greeengrass Lambda function for data storage that can be deployed the Greengrass core running on the Sentrius&trade; IG60.

### TextFileStorageLambda.py
This Lambda function receives Modbus messages (in the form as JSON) and writes all messages received to a CSV-delimited text file.

The output file is "managed", meaning the following:

* The output file size is limited, and new files are created to manage file size
* The output filenames are timestamped
* The output files are written to the SD card storage, when available
* If no SD card is available, the data is written to internal storage
* Any data written to internal storage will be copied to the SD card when it becomes available
* The storage function will automatically swith to writing to internal storage when an "SD card swap" operation is triggered via the BLE Mobile Application

**IMPORTANT**: You must deploy the Text File Storage Lambda function with the Greengrass containerization DISABLED.

## JSON Message Format
All Modbus messages that are handled by the Lambda function are translated from JSON, in a common format.  The JSON message format will have required and optional elements, depending on the requirements of the Lambda function.

All messages **must** contain an `address` element, which is an unsigned integer that represents the 8-bit Modbus slave address.

All messages **must** contain a `function` element, which is an unsigned integer that represents the 8-bit Modbus function code.

All messages **must** contain a `received` element, which is an unsigned integer that represents the message receive time as milliseconds since the Epoch (1-1-1970).

Messages **may** contain a `data` element, which is an array of unsigned integers that represent the Modbus data payload.  Messages that do not contain a data payload can omit this element.

An example of a JSON message representing a single Modbus message is as follows:

    {
       "address" : 16,
       "function" : 3,
       "data" : [ 0, 107, 0, 3 ],
       "received": 1568921373505
    }

This represents a Modbus master request to read 3 holding registers, beginning at address 107, from the slave with device ID 16.

**NOTE:** Modbus frames on the serial bus (both ASCII and RTU) contains a count of data bytes; this is not directly encoded in the JSON message, but can be inferred from the `data` element array length.

## Environment Variables
The Data Storage Lambda function has parameters to control its function that are based on environment variables (specified in the Greengrass deployment).

`UNIT_NAME`: specifies a unit name for the storage; the default is "modbus". You should specify unique unit names when deploying multiple copies of this Lambda function.

`BASE_NAME` specifies the output file base name; the default is "modbus".

`FILE_EXT` specifies the output file extension; the default is ".csv".

`MAX_FILE_SIZE` specifies the maximum file size for the managed files, in bytes. The default is 64MB.

## Message Topics
The Text File Storage Lambda receives and stores Modbus messages (in the specified JSON format) on the following topic wildcard:

    modbus/msg/#

You should configure the Lambda deployment with subscriptions that allow the Lambda to receive all messages you want to be stored (either from other Lambdas, such as the Modbus Lambdas, or from the IoT cloud service).

The Text File Storage Lambda also receives and responds to requests for the status of the storage on the IG60, on the following topic:

    storage/status/<node_id>/request

where `node_id` is the name of the Greengrass core deployed to the Sentrius IG60.  (The payload of the request message is not used, and can be empty.)  The Lambda will publish the storage status response on the following topic:

    storage/status/<node_id>/response

