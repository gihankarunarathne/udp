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

trimQuotes() {
    tmp="${1%\"}"
    tmp="${tmp#\"}"
    echo $tmp
}

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INIT_DIR=$(pwd)
CONFIG_FILE=$ROOT_DIR/CONFIG.json

forecast_date="`date +%Y-%m-%d`";
forecast_time="`date +%H:00:00`";
DAYS_BACK=0

# Extract user arguments
while getopts hd:t:b:f opt; do
    case $opt in
        h)
            usage
            exit 0
            ;;
        d)  forecast_date=$OPTARG
            ;;
        d)  forecast_time=$OPTARG
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

# cd into bash script's root directory
cd $ROOT_DIR
echo "Current Working Directory set to -> $(pwd)"
if [ -z "$(find $CONFIG_FILE -name CONFIG.json)" ]
then
    echo "Unable to find $CONFIG_FILE file"
    exit 1
fi

RF_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.RF_DIR_PATH'))
KUB_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.KUB_DIR_PATH'))
RF_GRID_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.RF_GRID_DIR_PATH'))
OUTPUT_DIR=$(trimQuotes $(cat CONFIG.json | jq '.OUTPUT_DIR'))

# Copy Rainfall data
RF_DIR_PATH=$RF_DIR_PATH/*-$forecast_date.*
scp -r -i ~/.ssh/id_uwcc_admin $RF_DIR_PATH  uwcc-admin@10.138.0.6:~/cfcwm/data/RF

# Copy Kelani Upper Basin mean Rainfall data
KUB_DIR_PATH=$KUB_DIR_PATH/mean-rf-$forecast_date.txt
scp -r -i ~/.ssh/id_uwcc_admin $KUB_DIR_PATH  uwcc-admin@10.138.0.6:~/cfcwm/data/RF/KUB/kelani-upper-basin-$forecast_date.txt

# Copy Rainfall Grid data
RF_GRID_DIR_PATH=$RF_GRID_DIR_PATH/created-$forecast_date
scp -r -i ~/.ssh/id_uwcc_admin $RF_GRID_DIR_PATH  uwcc-admin@10.138.0.6:~/cfcwm/data/RF_GRID

# Copy HEC-HMS Discharge
OUTPUT_DIR=$OUTPUT_DIR/DailyDischarge-$forecast_date.*
scp -r -i ~/.ssh/id_uwcc_admin $OUTPUT_DIR  uwcc-admin@10.138.0.6:~/cfcwm/data/DIS