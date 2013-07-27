#!/usr/bin/env python

import serial
import RPi.GPIO as GPIO
import time, io, datetime
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
import sqlite3

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

print "opening cards db"
conn = sqlite3.connect("cards.db")
cursor = conn.cursor()
print "cards db opened"
opentime = config.getint("gpio","opentime")

try:
	pygame.mixer.pre_init(44100,-16,2,256)
	pygame.mixer.init()
	
	sounds = {}
	wavlist = os.listdir("sounds")
	for wav in wavlist:
		if wav.endswith(".wav"):
			sounds[wav] = pygame.mixer.Sound("sounds/" + wav)
	
	ping = pygame.mixer.Sound("Ping.wav")
	ping.play()
except:
	print "Error initializing sound"
	#todo: actually print the error itself

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
			if doorPress == ALERT_PRESS_TIME:
				if alertSubproc:
					alertSubproc.kill()
					alertSubproc = None
				else:
					try:
						ping.play()
					except:
						print "sound play failed"
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
				try:
					fridgebell.play(loops=-1)
				except:
					print "sound play failed"
		else:
			fridgeTime = 0.0
			try:
				fridgebell.stop()
			except:
				print "sound stop failed"
		time.sleep(0.05)
thread.start_new_thread(doorThread, ())


irc_connected = False
def handle_welcome(_,__):
	global irc_connected
	irc_connected = True

try:
	channel = config.get("irc","channel")
	irc = IRC(nick=config.get("irc","ircnick"), start_channels=[channel], version="1.0")
	irc.make_conn(config.get("irc","ircserver"), config.getint("irc","ircport"))
	irc.bind(handle_welcome, RPL_WELCOME)
except:
	print "IRC start failed"

thread.start_new_thread(asyncore.loop, ()) # i really should work the serial bit into asyncore, shouldn't i?

soundList = []

def checkCard(tagID):
	global doorTime
	global soundList
	cursor.execute("SELECT `enabled`,`username`,`description` FROM `rfid` WHERE `card_id`=?", (tagID,))
	result = cursor.fetchone()
	if result:
		if result[0]:
			try:
				if not soundList:
					print "creating new soundList"
					soundList = sounds.keys()
					random.shuffle(soundList)
				sounds[soundList.pop()].play()
				print "valid card, unlocking door for %s" % result[1]
				irc.tell(channel, ("Unlocking door for user %s with a %s" % (result[1], result[2])).encode("ascii",errors="ignore"))
			except:
				print sys.exc_info()
			#if result['soundfile']:
			#	print "soundfile is %s" % result['soundfile']
			doorTime = time.time() + opentime
		else:
			print "usage of disabled card %s for user %s" % (tagID, result[1])
	else:
		print "unknown card %s" % tagID
		try:
			irc.tell(channel, ("Unknown card %s" % tagID).encode("ascii",errors="ignore"))
		except:
			print sys.exc_info()

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

