#!/bin/bash

#
# ./Forecast.sh -d <FORECAST_DATE>
#	e.g. ./Forecast.sh -d 2017-03-22
#
usage() {
cat <<EOF
Usage: ./Forecast.sh [-d FORECAST_DATE] [-c CONFIG_FILE] [-r ROOT_DIR] [-b DAYS_BACK] [-f]

    -h 	Show usage
    -d 	Date which need to run the forecast in YYYY-MM-DD format. Default is current date.
    -c 	Location of CONFIG.json. Default is Forecast.sh exist directory.
    -b 	Run forecast specified DAYS_BACK with respect to current date. Expect an integer.
		When specified -d option will be ignored.
    -p  Path of FLO2D Model folder
    -o  Suffix for 'water_level-<SUFFIX>' and 'water_level_grid-<SUFFIX>' output directories.
        Default is 'water_level-<YYYY-MM-DD>' and 'water_level_grid-<YYYY-MM-DD>' same as -d option value.
    -S  Base Date of FLO2D model output in YYYY-MM-DD format. Default is same as -d option value.
    -T  Base Time of FLO2D model output in HH:MM:SS format. Default is set to 00:00:00
EOF
}

trimQuotes() {
	tmp="${1%\"}"
	tmp="${tmp#\"}"
	echo $tmp
}

forecast_date="`date +%Y-%m-%d`";
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
META_FLO2D_DIR=$ROOT_DIR/META_FLO2D
FLO2D_DIR=$ROOT_DIR/FLO2D
INIT_DIR=$(pwd)
CONFIG_FILE=$ROOT_DIR/CONFIG.json
DAYS_BACK=0
FLO2D_PATH=""
FLO2D_OUTPUT_SUFFIX=""
START_DATE=""
START_TIME=""

# Extract user arguments
while getopts hd:c:b:p:o:S:T: opt; do
    case $opt in
        h)
            usage
            exit 0
            ;;
        d)  forecast_date=$OPTARG
            ;;
        c)  CONFIG_FILE=$OPTARG
            ;;
		b)  DAYS_BACK=$OPTARG
			;;
        p)  FLO2D_PATH=$OPTARG
            ;;
        o)  FLO2D_OUTPUT_SUFFIX=$OPTARG
            ;;
        S)  START_DATE=$OPTARG
            ;;
        T)  START_TIME=$OPTARG
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
echo "At $(pwd)"
if [ -z "$(find $CONFIG_FILE -name CONFIG.json)" ]
then
	echo "Unable to find $CONFIG_FILE file"
	exit 1
fi

HOST_ADDRESS=$(trimQuotes $(cat CONFIG.json | jq '.HOST_ADDRESS'))
HOST_PORT=$(cat CONFIG.json | jq '.HOST_PORT')
WINDOWS_HOST="$HOST_ADDRESS:$HOST_PORT"

current_date_time="`date +%Y-%m-%dT%H:%M:%S`";

main() {
    echo "Start at $current_date_time"
    cp $META_FLO2D_DIR/RUN_FLO2D.json $FLO2D_DIR
    # Set FLO2D model path
    FLO2D_PATH_TXT="\"FLO2D_PATH\"\t : \"$FLO2D_PATH\","
    sed -i "/FLO2D_PATH/c\    $FLO2D_PATH_TXT" $FLO2D_DIR/RUN_FLO2D.json
    # Set FLO2D output SUFFIX
    FLO2D_OUTPUT_SUFFIX_TXT="\"FLO2D_OUTPUT_SUFFIX\"\t : \"$FLO2D_OUTPUT_SUFFIX\","
    sed -i "/FLO2D_OUTPUT_SUFFIX/c\    $FLO2D_OUTPUT_SUFFIX_TXT" $FLO2D_DIR/RUN_FLO2D.json
    # Set Base Start Date for FLO2D
    START_DATE_TXT="\"START_DATE\"\t : \"$START_DATE\","
    sed -i "/START_DATE/c\    $START_DATE_TXT" $FLO2D_DIR/RUN_FLO2D.json
    # Set Base Start Time for FLO2D
    START_TIME_TXT="\"START_TIME\"\t : \"$START_TIME\""
    sed -i "/START_TIME/c\    $START_TIME_TXT" $FLO2D_DIR/RUN_FLO2D.json

    echo "Trigger FLO2D WaterLevel Extraction on Forecast Date: $forecast_date, Config File: $CONFIG_FILE, Root Dir: $ROOT_DIR"

    curl -X POST --data-binary @./FLO2D/RUN_FLO2D.json  $WINDOWS_HOST/EXTRACT_WATERLEVEL?$forecast_date
    echo "Send POST request to $WINDOWS_HOST with EXTRACT_WATERLEVEL?$forecast_date"

    curl -X POST --data-binary @./FLO2D/RUN_FLO2D.json  $WINDOWS_HOST/EXTRACT_WATERLEVEL_GRID?$forecast_date
    echo "Send POST request to $WINDOWS_HOST with EXTRACT_WATERLEVEL_GRID?$forecast_date"
}

main "$@"

# End of Trigger_Extract_WaterLevel_GRID.sh