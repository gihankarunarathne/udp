#!/bin/bash

#
# ./Forecast.sh <FORECAST_DATE>
#	e.g. ./Forecast.sh 2017-03-22
#

trimQuotes() {
	tmp="${1%\"}"
	tmp="${tmp#\"}"
	echo $tmp
}

ROOT_DIR=$(pwd)
CONFIG_FILE='CONFIG.json'
if [ -z "$(find $ROOT_DIR/$CONFIG_FILE -name $CONFIG_FILE)" ]
then
	echo "Unable to find $CONFIG_FILE file"
	exit 1
fi

HOST_ADDRESS=$(trimQuotes $(cat CONFIG.json | jq '.HOST_ADDRESS'))
HOST_PORT=$(cat CONFIG.json | jq '.HOST_PORT')
WINDOWS_HOST="$HOST_ADDRESS:$HOST_PORT"

RF_DIR_PATH=$(trimQuotes $(cat CONFIG.json | jq '.RF_DIR_PATH'))
STATUS_FILE=$(trimQuotes $(cat CONFIG.json | jq '.STATUS_FILE'))
HEC_HMS_DIR=$(trimQuotes $(cat CONFIG.json | jq '.HEC_HMS_DIR'))
HEC_DSSVUE_DIR=$(trimQuotes $(cat CONFIG.json | jq '.HEC_DSSVUE_DIR'))

current_date_time="`date +%Y-%m-%dT%H:%M:%S`";
forecast_date="`date +%Y-%m-%d`";
if [ ! -z "$1" ]; then
	forecast_date=$1
fi

main() {
	echo "Start at $current_date_time"
	echo "Forecasting for $forecast_date"

	local isWRF=$(isWRFAvailable)
	local forecastStatus=$(alreadyForecast $ROOT_DIR/$STATUS_FILE $forecast_date)
	echo "isWRF $isWRF forecastStatus $forecastStatus"

	if [ $isWRF == 1 ] && [ $forecastStatus == 0 ]
	then
		# Read WRF forecast data, then create precipitation .csv for Upper Catchment 
		# using Theissen Polygen
		./RFTOCSV.py $forecast_date

		# Read Avg precipitation, then create .dss input file for HEC-HMS model
		./dssvue/hec-dssvue.sh CSVTODSS.py

		# Run HEC-HMS model
		cd $ROOT_DIR/$HEC_HMS_DIR
		./HEC-HMS.sh -s ../2008_2_Events/2008_2_Events.script
		cd $ROOT_DIR

		# Read HEC-HMS result, then extract Discharge into .csv
		./dssvue/hec-dssvue.sh DSSTOCSV.py

		# Read Discharge .csv, then create INFLOW.DAT file for FLO2D
		./CSVTODAT.py

		# Send INFLOW.DAT file into Windows, and run FLO2D
		echo "Send POST request to $WINDOWS_HOST"
		curl -X POST --data-binary @./INFLOW.DAT  $WINDOWS_HOST/INFLOW.DAT?$forecast_date
	
		#writeForecastStatus $forecast_date $STATUS_FILE
	else
		echo "WARN: Already run the forecast. Quit"
		exit 1
	fi
}

isWRFAvailable() {
	local File_Pattern="*$forecast_date*.txt"
	if [ -z "$(find $ROOT_DIR/$RF_DIR_PATH -name $File_Pattern)" ]
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