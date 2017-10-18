#!/usr/bin/python3
import sys, traceback, csv, json, datetime, getopt, os
from datetime import datetime

def extractForecastTimeseries(timeseries, date, time) :
    '''
    Extracted timeseries upward from given date and time
    E.g. Consider timeseries 2017-09-01 to 2017-09-03
    date: 2017-09-01 and time: 14:00:00 will extract a timeseries which contains 
    values that timestamp onwards
    '''
    print('LibForecastTimeseries:: extractForecastTimeseries')
    dateTime = datetime.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
    newTimeseries = []
    for i, tt in enumerate(timeseries) :
        ttDateTime = datetime.strptime(tt[0], '%Y-%m-%d %H:%M:%S')
        if ttDateTime > dateTime :
            newTimeseries = timeseries[i:]
            break
    return newTimeseries


def extractForecastTimeseriesInDays(timeseries) :
    '''
    Devide into multiple timeseries for each day
    E.g. Consider timeseries 2017-09-01 14:00:00 to 2017-09-03 23:00:00
    will devide into 3 timeseries with
    [
        [2017-09-01 14:00:00-2017-09-01 23:00:00], 
        [2017-09-02 14:00:00-2017-09-02 23:00:00], 
        [2017-09-03 14:00:00-2017-09-03 23:00:00]
    ]
    '''
    newTimeseries = []
    if len(timeseries) > 0 :
        groupTimeseries = []
        isDateTimeObs = isinstance(timeseries[0][0], datetime)
        prevDate = timeseries[0][0] if isDateTimeObs else datetime.strptime(timeseries[0][0], '%Y-%m-%d %H:%M:%S')
        prevDate = prevDate.replace(hour=0, minute=0, second=0, microsecond=0)
        for tt in timeseries :
            # Match Daily
            ttDateTime = tt[0] if isDateTimeObs else datetime.strptime(tt[0], '%Y-%m-%d %H:%M:%S')
            if prevDate == ttDateTime.replace(hour=0, minute=0, second=0, microsecond=0) :
                groupTimeseries.append(tt)
            else :
                newTimeseries.append(groupTimeseries[:])
                groupTimeseries = []
                prevDate = ttDateTime.replace(hour=0, minute=0, second=0, microsecond=0)
                groupTimeseries.append(tt)

    return newTimeseries
