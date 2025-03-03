#!/bin/sh
#
# IG60 Update Script for EdgeIQ
#

UPDATEFILE=$1

# Check the current firmware release level (LRD7 or LRD11+)
LRD=$(grep VERSION_ID /etc/os-release | cut -f 2 -d"=" | cut -f 1 -d".")
echo "LRD is $LRD"

case $LRD in
    7)
        echo "Updating from LRD7"
        # Make verbose log, fail on uncaught errors
        set -xe
        FSCRYPT_KEY=ffffffffffffffff
        MOUNT_POINT=/var/migrate
        DATA_SECRET=${MOUNT_POINT}/secret
        DATA_PUBLIC=${MOUNT_POINT}/public
        KEYFILE=/etc/ssl/misc/dev.crt

        cleanup_and_fail(){
            echo "$1"
            umount ${MOUNT_POINT} >/dev/null 2>&1 || true
            rm -f "${UPDATEFILE}"
            exit 1
        }

        # Read the configured bootside and actual root filesystem partition in use
        BOOTSIDE=$(fw_printenv -n bootside) || cleanup_and_fail "Cannot read bootside"
        CURRENTROOT=$(sed -rn 's/.*(ubiblock0_[0-9]).*/\1/p' /proc/cmdline) || cleanup_and_fail "Cannot read current rootfs"

        if [ "${BOOTSIDE}" = "a" ]; then
            UPDATESIDE="b"
            MIGRATE_DEVICE="/dev/ubi0_5"
            EXPECTEDROOT="ubiblock0_1"
        else
            UPDATESIDE="a"
            MIGRATE_DEVICE="/dev/ubi0_2"
            EXPECTEDROOT="ubiblock0_4"
        fi

        # Sanity check that the mounted rootfs matches the bootside; this
        # prevents applying an update again before a reboot (which can
        # lead to an unbootable filesystem!)
        if [ "${CURRENTROOT}" != "${EXPECTEDROOT}" ]; then cleanup_and_fail "Inconsistent boot sides"; fi

        # Set update tag if a different bootloader key was assigned in manufacturing.
        # NOTE: Newer versions of fw_printenv return empty strings when variable is undefined
        UPDATETAG=$(fw_printenv -n fwkey) || UPDATETAG='stable'
        if [ -z "${UPDATETAG}" ]; then UPDATETAG="stable"; fi
        UPDATESEL="${UPDATETAG},main-${UPDATESIDE}"

        # Apply update
        echo "Applying update ${UPDATESEL} from ${UPDATEFILE}"
        swupdate -b "2 3" -l 4 -v -i "${UPDATEFILE}" -e "${UPDATESEL}" -k "${KEYFILE}" || cleanup_and_fail "Failed to perform swupdate"

        # Create mount point and mount the data device
        mkdir -p "${MOUNT_POINT}" || cleanup_and_fail "Failed to create ${MOUNT_POINT}"
        mount -o noatime -t ubifs "${MIGRATE_DEVICE}" "${MOUNT_POINT}" || "Failed to mount ${MIGRATE_DEVICE}"

        # Wipe data patition
        rm -rf "${MOUNT_POINT:?}"/* || cleanup_and_fail "Cannot erase ${MOUNT_POINT}"

        # Make sure the encryption key is available
        keyctl link "@us" "@s" || cleanup_and_fail "Cannot obtain encryption key"

        # Create encrypted directory and sync encrypted data
        mkdir -p "${DATA_SECRET}" || cleanup_and_fail "Cannot create ${DATA_SECRET}"
        fscryptctl set_policy "${FSCRYPT_KEY}" "${DATA_SECRET}" || cleanup_and_fail "Cannot enable encryption"
        rsync -rlptDW --exclude=.mounted /data/secret/ "${DATA_SECRET}" || cleanup_and_fail "Cannot sync to ${DATA_SECRET}"

        # Migrate public data
        mkdir -p "${DATA_PUBLIC}" || cleanup_and_fail "Cannot create ${DATA_PUBLIC}"
        rsync -rlptDW /data/public/ "${DATA_PUBLIC}" || cleanup_and_fail "Cannot sync to ${DATA_PUBLIC}"
        umount "${MOUNT_POINT}" || cleanup_and_fail "Cannot unmount ${MOUNT_POINT}"

        # Change the bootside
        fw_setenv bootside "${UPDATESIDE}" || cleanup_and_fail "Cannot set bootside"

        # Delete the update file to save space
        rm -f "${UPDATEFILE}"

        exit 0
        ;;
    11)
        echo "Updating from LRD11"
        ;;
    12)
        echo "Updating from LRD12"
        ;;
    *)
        echo "Unknown LRD version: $LRD"
        ;;
esac

fw_update "./$UPDATEFILE" > output.txt 2>&1
# if "failed" is NOT found, err level 1 is set - thus, we are LRD11+ -> LRD11+
if ! grep -q 'failed' output.txt; then
    # No sign of "failed" in output.txt - we should be done
    echo "Successfully upgraded from $LRD"
    exit 0
else
    # this means something bad happened...
    echo "Error when upgrading from $LRD"
    exit 1
fi
