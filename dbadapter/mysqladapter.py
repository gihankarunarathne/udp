#!/usr/bin/python3

import pymysql.cursors, hashlib, collections, json, traceback

MyStruct = collections.namedtuple("MyStruct", "field1 field2 field3")

class mysqladapter :
    def __init__(self, host="localhost", user="root", password="", db="curw") :
        '''Initialize Database Connection'''
        # Open database connection
        self.connection = pymysql.connect(host=host,
                            user=user,
                            password=password,
                            db=db)

        # prepare a cursor object using cursor() method
        cursor = self.connection.cursor()

        # execute SQL query using execute() method.
        cursor.execute("SELECT VERSION()")

        # Fetch a single row using fetchone() method.
        data = cursor.fetchone()

        print ("Database version : %s " % data)

        # disconnect from server
        #self.connection.close()


    def getEventId(self, metaData) :
        '''Get the event id for given meta data

        :param dict metaData: Dict of Meta Data that use to create the hash
        Meta Data should contains all of following keys s.t.
        {
            'station': 'Hanwella',
            'variable': 'Discharge',
            'unit': 'm3/s',
            'type': 'Forecast',
            'source': 'HEC-HMS',
            'name': 'HEC-HMS 1st',
            'start_date': '2017-05-01 00:00:00',
            'end_date': '2017-05-03 23:00:00'
        }
        If start_date is not set, use default date as "01 Jan 1970 00:00:00 GMT"
        If end_date   is not set, use default date as "01 Jan 2100 00:00:00 GMT"

        :return str: sha256 hash value in hex format (length of 64 characters)
        '''
        print('getEventId')
        eventId = None
        print(json.dumps(metaData, sort_keys=True).encode("ascii"))
        m = hashlib.sha256()
        m.update(json.dumps(metaData, sort_keys=True).encode("ascii"))
        possibleId = m.hexdigest()
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT 1 FROM `run` WHERE `id`=%s"

                cursor.execute(sql, possibleId)
                isExist = cursor.fetchone()
                if isExist is not None :
                    eventId = possibleId
        except Exception as e :
            traceback.print_exc()
        finally:
            return eventId


    def createEventId(self, metaData) :
        '''Create a new event id for given meta data

        :param dict metaData: Dict of Meta Data that use to create the hash
        Meta Data should contains all of following keys s.t.
        {
            'station': 'Hanwella',
            'variable': 'Precipitation',
            'unit': 'mm',
            'type': 'Forecast',
            'source': 'WRF',
            'name': 'WRF 1st',
            'start_date': '2017-05-01 00:00:00',
            'end_date': '2017-05-03 23:00:00'
        }

        :return str: sha256 hash value in hex format (length of 64 characters)
        '''
        print('createEventId')
        #d = MyStruct("foo", "bar", "baz")
        #d = { 'name': 'Gihan', 'send': '123' }
        print(json.dumps(metaData, sort_keys=True).encode("ascii"))
        m = hashlib.sha256()
        m.update(json.dumps(metaData, sort_keys=True).encode("ascii"))
        eventId = m.hexdigest()
        try:
            with self.connection.cursor() as cursor:
                sql = [
                    "SELECT `id` as `stationId` FROM `station` WHERE `name`=%s",
                    "SELECT `id` as `variableId` FROM `variable` WHERE `variable`=%s",
                    "SELECT `id` as `unitId` FROM `unit` WHERE `unit`=%s",
                    "SELECT `id` as `typeId` FROM `type` WHERE `type`=%s",
                    "SELECT `id` as `sourceId` FROM `source` WHERE `source`=%s"
                ]

                cursor.execute(sql[0], (metaData['station']))
                stationId = cursor.fetchone()[0]
                cursor.execute(sql[1], (metaData['variable']))
                variableId = cursor.fetchone()[0]
                cursor.execute(sql[2], (metaData['unit']))
                unitId = cursor.fetchone()[0]
                cursor.execute(sql[3], (metaData['type']))
                typeId = cursor.fetchone()[0]
                cursor.execute(sql[4], (metaData['source']))
                sourceId = cursor.fetchone()[0]

                print('stationId', metaData['station'], '>', stationId)
                print('variableId', metaData['variable'], '>', variableId)
                print('unitId', metaData['unit'], '>', unitId)
                print('typeId', metaData['type'], '>', typeId)
                print('sourceId', metaData['source'], '>', sourceId)

                sql = "INSERT INTO `run` (`id`, `name`, `start_date`, `end_date`, `station`, `variable`, `unit`, `type`, `source`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                sqlValues = (
                    eventId,
                    metaData['name'],
                    metaData['start_date'],
                    metaData['end_date'],
                    stationId,
                    variableId,
                    unitId,
                    typeId,
                    sourceId
                )
                print(sqlValues)
                cursor.execute(sql, sqlValues)
                self.connection.commit()

        except Exception as e :
            traceback.print_exc()

        return eventId

    def insertTimeseries(self, eventId, timeseries) :
        '''Insert timeseries into the db against given eventId'''
        print('insertTimeSeries')
        rowCount = 0
        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO `data` (`id`, `time`, `value`) VALUES (%s, %s, %s)"

                newTimeseries = []
                for t in timeseries :
                    t[1] = round(float(t[1]), 3)
                    t.insert(0, eventId)
                    newTimeseries.append(t)

                # print(newTimeseries[:10])
                rowCount = cursor.executemany(sql, (newTimeseries))
                self.connection.commit()

        except Exception as e :
            traceback.print_exc()
        finally:
            return rowCount

    def deleteTimeseries(self, eventId) :
        '''Delete given timeseries from the database'''
        rowCount = 0
        try:
            with self.connection.cursor() as cursor:
                sql = "DELETE FROM `data` WHERE `id`=%s"

                rowCount = cursor.execute(sql, (eventId))
                self.connection.commit()

        except Exception as e :
            traceback.print_exc()
        finally:
            return rowCount

    def getEventIds(self) :
        '''Get event ids set according to given meta data'''
        print('getEventIds')

    def retrieveTimeseries(self) :
        '''Get timeseries'''
        print('retrieveTimeSeries')

