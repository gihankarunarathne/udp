#!/bin/bash

# Copy Rainfall data
scp -r -i ~/.ssh/id_uwcc_admin /mnt/disks/wrf-mod/OUTPUT/RF/*  uwcc-admin@10.138.0.6:~/cfcwm/data/RF

# Copy Rainfall Grid data
scp -r -i ~/.ssh/id_uwcc_admin /mnt/disks/wrf-mod/OUTPUT/colombo/*  uwcc-admin@10.138.0.6:~/cfcwm/data/RF_GRID

# Copy HEC-HMS Discharge
scp -r -i ~/.ssh/id_uwcc_admin ~/udp/OUTPUT/DailyDischarge*  uwcc-admin@10.138.0.6:~/cfcwm/data/DIS