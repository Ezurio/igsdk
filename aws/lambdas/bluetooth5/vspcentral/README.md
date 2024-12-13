# VSP (BLE GATT) Sensor Demonstration
This folder contains a demonstration of using a BLE GATT connection between
the Sentrius IG60 and a remote (simulated) sensor device, using a "virtual serial
port" (VSP) connection.

## Introduction
This demonstration shows how you can use the **Sentrius IG60 with Bluetooth 5** to transport data end-to-end, from a Bluetooth 5 end device (such as a sensor) through the Sentrius IG60 (acting as a Bluetooth gateway) and into the AWS IoT cloud, as well as manage the remote end-devices by sending control messages down to the device (in this example, to manage the reporting period of the device).

### Key Concepts
The following are some key concepts and definitions of terms used throughout this demo:

**GATT**: GATT (the *G*eneric *ATT*tribute Profile) is a connection-oriented method of exchanging data between two Bluetooth devices.  GATT defines two roles, the *central* role for devices that initiate the connection (and can have multiple connections active), and the *peripheral* role which responds to the connection (and can only be connected to a single central device).

**VSP**: "Virtual Serial Port", meaning that data in both directions (to and from the Bluetooth end device) is transported in a stream of data (like a serial port), but over the Bluetooth 5 connection.  This is accomplished using two (2) BLE GATT characteristics, one for each direction between the central and peripheral devices.

**JSON**: JSON is an data object serialization method that encodes objects into strings and conversely decodes strings into object data.  In this demonstration, all the data and control messages passed over the VSP connection are encoded as JSON.

**smartBASIC**: Sentrius IG60 with Bluetooth 5, and the BL654 USB dongle both support the smartBASIC programming language.  Refer to the [BL654 product page](https://www.lairdconnect.com/wireless-modules/bluetooth-modules/bluetooth-5-modules/bl654-series-bluetooth-module-nfc) for more details and support information regarding smartBASIC.

### Component Overview

#### BL654 USB Dongle + VSP Peripheral Role smartBASIC Application
The VSP Peripheral Role smartBASIC application `peripheral.sb` runs on the external BL654 USB dongle.  This application acts as the BLE GATT peripheral role, and accepts incoming connections.  Once connected, this application forwards messages in both directions between the USB serial port on the development PC and the BLE central device (the Sentrius IG60).

#### VSP Peripheral Test Script
The VSP peripheral test script `vsp_peripheral.py` simulates the BLE sensor.  It communicates over the development PC USB serial port with the BL654 USB dongle, and sends simulated sensor data as JSON messages to the peripheral smartBASIC application.  It also receives control messages via the peripheral application, and modifies the "sensor" behavior (in this case, changing the reporting period).

#### VSP Central smartBASIC Application
The VSP Central smartBASIC application `central.sb` is deployed on the embedded Bluetooth co-processor on the Sentrius IG60.  This application connects to the sensor (VSP peripheral role) and forwards messages in both directions between serial port on the Sentrius IG60 and the VSP peripheral device.

#### VSP Central Role Lambda
The VSP central Lambda function `vsp_central.py` performs the core functions of this demo: it deploys the compiled VSP Central smartBASIC application to the embedded Bluetooth 5 co-processor on the Sentrius IG60, then it starts the application, which connects to the peripheral device.  Once the connection has been established, the VSP central application on the co-processor bridges messages over BLE to the IG60 serial port, and the Lambda bridges those messages to the AWS IoT cloud.

### Supporting Documentation
You may wish to refer to the following additional documentation for details that are omitted here:

[Sentrius IG60 Online Documentation](http://documentation.lairdconnect.com/Builds/IG60-GREENGRASS/latest/Content/Home.htm)

[AWS IoT Greengrass Developer Guide](https://docs.aws.amazon.com/greengrass/latest/developerguide/what-is-gg.html)

[BL654 Documentation](https://www.lairdconnect.com/wireless-modules/bluetooth-modules/bluetooth-5-modules/bl654-series-bluetooth-module-nfc#documentation)

[UwTerminalX Setup and Installation Guide](https://github.com/LairdCP/UwTerminalX) on Github

## Running the VSP Sensor Demo

### Pre-Requisites

In order to run this demo, you must have the following:
* A Sentrius IG60 with Bluetooth 5
* A BL654 USB dongle (*NOTE:* This dongle is **NOT** included with the Sentrius IG60 and must be obtained separately)
* A mobile phone running iOS 8.0 or later, or Android 7.0 or later, and the free Sentrius IG Connect application available in the Apple App Store or Google Play
* A development PC running Windows, with the following installed:
  * [UwTerminalX](https://github.com/LairdCP/UwTerminalX)
  * Python 3.7 or later
  * pySerial 3.3 or later
  * The smartBASIC XCompiler for the Sentrius IG60 Bluetooth 5 co-processor (contact support for more details), e.g., `XComp_BL654_A231_7D41.exe`
* An AWS account with permissions to create and manage Lambdas functions and Greengrass groups

### Install and Provision the Sentrius IG60 with Bluetooth 5
Refer to the Sentrius IG60 online documentation for details on how to [connect the IG60 to your AWS account](http://documentation.lairdconnect.com/Builds/IG60-GREENGRASS/latest/Content/Topics/5%20-%20Using%20the%20Device/Greengrass%20Getting%20Started/Introduction.htm).  Once you have completed this step, verify that your Sentrius IG60 is online (via the status LEDs) and available via the AWS IoT Greengrass console.

### Build and deploy the VSP peripheral application (simulated sensor)

* Insert the BL654 USB dongle in your development PC (note the device name, such as `COM9`)
* Start UwTerminalX on your development PC, and connect to the BL654 USB dongle (using the correct device name)
* In the UwTerminalX main window, enter the command `ATI 4` followed by Enter; this should display the MAC address as something like the following output:

      ATI 4
      
      10	4	01 C2F54C8147B4
      00
  Be sure to note the response (the last 14 hexadecimal digits, e.g., `01C2F54C8147B4`) for use later when configuring the central Lambda.
* Copy the peripheral smartBASIC script `peripheral.sb` from the `scripts` directory in this example to your development PC
* In UwTerminalX, right-click and select "XCompile + Load" and select the `peripheral.sb` script from your development PC
* Once the script has loaded, verify it is present on the BL654 by using the `AT+dir` command:

      AT+dir
      
      06    peripheral
      00

### Build the VSP central application for the Sentrius IG60 BL654 co-processor

* Copy the central smartBASIC script `central.sb` from the `scripts` directory in this example to your development PC
* Open a command window and run the smartBASIC cross-compiler executable on the `central.sb` script:

      C:\>XComp_BL654_A321_7D41.exe central.sb
  This should generate a file named `central.uwc` in the same directory.

### Deploy the VSP central Lambda

* Create a ZIP file containing the following:
  * `vspcentral.py` from this directory
  * The compiled "central.uwc" smartBASIC application (generated in the previous step)
  * The Sentrius IG60 ["igsdk"](https://github.com/LairdCP/igsdk/tree/master/python/igsdk) directory
  * The Greengrass Core SDK directory ["greengrasssdk"](https://github.com/aws/aws-greengrass-core-sdk-python) directory
* Log into your AWS account dashboard
* Enter the AWS Lambda console and create a new Lambda function (e.g., "vsp_central") with Python 3.7 as the runtime
* Select "Upload a ZIP file", and upload this ZIP file as the contents of the Lambda
* Publish a new version of the Lambda
* Enter the AWS IoT Greengrass console, and navigate to the "Groups" tab, then select the group you created for your Sentrius IG60
* In the "Lambdas" pane, add your VSP central Lambda (e.g., "vsp_central"), then modify the Lambda configuration as follows:
  * Set "Containerization" to "Greengrass container"
  * Set the "Memory Limit" to 32 MB
  * Set the "Timeout" to 60 seconds
  * Set the "Lambda Lifecycle" to "Make this function long-lived"
  * Define an environment variable `PERIPHERAL_ADDR` and set it to the 14-digit hexadecimal string of your peripheral device (e.g., `01C2F54C8147B4`)
* Click "Update" to update the Lambda configuration
* In the Lambda details page, select "Resources" to add a resource for the serial port
* Add a local resource for a Device with the path `/dev/ttyS2`, select "Automatically add OS group permissions", and select "Read and write access", then click "Update" to save the resource
* In the "Subscriptions" pane, create two subscriptions:
  * Create a subscription with a "Source" of "IoT Cloud" and "Target" of your Lambda, with a topic of "vsp/_CORE NAME_/_PERIPHERAL ADDR_/send" (where _CORE NAME_ is the name of your core and _PERIPHERAL ADDR_ is the 14-digit hexadecimal address of your peripheral)
  * Create a subscription with a "Source" of your Lambda and "Target" of "IoT Cloud", with a topic of "vsp/_CORE NAME_/_PERIPHERAL ADDR_/receive" (where _CORE NAME_ is the name of your core and _PERIPHERAL ADDR_ is the 14-digit hexadecimal address of your peripheral)
* (Optional) Configure your Greengrass group to perform logging via CloudWatch; refer to the [AWS Documentation on Monitoring with AWS Iot Greengrass Logs](https://docs.aws.amazon.com/greengrass/latest/developerguide/greengrass-logs-overview.html) for details
* Select "Deploy" under "Actions" to deploy the VSP central Lambda

### Start the VSP Peripheral Test script
* Copy the VSP Peripheral test script `vsp_peripheral.py` to your development PC
* Run the test script using Python 3, specifying the arguments for the COM port name and baud rate:

      C:/>py vsp_peripheral.py COM9 115200
  You should see debug output indicating that the script has started, and is receiving data from the BL654 USB dongle:

      INFO:__main__:Starting remote script.
      INFO:__main__:Starting serial receive.
  Once the peripheral receives the incoming connection from the central device (Sentrius IG60), you should see the following messages, indicating that Sentrius IG60 has connect to the peripheral, and simulated sensor data is being sent:

      INFO:__main__:VSP connected!
      INFO:__main__:Sending simulated message: {'temperature': 6.629443208538181, 'timestamp': 1576169206.5041006}

### Verify End-to-End Messaging with the AWS IoT Cloud
* In the AWS IoT Console, select the "Test" pane
* Enter a subscription topic that corresponds to your device: "vsp/_CORE NAME_/_PERIPHERAL ADDR_/receive" (where _CORE NAME_ is the name of your core and _PERIPHERAL ADDR_ is the 14-digit hexadecimal address of your peripheral).  As messages are published from the peripheral, you should see them appear in the AWS console:

      vsp/My_Core/01C2F54C8147B4/receive Dec 12, 2019 11:50:47 AM -0500
      {
        "temperature": -13.50354310451575,
        "timestamp": 1576169446.8314948
      }
* Publish a message to modify the reporting period of the simulated sensor:
  * In the "Publish" topic field, enter the topic that corresponds to your device: "vsp/_CORE NAME_/_PERIPHERAL ADDR_/send" (where _CORE NAME_ is the name of your core and _PERIPHERAL ADDR_ is the14-digit hexadecimal address of your peripheral)
  * In the payload field, enter a JSON payload that contains the "period" field:

        {
            "period" : 10
        }
    You should see an indication from the test script that the reporting period was changed:

        INFO:__main__:Changing message period to 10

