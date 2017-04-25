#!/bin/bash

usage() {
cat <<EOF
Usage: ./Forecast.sh [-d FORECAST_DATE]

	-h 	Show usage
	-d 	Date which need to run the forecast in YYYY-MM-DD format. Default is current date.
EOF
}

forecast_date="`date +%Y-%m-%d`";

# Extract user arguments
while getopts hd: opt; do
    case $opt in
        h)
            usage
            exit 0
            ;;
        d)  forecast_date=$OPTARG
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
done

curl -X POST --data-binary @../FLO2D/Org_INFLOW.DAT  localhost:8080/INFLOW.DAT?$forecast_date

curl -X POST --data-binary @../FLO2D/RAINCELL.DAT  localhost:8080/RAINCELL.DAT?$forecast_date

curl -X POST -d @../FLO2D/RUN_FLO2D.json localhost:8080/RUN_FLO2D?$forecast_date --header "Content-Type: application/json"
