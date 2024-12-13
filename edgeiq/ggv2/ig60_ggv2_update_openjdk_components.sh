#!/bin/bash
# Copyright (c) 2024 Ezurio LLC.
#
# IG60 helper script for updating the OpenJDK dependency components to support
# GGv2 which are stored on the SD card
#
# Usage: ig60_ggv2_update_openjdk_components.sh path/to/openjdk.tar.gz
#

# Make verbose log, fail on uncaught errors
set -xe

OPENJDK_TARBALL_FILE=$1

programname=$(basename $0)

#
# Helper function to print out the script usage
#
show_usage() {
    echo -e "Usage: $programname path/to/openjdk.tar.gz\n"
}

#
# Helper function to print an error message and exit with a failure code
#
cleanup_and_fail(){
    echo $1
    rm -f ${OPENJDK_TARBALL_FILE}
    exit 1
}

if [ $# -ne 1 ]; then
    show_usage
    cleanup_and_fail "Invalid arguments"
    exit 1
fi

SDCARD_ROOT="/media/mmcblk0p1"

# Link in the FS key
keyctl link @us @s

# Stop GGv2
echo "Stopping Greengrass V2"
systemctl stop ggv2runner

# Since the 'ggv2sdmount' service is configured as 'PartOf' the main
# 'ggv2runner' service, it must be "manually" started here in order to properly
# re-mount the SD card.
echo "Re-mounting SD card"
systemctl start ggv2sdmount

# Verify the SD card root exists
if [ ! -d "${SDCARD_ROOT}" ]; then cleanup_and_fail "SD card not found"; fi

# Delete existing OpenJDK files
rm -rf $SDCARD_ROOT/jdk

# Extract the tarball
echo "Extracting the OpenJDK dependency components tarball"
tar xzf ${OPENJDK_TARBALL_FILE} -C ${SDCARD_ROOT} --no-same-owner
if [ ! $? -eq 0 ]; then cleanup_and_fail "Unable to extract OpenJDK dependency components tarball"; fi

# Delete the OpenJDK dependency components tarball
rm -f ${OPENJDK_TARBALL_FILE}

# Restart GGv2
echo "Restarting Greengrass V2"
systemctl start ggv2runner

exit 0
