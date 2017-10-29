#!/bin/bash

#
# ./Trigger_Extract_WaterLevel.sh -d <FORECAST_DATE>
#	e.g. ./Trigger_Extract_WaterLevel.sh -d 2017-03-22
#
usage() {
cat <<EOF
Usage: ./Trigger_Extract_WaterLevel.sh [-d FORECAST_DATE] [-c CONFIG_FILE] [-r ROOT_DIR] [-b DAYS_BACK] [-f]

    -h 	Show usage
    -d 	Model State Date which need to run the forecast in YYYY-MM-DD format. Default is current date.
    -t  Modal State Time which run the forecast in HH:MM:SS format. If -d passed, then default is 00:00:00.
        Otherwise Default is current time.
    -b  Run forecast specified DAYS_BACK with respect to current date. Expect an integer.
        When specified -d option will be ignored.
    -S  Base Date(Timeseries start date) of FLO2D model output in YYYY-MM-DD format. Default is same as -d option value.
    -T  Base Time(Timeseries start time) of FLO2D model output in HH:MM:SS format. Default is same as -t option value.
    -p  Path of FLO2D Model folder.
    -o  Suffix for 'water_level-<SUFFIX>' and 'water_level_grid-<SUFFIX>' output directories.
        Default is 'water_level-<YYYY-MM-DD>' and 'water_level_grid-<YYYY-MM-DD>' same as -d option value.
    -H  Host ADDRESS of 'FLO2D Server' is running. Default is 'HOST_ADDRESS' taken from CONFIG.json
    -P  Host PORT of 'FLO2D Server' is running. Default is 'HOST_PORT' taken from CONFIG.json
    -c  Location of CONFIG.json. Default is Forecast.sh exist directory.
    -n  Name field value of the Run table in Database. Use time format such as <%H:%M:%S> to replace with time(t).
EOF
}

trimQuotes() {
	tmp="${1%\"}"
	tmp="${tmp#\"}"
	echo $tmp
}

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
META_FLO2D_DIR=$ROOT_DIR/META_FLO2D
FLO2D_DIR=$ROOT_DIR/FLO2D
INIT_DIR=$(pwd)
CONFIG_FILE=$ROOT_DIR/CONFIG.json

forecast_date="`date +%Y-%m-%d`";
forecast_time="00:00:00";
# forecast_time="`date +%H:00:00`";

DAYS_BACK=0
FLO2D_PATH=""
FLO2D_OUTPUT_SUFFIX=""
TIMESERIES_START_DATE=""
TIMESERIES_START_TIME=""
RUN_NAME=""
CUSTOM_HOST_ADDRESS=""
CUSTOM_HOST_PORT=""

# Extract user arguments
while getopts hd:c:b:p:o:S:T:H:P: opt; do
    case $opt in
        h)
            usage >&2
            exit 0
            ;;
        d)  forecast_date=$OPTARG
            ;;
        t)  forecast_time=$OPTARG
            ;;
        c)  CONFIG_FILE=$OPTARG
            ;;
		b)  DAYS_BACK=$OPTARG
			;;
        p)  FLO2D_PATH=$OPTARG
            ;;
        o)  FLO2D_OUTPUT_SUFFIX=$OPTARG
            ;;
        S)  TIMESERIES_START_DATE=$OPTARG
            ;;
        T)  TIMESERIES_START_TIME=$OPTARG
            ;;
        H)  CUSTOM_HOST_ADDRESS=$OPTARG
            ;;
        P)  CUSTOM_HOST_PORT=$OPTARG
            ;;
        n)  RUN_NAME=$OPTARG
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
done

if [ "$DAYS_BACK" -gt 0 ]; then
	#TODO: Try to back date base on user given date
	forecast_date="`date +%Y-%m-%d -d "$DAYS_BACK days ago"`";
fi

if [ -z $TIMESERIES_START_DATE ]; then
    TIMESERIES_START_DATE=$forecast_date
fi
if [ -z $TIMESERIES_START_TIME ]; then
    TIMESERIES_START_TIME=$forecast_time
fi

# cd into bash script's root directory
cd $ROOT_DIR
echo "At $(pwd)"
if [ -z "$(find $CONFIG_FILE -name CONFIG.json)" ]
then
	echo "Unable to find $CONFIG_FILE file"
	exit 1
fi

HOST_ADDRESS=`[[ $CUSTOM_HOST_ADDRESS != "" ]] && echo $CUSTOM_HOST_ADDRESS || echo $(trimQuotes $(cat CONFIG.json | jq '.HOST_ADDRESS'))`
HOST_PORT=`[[ $CUSTOM_HOST_PORT != "" ]] && echo $CUSTOM_HOST_PORT || echo $(cat CONFIG.json | jq '.HOST_PORT')`
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

    # Set Base Start Date for FLO2D (which maps to 0 step)
    TIMESERIES_START_DATE_TXT="\"TIMESERIES_START_DATE\"\t : \"$TIMESERIES_START_DATE\","
    sed -i "/TIMESERIES_START_DATE/c\    $TIMESERIES_START_DATE_TXT" $FLO2D_DIR/RUN_FLO2D.json
    # Set Base Start Time for FLO2D (which maps to 0 step)
    TIMESERIES_START_TIME_TXT="\"TIMESERIES_START_TIME\"\t : \"$TIMESERIES_START_TIME\","
    sed -i "/TIMESERIES_START_TIME/c\    $TIMESERIES_START_TIME_TXT" $FLO2D_DIR/RUN_FLO2D.json

    # Set Model State Date for FLO2D
    MODEL_STATE_DATE_TXT="\"MODEL_STATE_DATE\"\t : \"$forecast_date\","
    sed -i "/MODEL_STATE_DATE/c\    $MODEL_STATE_DATE_TXT" $FLO2D_DIR/RUN_FLO2D.json
    # Set Model State Time for FLO2D
    MODEL_STATE_TIME_TXT="\"MODEL_STATE_TIME\"\t : \"$forecast_time\","
    sed -i "/MODEL_STATE_TIME/c\    $MODEL_STATE_TIME_TXT" $FLO2D_DIR/RUN_FLO2D.json

    # Run name/tags of the Timeseries
    RUN_NAME_TXT="\"RUN_NAME\"\t : \"$RUN_NAME\","
    sed -i "/RUN_NAME/c\    $RUN_NAME_TXT" $FLO2D_DIR/RUN_FLO2D.json

    echo "Trigger FLO2D WaterLevel Extraction on Forecast Date: $forecast_date $forecast_time $TIMESERIES_START_DATE $TIMESERIES_START_TIME, Config File: $CONFIG_FILE, Root Dir: $ROOT_DIR"

    curl -X POST --data-binary @./FLO2D/RUN_FLO2D.json  $WINDOWS_HOST/EXTRACT_WATERLEVEL?$forecast_date
    echo "Send POST request to $WINDOWS_HOST with EXTRACT_WATERLEVEL?$forecast_date"

    curl -X POST --data-binary @./FLO2D/RUN_FLO2D.json  $WINDOWS_HOST/EXTRACT_WATERLEVEL_GRID?$forecast_date
    echo "Send POST request to $WINDOWS_HOST with EXTRACT_WATERLEVEL_GRID?$forecast_date"
}

main "$@"

# End of Trigger_Extract_WaterLevel_GRID.sh