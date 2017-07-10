#!/bin/bash

#
# ./Forecast.sh -d <FORECAST_DATE>
#   e.g. ./Forecast.sh -d 2017-03-22
#
usage() {
cat <<EOF
Usage: ./Forecast.sh [-d FORECAST_DATE] [-t FORECAST_TIME] [-c CONFIG_FILE] [-r ROOT_DIR] [-b DAYS_BACK] [-f]

    -h      Show usage
    -d      Date which need to run the forecast in YYYY-MM-DD format. Default is current date.
    -t      Time which need to run the forecast in HH:MM:SS format. Default is current hour. Run on hour resolution only.
    -c      Location of CONFIG.json. Default is Forecast.sh exist directory.
    -r      ROOT_DIR which is program running directory. Default is Forecast.sh exist directory.
    -b      Run forecast specified DAYS_BACK with respect to current date. Expect an integer.
            When specified -d option will be ignored.
    -f      Force run forecast. Even the forecast already run for the particular day, run again. Default is false.
    -i      Initiate a State at the end of HEC-HMS run.
    -s      Store Timeseries data on MySQL database.
    -e      Exit without executing models which run on Windows.
    -C      (Control Interval in minutes) Time period that HEC-HMS model should run

    -T|--tag    Tag to differential simultaneous Forecast Runs E.g. wrf1, wrf2 ...

    --wrf-out       Path of WRF_OUTPUT directory. If this is set, then 
                        <WRF_OUT>/RF                    (<-RF_DIR_PATH)
                        <WRF_OUT>/kelani-upper-basin    (<-KUB_DIR_PATH)
                        <WRF_OUT>/colombo               (<-RF_GRID_DIR_PATH)
                        <WRF_OUT>/kelani-basin          (<-FLO2D_RAINCELL_DIR_PATH)
                    will use respectively instead of CONFIG.json.
                    Otherwise using the values from CONFIG.json
    --wrf-rf        Path of WRF Rf(Rainfall) Directory. Otherwise using the `RF_DIR_PATH` from CONFIG.json
    --wrf-kub       Path of WRF kelani-upper-basin(KUB) Directory. Otherwise using the `KUB_DIR_PATH` from CONFIG.json
    --wrf-rf-grid   Path of WRF colombo(RF_GRID) Directory. Otherwise using the `RF_GRID_DIR_PATH` from CONFIG.json
    --wrf-raincell  Path of WRF kelani-basin(Raincell) Directory. Otherwise using the `RF_DIR_PATH` from CONFIG.json
EOF
}

trimQuotes() {
    tmp="${1%\"}"
    tmp="${tmp#\"}"
    echo $tmp
}
# replaceStringVariable <variableName> <replacingVariableName> <replacingVariableValue>
replaceStringVariable() {
    # E.g. Working example of replacing "${HEC_HMS_MODEL_DIR}/2008_2_Events_input.dss"
    # with HEC_HMS_MODEL_DIR="./2008_2_Events"
    #
    # if [[ "$DSS_INPUT_FILE" =~ ^\$\{(HEC_HMS_MODEL_DIR)\} ]]; then
    #     DSS_INPUT_FILE=${DSS_INPUT_FILE/\$\{HEC_HMS_MODEL_DIR\}/$HEC_HMS_MODEL_DIR}
    # fi

    if [[ "$1" =~ ^\$\{("$2")\} ]]; then
        echo ${1/\$\{$2\}/"$3"}
    else
        echo $1
    fi
}

forecast_date="`date +%Y-%m-%d`";
forecast_time="`date +%H:00:00`";
ROOT_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INIT_DIR=$(pwd)
CONFIG_FILE=$ROOT_DIR/CONFIG.json
DAYS_BACK=0
FORCE_RUN=false
INIT_STATE=false
STORE_DATA=false
FORCE_EXIT=false
CONTROL_INTERVAL=0
TAG=""
WRF_OUT=""

# Read the options
# Ref: http://www.bahmanm.com/blogs/command-line-options-how-to-parse-in-bash-using-getopt
TEMP=`getopt -o hd:t:c:r:b:fiseC:T: \
        --long arga::,argb,argc:,tag:,wrf-out: \
        -n 'Forecast.sh' -- "$@"`

# Terminate on wrong args. Ref: https://stackoverflow.com/a/7948533/1461060
if [ $? != 0 ] ; then usage >&2 ; exit 1 ; fi

eval set -- "$TEMP"

# Extract options and their arguments into variables.
while true ; do
    case "$1" in
        # -a|--arga)
        #     case "$2" in
        #         "") ARG_A='some default value' ; shift 2 ;;
        #         *) ARG_A=$2 ; shift 2 ;;
        #     esac ;;
        # -b|--argb) ARG_B=1 ; shift ;;
        # -c|--argc)
        #     case "$2" in
        #         "") shift 2 ;;
        #         *) ARG_C=$2 ; shift 2 ;;
        #     esac ;;

        -h)
            usage >&2
            exit 0
            shift ;;
        -d)
            case "$2" in
                "") shift 2 ;;
                *) forecast_date="$2" ; shift 2 ;;
            esac ;;
        -t)
            case "$2" in
                "") shift 2 ;;
                *) forecast_time="$2" ; shift 2 ;;
            esac ;;
        -c)
            case "$2" in
                "") shift 2 ;;
                *) CONFIG_FILE="$2" ; shift 2 ;;
            esac ;;
        -r)
            case "$2" in
                "") shift 2 ;;
                *) ROOT_DIR="$2" ; shift 2 ;;
            esac ;;
        -b)
            case "$2" in
                "") shift 2 ;;
                *) DAYS_BACK="$2" ; shift 2 ;;
            esac ;;
        -f)  FORCE_RUN=true ; shift ;;
        -i)  INIT_STATE=true ; shift ;;
        -s)  STORE_DATA=true ; shift ;;
        -e)  FORCE_EXIT=true ; shift ;;
        -C)
            case "$2" in
                "") shift 2 ;;
                *) CONTROL_INTERVAL="$2" ; shift 2 ;;
            esac ;;
        -T|--tag)
            case "$2" in
                "") shift 2 ;;
                *) TAG="$2" ; shift 2 ;;
            esac ;;
        --wrf-out)
            case "$2" in
                "") shift 2 ;;
                *) WRF_OUT="$2" ; shift 2 ;;
            esac ;;

        --) shift ; break ;;
        *) usage >&2 ; exit 1 ;;
    esac
done

if [ "$DAYS_BACK" -gt 0 ]; then
    #TODO: Try to back date base on user given date
    forecast_date="`date +%Y-%m-%d -d "$DAYS_BACK days ago"`";
fi

# cd into bash script's root directory
cd $ROOT_DIR
echo "Current Working Directory set to -> $(pwd)"
if [ -z "$(find $CONFIG_FILE -name CONFIG.json)" ]; then
    echo "Unable to find $CONFIG_FILE file"
    exit 1
fi

HOST_ADDRESS=$(trimQuotes $(cat CONFIG.json | jq '.HOST_ADDRESS'))
HOST_PORT=$(cat CONFIG.json | jq '.HOST_PORT')
WINDOWS_HOST="$HOST_ADDRESS:$HOST_PORT"

RF_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.RF_DIR_PATH'))
KUB_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.KUB_DIR_PATH'))
RF_GRID_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.RF_GRID_DIR_PATH'))
FLO2D_RAINCELL_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.FLO2D_RAINCELL_DIR_PATH'))

OUTPUT_DIR=$(trimQuotes $(cat CONFIG.json | jq '.OUTPUT_DIR'))
STATUS_FILE=$(trimQuotes $(cat CONFIG.json | jq '.STATUS_FILE'))

HEC_HMS_MODEL_DIR=$(trimQuotes $(cat CONFIG.json | jq '.HEC_HMS_MODEL_DIR'))
HEC_HMS_DIR=$(trimQuotes $(cat CONFIG.json | jq '.HEC_HMS_DIR'))
HEC_DSSVUE_DIR=$(trimQuotes $(cat CONFIG.json | jq '.HEC_DSSVUE_DIR'))
DSS_INPUT_FILE=$(trimQuotes $(cat CONFIG.json | jq '.DSS_INPUT_FILE'))
DSS_OUTPUT_FILE=$(trimQuotes $(cat CONFIG.json | jq '.DSS_OUTPUT_FILE'))

INFLOW_DAT_FILE=$(trimQuotes $(cat CONFIG.json | jq '.INFLOW_DAT_FILE'))

current_date_time="`date +%Y-%m-%dT%H:%M:%S`";

main() {
    if [[ "$TAG" =~ [^a-zA-Z0-9\ ] ]]; then
        echo "Parameter for -T|--tag is \"$TAG\" invalid. It can onaly contain alphanumberic values."
        exit 1;
    fi
    if [ ! -z $TAG ]; then
        INFLOW_DAT_FILE=${INFLOW_DAT_FILE/.DAT/".$TAG.DAT"}
    fi

    if [ ! -z $WRF_OUT ] && [ -d $WRF_OUT ]; then
        RF_DIR_PATH=$WRF_OUT/RF
        KUB_DIR_PATH=$WRF_OUT/kelani-upper-basin
        RF_GRID_DIR_PATH=$WRF_OUT/colombo
        FLO2D_RAINCELL_DIR_PATH=$WRF_OUT/kelani-basin
        echo "WRF OUT paths changed to -> $RF_DIR_PATH, $KUB_DIR_PATH, $RF_GRID_DIR_PATH, $FLO2D_RAINCELL_DIR_PATH"
    fi

    # if [[ "$DSS_INPUT_FILE" =~ ^\$\{(HEC_HMS_MODEL_DIR)\} ]]; then
    #     DSS_INPUT_FILE=${DSS_INPUT_FILE/\$\{HEC_HMS_MODEL_DIR\}/$HEC_HMS_MODEL_DIR}
    # fi
    # if [[ "$DSS_OUTPUT_FILE" =~ ^\$\{(HEC_HMS_MODEL_DIR)\} ]]; then
    #     DSS_OUTPUT_FILE=${DSS_OUTPUT_FILE/\$\{HEC_HMS_MODEL_DIR\}/$HEC_HMS_MODEL_DIR}
    # fi
    DSS_INPUT_FILE=$(replaceStringVariable $DSS_INPUT_FILE "HEC_HMS_MODEL_DIR" $HEC_HMS_MODEL_DIR)
    echo "Set DSS_INPUT_FILE=$DSS_INPUT_FILE"
    DSS_OUTPUT_FILE=$(replaceStringVariable $DSS_OUTPUT_FILE "HEC_HMS_MODEL_DIR" $HEC_HMS_MODEL_DIR)
    echo "Set DSS_OUTPUT_FILE=$DSS_OUTPUT_FILE"

    echo "Start at $current_date_time $FORCE_EXIT"
    echo "Forecasting with Forecast Date: $forecast_date @ $forecast_time, Config File: $CONFIG_FILE, Root Dir: $ROOT_DIR"

    local isWRF=$(isWRFAvailable)
    local forecastStatus=$(alreadyForecast $ROOT_DIR/$STATUS_FILE $forecast_date)
    if [ $FORCE_RUN == true ]; then
        forecastStatus=0
    fi
    echo "isWRF $isWRF forecastStatus $forecastStatus"

    if [ $isWRF == 1 ] && [ $forecastStatus == 0 ]; then
        mkdir $OUTPUT_DIR

        # Read WRF forecast data, then create precipitation .csv for Upper Catchment 
        # using Theissen Polygen
        ./RFTOCSV.py -d $forecast_date -t $forecast_time \
            --wrf-rf $RF_DIR_PATH --wrf-kub $KUB_DIR_PATH \
            `[[ -z $TAG ]] && echo "" || echo "--tag $TAG"`

        # HACK: There is an issue with running HEC-HMS model, it gave a sudden value change after 1 day
        # We discovered that, this issue on 3.5 version, hence upgrade into 4.1
        # But with 4.1, it runs correctly when the data are saved by the HEC-HMS program
        # After run the model using the script, it can't reuse for a correct run again
        # Here we reuse a corrected model which can run using the script
        yes | cp -R 2008_2_Events_Hack/* 2008_2_Events/

        # Remove .dss files in order to remove previous results
        rm $DSS_INPUT_FILE
        rm $DSS_OUTPUT_FILE
        # Read Avg precipitation, then create .dss input file for HEC-HMS model
        ./dssvue/hec-dssvue.sh CSVTODSS.py --date $forecast_date \
            `[[ -z $TAG ]] && echo "" || echo "--tag $TAG"`

        # Change HEC-HMS running time window
        ./Update_HECHMS.py -d $forecast_date \
            `[[ $INIT_STATE == true ]] && echo "-i" || echo ""` \
            `[[ $CONTROL_INTERVAL == 0 ]] && echo "" || echo "-c $CONTROL_INTERVAL"` \
            `[[ -z $TAG ]] && echo "" || echo "--tag $TAG"`

        # Run HEC-HMS model
        cd $ROOT_DIR/$HEC_HMS_DIR
        ./HEC-HMS.sh -s ../2008_2_Events/2008_2_Events.script
        cd $ROOT_DIR

        # Read HEC-HMS result, then extract Discharge into .csv
        ./dssvue/hec-dssvue.sh DSSTOCSV.py --date $forecast_date \
            `[[ -z $TAG ]] && echo "" || echo "--tag $TAG"`

        # Read Discharge .csv, then create INFLOW.DAT file for FLO2D
        ./CSVTODAT.py  -d $forecast_date \
            `[[ -z $TAG ]] && echo "" || echo "--tag $TAG"`

        if [ $FORCE_EXIT == false ]; then
            # Send INFLOW.DAT file into Windows
            echo "Send POST request to $WINDOWS_HOST with INFLOW.DAT"
            curl -X POST --data-binary @$INFLOW_DAT_FILE  $WINDOWS_HOST/INFLOW.DAT?$forecast_date

            # Send RAINCELL.DAT file into Windows
            echo "Send POST request to $WINDOWS_HOST with RAINCELL.DAT"
            FLO2D_RAINCELL_FILE_PATH=$FLO2D_RAINCELL_DIR_PATH/created-$forecast_date/RAINCELL.DAT
            curl -X POST --data-binary @$FLO2D_RAINCELL_FILE_PATH  $WINDOWS_HOST/RAINCELL.DAT?$forecast_date

            # Send RUN_FLO2D.json file into Windows, and run FLO2D
            echo "Send POST request to $WINDOWS_HOST with RUN_FLO2D"
            curl -X POST --data-binary @./FLO2D/RUN_FLO2D.json  $WINDOWS_HOST/RUN_FLO2D?$forecast_date

            ./CopyToCMS.sh -d $forecast_date
        fi
    
        local writeStatus=$(alreadyForecast $ROOT_DIR/$STATUS_FILE $forecast_date)
        if [ $writeStatus == 0 ]; then
            writeForecastStatus $forecast_date $STATUS_FILE
        fi
    else
        echo "WARN: Already run the forecast. Quit"
        exit 1
    fi
}

isWRFAvailable() {
    local File_Pattern="*$forecast_date*.txt"
    if [ -z "$(find $RF_DIR_PATH -name $File_Pattern)" ]; then
      # echo "empty (Unable find files $File_Pattern)"
      echo 0
    else
      # echo "Found WRF output"
      echo 1
    fi
}

writeForecastStatus() {
    echo $1 >> $2
}

alreadyForecast() {
    local forecasted=0

    while IFS='' read -r line || [[ -n "$line" ]]; do
        if [ $2 == $line ]; then
            forecasted=1
            break
        fi
    done < "$1"
    echo $forecasted
}

main "$@"

# End of Forecast.sh