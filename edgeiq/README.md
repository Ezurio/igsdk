# Sentrius IG60 EdgeIQ Support
This folder contains various utilities for supporting the EdgeIQ Device Management service on the Sentrius&trade; IG60.

## Firmware Update
The script `ig60_update.sh` is used to perform a firmware update operation via the EdgeIQ cloud:

1. In the "Software" page in the UI, create a Software Package and attach the update file (.SWU) and the script `ig60_update.sh`
2. Set the script to be `./ig60_update.sh UPDATE_FILE` where `UPDATE_FILE` is the name of the update .SWU file
3. Apply the update to one or more IG60 devices via the UI

## Edge Update
The script `update_edge.sh` is used to update the Edge agent to the latest version.

1. In the "Software" page in the UI, create a Software Package and attach the script `update_edge.sh`
2. Set the script to be `./update_edge.sh /gg /tmp`
3. Apply the update to one or more IG60 devices via the UI
