#!/usr/bin/python3

import pymysql.cursors

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