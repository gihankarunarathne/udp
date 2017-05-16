#!/usr/bin/python3

import pymysql.cursors

class MySQLAdapter :
    def __init__(self) :
        '''Initialize Database Connection'''
        # Open database connection
        db = pymysql.connect(host="localhost",
                            user="curw",
                            password="curw@123",
                            db="curw")

        # prepare a cursor object using cursor() method
        cursor = db.cursor()

        # execute SQL query using execute() method.
        cursor.execute("SELECT VERSION()")

        # Fetch a single row using fetchone() method.
        data = cursor.fetchone()

        print ("Database version : %s " % data)

        # disconnect from server
        db.close()

    def getEventId(self) :
        '''Get the event id for given meta data'''

    def createEventId(self) :
        '''Create a new event id for given meta data'''

    def insertTimeSeries(self, eventId, timeseries) :
        '''Insert timeseries into the db against given eventId'''

    def getEventIds(self) :
        '''Get event ids set according to given meta data'''

    def retrieveTimeSeries(self) :
        '''Get timeseries'''