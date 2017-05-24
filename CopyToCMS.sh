#!/bin/bash

usage() {
cat <<EOF
Usage: ./Forecast.sh [-d FORECAST_DATE] [-c CONFIG_FILE] [-r ROOT_DIR] [-b DAYS_BACK] [-f]

    -h  Show usage
    -d  Date which need to run the forecast in YYYY-MM-DD format. Default is current date.
    -b  Run forecast specified DAYS_BACK with respect to current date. Expect an integer.
        When specified -d option will be ignored.
EOF
}

forecast_date="`date +%Y-%m-%d`";
DAYS_BACK=0
# Extract user arguments
while getopts hd:b:f opt; do
    case $opt in
        h)
            usage
            exit 0
            ;;
        d)  forecast_date=$OPTARG
            ;;
        b)  DAYS_BACK=$OPTARG
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
done

if [ "$DAYS_BACK" -gt 0 ]
then
    #TODO: Try to back date base on user given date
    forecast_date="`date +%Y-%m-%d -d "$DAYS_BACK days ago"`";
fi

# Copy Rainfall data
scp -r -i ~/.ssh/id_uwcc_admin /mnt/disks/wrf-mod/OUTPUT/RF/*-$forecast_date.*  uwcc-admin@10.138.0.6:~/cfcwm/data/RF

# Copy Kelani Upper Basin mean Rainfall data
scp -r -i ~/.ssh/id_uwcc_admin /mnt/disks/wrf-mod/OUTPUT/kelani-upper-basin/mean-rf-$forecast_date.txt  uwcc-admin@10.138.0.6:~/cfcwm/data/RF/KUB/kelani-upper-basin-$forecast_date.txt

# Copy Rainfall Grid data
scp -r -i ~/.ssh/id_uwcc_admin /mnt/disks/wrf-mod/OUTPUT/colombo/created-$forecast_date  uwcc-admin@10.138.0.6:~/cfcwm/data/RF_GRID

# Copy HEC-HMS Discharge
scp -r -i ~/.ssh/id_uwcc_admin ~/udp/OUTPUT/DailyDischarge-$forecast_date.*  uwcc-admin@10.138.0.6:~/cfcwm/data/DIS