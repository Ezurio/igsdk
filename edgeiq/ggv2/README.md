# IG60 AWS IoT Greengrass V2 Support
This folder contains various utilities for supporting AWS IoT Greengrass V2 via the EdgeIQ Device Management service on the Sentrius&trade; IG60.

## AWS IoT Greengrass V2 Installation
The script [`install_ggv2_fleet_provisioning.sh`](install_ggv2_fleet_provisioning.sh) is used to perform the AWS IoT Greengras V2 operation via the EdgeIQ cloud.

The [`ggv2_fleet_provisioning_template.conf`](ggv2_fleet_provisioning_template.conf) configuration file specifies the parameters passed to the installation script.

For more info, see the Sentrius&trade; IG60 AWS IoT Greengrass V2 Getting Started Guide.

## Update OpenJDK Dependency Components
The script [`ig60_ggv2_update_openjdk_components.sh`](ig60_ggv2_update_openjdk_components.sh) is used to update the OpenJDK dependency components on an IG60 device via the EdgeIQ cloud. These components **must** be kept in sync with the version of OpenJDK utilized in the installed IG60 firmware version.

To perform the update:
1. In the "Software" page in the UI, create a Software Package and attach the OpenJDK dependency components tarball file (.tar.gz) provided in the release and the script `ig60_ggv2_update_openjdk_components.sh`.
2. Set the script to be `./ig60_ggv2_update_openjdk_components.sh OPENJDK_TARBALL_FILE` where `OPENJDK_TARBALL_FILE` is the name of the OpenJDK dependency components tarball file.
3. Apply the update to one or more IG60 devices via the UI

