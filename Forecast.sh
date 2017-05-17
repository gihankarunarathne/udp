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
	-r 	ROOT_DIR which is program running directory. Default is Forecast.sh exist directory.
	-b 	Run forecast specified DAYS_BACK with respect to current date. Expect an integer.
		When specified -d option will be ignored.
	-f 	Force run forecast. Even the forecast already run for the particular day, run again. Default is false.
	-i 	Initiate a State at the end of HEC-HMS run
	-s 	Store Timeseries data on MySQL database
EOF
}

trimQuotes() {
	tmp="${1%\"}"
	tmp="${tmp#\"}"
	echo $tmp
}

forecast_date="`date +%Y-%m-%d`";
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INIT_DIR=$(pwd)
CONFIG_FILE=$ROOT_DIR/CONFIG.json
DAYS_BACK=0
FORCE_RUN=false
INIT_STATE=false
STORE_DATA=false
# Extract user arguments
while getopts hd:c:r:b:fis opt; do
    case $opt in
        h)
            usage
            exit 0
            ;;
        d)  forecast_date=$OPTARG
            ;;
        c)  CONFIG_FILE=$OPTARG
            ;;
        r)  ROOT_DIR=$OPTARG
			;;
		b)  DAYS_BACK=$OPTARG
			;;
		f)  FORCE_RUN=true
			;;
		i)  INIT_STATE=true
			;;
		s)  STORE_DATA=true
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
echo $(pwd)
if [ -z "$(find $CONFIG_FILE -name CONFIG.json)" ]
then
	echo "Unable to find $CONFIG_FILE file"
	exit 1
fi

HOST_ADDRESS=$(trimQuotes $(cat CONFIG.json | jq '.HOST_ADDRESS'))
HOST_PORT=$(cat CONFIG.json | jq '.HOST_PORT')
WINDOWS_HOST="$HOST_ADDRESS:$HOST_PORT"

RF_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.RF_DIR_PATH'))
RF_GRID_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.RF_GRID_DIR_PATH'))
FLO2D_RAINCELL_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.FLO2D_RAINCELL_DIR_PATH'))
OUTPUT_DIR=$(trimQuotes $(cat CONFIG.json | jq '.OUTPUT_DIR'))
STATUS_FILE=$(trimQuotes $(cat CONFIG.json | jq '.STATUS_FILE'))
HEC_HMS_DIR=$(trimQuotes $(cat CONFIG.json | jq '.HEC_HMS_DIR'))
HEC_DSSVUE_DIR=$(trimQuotes $(cat CONFIG.json | jq '.HEC_DSSVUE_DIR'))
DSS_INPUT_FILE=$(trimQuotes $(cat CONFIG.json | jq '.DSS_INPUT_FILE'))
DSS_OUTPUT_FILE=$(trimQuotes $(cat CONFIG.json | jq '.DSS_OUTPUT_FILE'))

current_date_time="`date +%Y-%m-%dT%H:%M:%S`";

main() {
	echo "Start at $current_date_time"
	echo "Forecasting with Forecast Date: $forecast_date, Config File: $CONFIG_FILE, Root Dir: $ROOT_DIR"

	local isWRF=$(isWRFAvailable)
	local forecastStatus=$(alreadyForecast $ROOT_DIR/$STATUS_FILE $forecast_date)
	if [ $FORCE_RUN == true ]
	then
		forecastStatus=0
	fi
	echo "isWRF $isWRF forecastStatus $forecastStatus"

	if [ $isWRF == 1 ] && [ $forecastStatus == 0 ]
	then
		mkdir $OUTPUT_DIR
		
		# Read WRF forecast data, then create precipitation .csv for Upper Catchment 
		# using Theissen Polygen
		./RFTOCSV.py $forecast_date

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
		./dssvue/hec-dssvue.sh CSVTODSS.py $forecast_date

		# Change HEC-HMS running time window
		./Update_HECHMS.py -d $forecast_date `[[ $INIT_STATE == true ]] && echo "-i" || echo ""`

		# Run HEC-HMS model
		cd $ROOT_DIR/$HEC_HMS_DIR
		./HEC-HMS.sh -s ../2008_2_Events/2008_2_Events.script
		cd $ROOT_DIR

		# Read HEC-HMS result, then extract Discharge into .csv
		./dssvue/hec-dssvue.sh DSSTOCSV.py $forecast_date

		# Read Discharge .csv, then create INFLOW.DAT file for FLO2D
		./CSVTODAT.py $forecast_date
		exit 0

		# Send INFLOW.DAT file into Windows
		echo "Send POST request to $WINDOWS_HOST with INFLOW.DAT"
		curl -X POST --data-binary @./FLO2D/INFLOW.DAT  $WINDOWS_HOST/INFLOW.DAT?$forecast_date

		# Send RAINCELL.DAT file into Windows
		echo "Send POST request to $WINDOWS_HOST with RAINCELL.DAT"
		FLO2D_RAINCELL_FILE_PATH=$FLO2D_RAINCELL_DIR_PATH/created-$forecast_date/RAINCELL.DAT
		curl -X POST --data-binary @$FLO2D_RAINCELL_FILE_PATH  $WINDOWS_HOST/RAINCELL.DAT?$forecast_date

		# Send RUN_FLO2D.json file into Windows, and run FLO2D
		echo "Send POST request to $WINDOWS_HOST with RUN_FLO2D"
		curl -X POST --data-binary @./FLO2D/RUN_FLO2D.json  $WINDOWS_HOST/RUN_FLO2D?$forecast_date

		./CopyToCMS.sh -d $forecast_date
	
		local writeStatus=$(alreadyForecast $ROOT_DIR/$STATUS_FILE $forecast_date)
		if [ $writeStatus == 0 ]
		then
			writeForecastStatus $forecast_date $STATUS_FILE
		fi
	else
		echo "WARN: Already run the forecast. Quit"
		exit 1
	fi
}

isWRFAvailable() {
	local File_Pattern="*$forecast_date*.txt"
	if [ -z "$(find $RF_DIR_PATH -name $File_Pattern)" ]
	then
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
    	if [ $2 == $line ] 
    	then
    		forecasted=1
    		break
    	fi
	done < "$1"
	echo $forecasted
}

main "$@"

# End of Forecast.sh