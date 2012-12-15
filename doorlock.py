#!/usr/bin/env python

import serial
import RPi.GPIO as GPIO
import time, io
import MySQLdb, MySQLdb.cursors
import ConfigParser

config = ConfigParser.ConfigParser()
config.read("doorlock.ini")

GPIO_PIN = config.getint("gpio","gpio_pin")

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False) # disable warning for already having GPIO open
GPIO.setup(GPIO_PIN, GPIO.OUT)
GPIO.output(GPIO_PIN, GPIO.LOW)

ser = serial.Serial(config.get("rfid","port"), config.getint("rfid","baud"), timeout=1)

conn = MySQLdb.connect(	host=config.get("mysql","host"),
			user=config.get("mysql","user"),
			passwd=config.get("mysql","passwd"),
			db=config.get("mysql","db"), 
			cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
cursor = conn.cursor()

def toggleDoor():
	GPIO.output(GPIO_PIN, GPIO.HIGH)
	time.sleep(2)
	GPIO.output(GPIO_PIN, GPIO.LOW)

def checkCard(tagID):
	cursor.execute("SELECT * FROM `rfid` WHERE `card_id`=%(tagID)s", {'tagID': tagID})
	result = cursor.fetchone()
	if result:
		if result['enabled']:
			print "valid card, unlocking door for %s" % result['username']
			if result['soundfile']:
				print "soundfile is %s" % result['soundfile']
			toggleDoor()
		else:
			print "usage of disabled card %s for user %s" % (result['card_id'], result['username'])
	else:
		print "unknown card %s" % tagID

while True:
	data = ser.read(14)
	if len(data) == 14:
		if ord(data[0]) != 2:
			print "invalid header"
			continue
		if ord(data[13]) != 3:
			print "invalid footer"
			continue
		tagID = data[1:11]
		checksum = int(data[11:13],16)
		databytes = []
		for i in range(0,10,2):
			tagbyte = tagID[i:i+2]
			databytes += [int(tagbyte,16)]
		calcchecksum = 0
		for byte in databytes:
			calcchecksum = calcchecksum ^ byte
		if (calcchecksum != checksum):
			print "invalid checksum"
			continue
		print "got card, ID is %s" % databytes
		checkCard(tagID)
	else:
		if len(data) > 0: print "invalid read len %i" % len(data)

