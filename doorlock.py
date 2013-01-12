#!/usr/bin/env python

import serial
import RPi.GPIO as GPIO
import time, io, datetime
import MySQLdb, MySQLdb.cursors
import ConfigParser
import asyncore
import thread
import pygame
import pyaudio, wave
import os
import random
import subprocess
import shlex
from ircasync import *
from rdm880 import *

config = ConfigParser.ConfigParser()
config.read("doorlock.ini")

LOCK_PIN = config.getint("gpio","lock_pin")

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False) # disable warning for already having GPIO open
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.output(LOCK_PIN, GPIO.LOW)

EXIT_PIN = config.getint("gpio","exit_pin")
FRIDGE_PIN = config.getint("gpio","fridge_pin")

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(EXIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(FRIDGE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

ser = serial.Serial(config.get("rfid","port"), config.getint("rfid","baud"), timeout=1)

print "connecting to MySQL"
conn = MySQLdb.connect(	host=config.get("mysql","host"),
			user=config.get("mysql","user"),
			passwd=config.get("mysql","passwd"),
			db=config.get("mysql","db"), 
			cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
cursor = conn.cursor()
print "MySQL connected"
opentime = config.getint("gpio","opentime")

pygame.mixer.pre_init(44100,-16,2,256)
pygame.mixer.init()

sounds = {}
wavlist = os.listdir("sounds")
for wav in wavlist:
	if wav.endswith(".wav"):
		sounds[wav] = pygame.mixer.Sound("sounds/" + wav)

ping = pygame.mixer.Sound("Ping.wav")
ping.play()

ALERT_COMMAND = shlex.split(config.get("alert","command"))
ALERT_PRESS_TIME = config.getint("alert","presstime")

doorTime = 0.0
fridgebell = pygame.mixer.Sound("bell.wav")
fridgebell_playing = False
def doorThread():
	global doorTime
	fridgeTime = 0
	doorPress = 0
	alertSubproc = None
	while True:
		if GPIO.input(EXIT_PIN):
			doorPress += 1
			print "doorPress is %i" % doorPress
			if doorPress == ALERT_PRESS_TIME:
				if alertSubproc:
					alertSubproc.kill()
				else:
					ping.play()
					ping.play()
					alertSubproc = subprocess.Popen(ALERT_COMMAND, stdout=subprocess.PIPE, shell=False)
			if not ((time.time() - doorTime) < 0):
				doorTime = time.time() + 2
				print "button pushed, unlocking door"
				try:
					irc.tell(channel, "Unlocking door for exiting user")
				except:
					pass
		else:
			doorPress = 0	
		if (time.time() - doorTime) < 0:
			GPIO.output(LOCK_PIN, GPIO.HIGH)
		else:
			GPIO.output(LOCK_PIN, GPIO.LOW)
		if GPIO.input(FRIDGE_PIN):
			fridgeTime += 1
			print "fridge has been open for %f seconds" % (fridgeTime/20.0)
			if fridgeTime == 30*20:
				print "playing bell"
				fridgebell.play(loops=-1)
		else:
			fridgeTime = 0.0
			fridgebell.stop()
		time.sleep(0.05)
thread.start_new_thread(doorThread, ())

irc_connected = False
def handle_welcome(_,__):
	global irc_connected
	irc_connected = True

channel = config.get("irc","channel")
irc = IRC(nick=config.get("irc","ircnick"), start_channels=[channel], version="1.0")
irc.make_conn(config.get("irc","ircserver"), config.getint("irc","ircport"))
irc.bind(handle_welcome, RPL_WELCOME)
thread.start_new_thread(asyncore.loop, ()) # i really should work the serial bit into asyncore, shouldn't i?

def checkCard(tagID):
	global doorTime
	cursor.execute("SELECT * FROM `rfid` WHERE `card_id`=%(cardid)s", {'cardid': tagID})
	result = cursor.fetchone()
	if result:
		if result['enabled']:
			random.choice(sounds.values()).play()
			print "valid card, unlocking door for %s" % result['username']
			try:
				irc.tell(channel, ("Unlocking door for user %s" % result['username']).encode("ascii",errors="ignore"))
			except:
				print sys.exc_info()
			if result['soundfile']:
				print "soundfile is %s" % result['soundfile']
			doorTime = time.time() + opentime
		else:
			print "usage of disabled card %s for user %s" % (result['card_id'], result['username'])
	else:
		print "unknown card %s" % tagID

prevcardid = None
while True:
	p = Packet(ISO14443A.Request)
	reply = p.execute(ser)
	p = Packet(ISO14443A.Anticollision)
	reply = p.execute(ser)
	cardid = reply.data
	if cardid:
		cardid_hex = "".join(map(lambda x: "%.2X" % x , cardid))
		if cardid_hex != prevcardid:
			prevcardid = cardid_hex
			checkCard(cardid_hex)
	else:
		prevcardid = None
	time.sleep(0.1)
	#data = ser.read(14)
	#if len(data) == 14:
	#	if ord(data[0]) != 2:
	#		print "invalid header"
	#		continue
	#	if ord(data[13]) != 3:
	#		print "invalid footer"
	#		continue
	#	tagID = data[1:11]
	#	checksum = int(data[11:13],16)
	#	databytes = []
	#	for i in range(0,10,2):
	#		tagbyte = tagID[i:i+2]
	#		databytes += [int(tagbyte,16)]
	#	calcchecksum = 0
	#	for byte in databytes:
	#		calcchecksum = calcchecksum ^ byte
	#	if (calcchecksum != checksum):
	#		print "invalid checksum"
	#		continue
	#	print "got card, ID is %s" % databytes
	#	if tagID != "0000000000": # RFID reader sometimes spits out all zeros for some reason, but this passes checksum because 0 ^ 0 = 0
	#		checkCard(tagID)
	#else:
	#	if len(data) > 0: print "invalid read len %i" % len(data)

