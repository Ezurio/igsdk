#!/bin/bash

set -e

# How to use:
# sudo ./update_edge_through_sw_update.sh <edge-location-without-trailing-slash> <writable-tmp-dir-without-trailing-slash>

# - create a software package through the edge portal
# - set the following command `sudo ./update_edge_through_sw_update.sh`
# - attach this file
# - run against target device

# ASSUMPTIONS
# - linux-amd64
# - systemd enabled
# - standard location /opt/edge/*

# FLAGS to pass
# - writeable temporary location
WRITEABLE_TMP_LOCATION="/tmp"
# - location for config files
EDGE_PARENT_DIR="/gg"
# (- architecture?)


# make it look nice
INFO="INFO:  "
TEST="TEST:  "
CHECK="CHECK: "
PASSED="PASSED:"
WARN="WARN:  "
ERROR="ERROR: "
RUN="RUN:   "

printf "\n==== CHECKING INPUTS ====\n\n"

if [ ! -z "$1" ]
then
    EDGE_PARENT_DIR=$1
    echo "$INFO received custom edge directory $EDGE_PARENT_DIR."
fi
echo "$INFO using edge location $EDGE_LOCATION."
if [ ! -z "$2" ]
then
    WRITEABLE_TMP_LOCATION=$2
    echo "$INFO received custom tmp folder $WRITEABLE_TMP_LOCATION."
fi
echo "$INFO using tmp folder $WRITEABLE_TMP_LOCATION."

# Set edge location
EDGE_LOCATION="$EDGE_PARENT_DIR/edge"

# IG60 specifics
# - architecture armv7 (thumb) - assume edge arm7 / edgectl armhf
# - kernel 4.19, bash, curl, wget available
# - There is a systemd unit file present on the device (in place before edge is installed).
# 

printf "\n==== CHECKING IF CONDITIONS FOR UPDATE ARE MET ====\n\n"

# config
# http would work too, as long as it only downloads files
STAGING_URL="https://api.stage.machineshop.io/api/v1/platform"
PROD_URL="https://machineshopapi.com/api/v1/platform"
# not used for now
STAGING_URL_NEW="https://api.stage.edgeiq.io/api/v1/platform"
PROD_URL_NEW="https://api.edgeiq.io/api/v1/platform"

# test if boostrap.json is at the default location
BOOTSTRAP_FILE=$EDGE_LOCATION/conf/bootstrap.json
printf "$TEST check if bootstrap.json is at the specified location ($BOOTSTRAP_FILE).\n"
if [ ! -f $BOOTSTRAP_FILE ]; then
    printf "$ERROR bootstrap.json not found, cannot proceed.\n"
    exit 1;
else
    printf "$PASSED found bootstrap.json.\n"
fi

# Extract company identifier from bootstrap.conf
COMPANY_ID="$(cat /gg/edge/conf/bootstrap.json | tr -d ' ,"' | grep company_id | awk -F':' ' {print $2}')"
if [ -z "$COMPANY_ID" ]
then
    printf "$ERROR cannot find company id, cannot proceed.\n"
    exit 1;
fi

# test if conf.json is at the default location
CONF_FILE=$EDGE_LOCATION/conf/conf.json
printf "$TEST check if conf.json is at the specified location ($CONF_FILE).\n"
if [ ! -f $CONF_FILE ]; then
    printf "$ERROR conf.json not found, cannot proceed.\n"
    exit 1;
else
    printf "$PASSED found conf.json.\n"
fi

# test if /tmp folder is writable
TEST_FILE="$WRITEABLE_TMP_LOCATION/edgectl-testwrite.txt"
echo "TEST" > $TEST_FILE || ( echo "$ERROR cannot write to tmp location $WRITEABLE_TMP_LOCATION/." )
rm $TEST_FILE || echo "$WARN cannot delete temporary file: $TEST_FILE."

# test if there is enough free space (>80 MB) in /tmp
printf "$TEST check if there is enough free space in $WRITEABLE_TMP_LOCATION.\n"
FREE_SPACE=$(df -P "$WRITEABLE_TMP_LOCATION" | awk 'int($4)>81920{print $4}') || echo "$WARN cannot check free space."
if [ -z "$FREE_SPACE" ]
then
    printf "$ERROR not enough free space in $WRITEABLE_TMP_LOCATION, cannot proceed.\n"
    exit 1;
else
    printf "$INFO enough space in $WRITEABLE_TMP_LOCATION: $FREE_SPACE.\n"
fi

# test if staging or production url is set up in conf.json
printf "$TEST check which environment conf.json is configured to use.\n"

# Always use production
ENV_DETECTED="prod"
PLATFORM_URL="$PROD_URL_NEW"

# test if systemd is set up correctly
printf "$TEST check if systemd unit file exists\n"
SYSTEMD_UNIT_FILE="/etc/systemd/system/edge.service"

if [ ! -f $SYSTEMD_UNIT_FILE ]
then
    printf "$ERROR edge systemd unit file is missing, cannot proceed.\n"
    exit 1;
else
    printf "$PASSED systemd unit file exists ($SYSTEMD_UNIT_FILE).\n"
fi

# test if edgectl is installed
printf "$CHECK check if edgectl is installed.\n"

EDGECTL_COMMAND="edgectl"
EDGECTL_DL_URL=""

if [ -z "$(which edgectl)" ]
then
    printf "$INFO edgectl is not installed, needs to be installed.\n"
    # TODO install

    # test if architecture is supported
    printf "$TEST if architecture is supported.\n"
    ARCH=$(uname -m)
    if [[ $ARCH == "x86_64" ]]
    then
        printf "$PASSED architecture is $ARCH / amd64 is supported.\n"
        ARCH="amd64"
    elif [[ $ARCH == "aarch64" ]]
    then
        printf "$PASSED architecture is $ARCH is supported.\n"
        # set arch to armhf in case of arm7 (edgectl binary is named armhf)
        ARCH="arm64"
    elif [[ $ARCH == "armv7l" ]]
    then
        printf "$PASSED architecture is $ARCH is supported.\n"
        # set arch to armhf in case of arm7 (edgectl binary is named armhf)
        ARCH="armhf"
    else
        printf "$ERROR architecture $ARCH is not supported.\n"
        exit 1
    fi
    # download edgectl
    wget $PLATFORM_URL/edgectl/latest/edgectl-linux-$ARCH-latest -O $WRITEABLE_TMP_LOCATION/edgectl || ( echo "$ERROR while downloading edgectl."; exit 1 )

    # set binary executable
    chmod +x $WRITEABLE_TMP_LOCATION/edgectl || ( echo "$ERROR while making edgectl executable."; exit 1 )
    EDGECTL_COMMAND="$WRITEABLE_TMP_LOCATION/edgectl"
else
    printf "$INFO edgectl is installed.\n"
fi

printf "$TEST check if edgectl is executable.\n"
$EDGECTL_COMMAND version || ( echo "$ERROR cannot execute edgectl."; exit 1 )

# Create install script
EDGE_INSTALL_SCRIPT=${WRITEABLE_TMP_LOCATION}/edge_install.sh
rm -rf ${EDGE_INSTALL_SCRIPT}
cat > ${EDGE_INSTALL_SCRIPT} << EOF
#!/bin/sh

cp ${EDGE_PARENT_DIR}/edge/init/systemd/edge.service ${WRITEABLE_TMP_LOCATION}/edge.service
systemctl stop edge || true
rm -rf ${EDGE_PARENT_DIR}/edge.old
mv ${EDGE_PARENT_DIR}/edge ${EDGE_PARENT_DIR}/edge.old
${EDGECTL_COMMAND} install -p laird -d ${EDGE_PARENT_DIR} -t -c ${COMPANY_ID} || (echo "$ERROR Install failed, restoring old version." ; rm -rf ${EDGE_PARENT_DIR}/edge ; mv ${EDGE_PARENT_DIR}/edge.old ${EDGE_PARENT_DIR}/edge )
cp ${WRITEABLE_TMP_LOCATION}/edge.service ${EDGE_PARENT_DIR}/edge/init/systemd/edge.service
systemctl start edge
rm -rf ${EDGE_PARENT_DIR}/edge.old
EOF

# set update script executable
chmod +x ${EDGE_INSTALL_SCRIPT} || ( echo "$ERROR while making update script executable."; exit 1 )

printf "Update script contents:"
cat ${EDGE_INSTALL_SCRIPT}

printf "\n==== PROCEEDING WITH UPDATE ====\n\n"

EDGECTL_LOG="$WRITEABLE_TMP_LOCATION/edgectl_install.log"

echo "$RUN executing install script... will go dark now."

# need to run this in the background, because edgectl will kill edge and therefore this script, too
nohup $EDGE_INSTALL_SCRIPT &> "$EDGECTL_LOG" &

