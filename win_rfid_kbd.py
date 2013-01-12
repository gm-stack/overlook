from serial import Serial
from rdm880 import *
import MySQLdb, MySQLdb.cursors
import time
import win32com.client
import ConfigParser

config = ConfigParser.ConfigParser()
config.read("win_rfid_kbd.ini")

print "connecting to MySQL"
conn = MySQLdb.connect(	host=config.get("mysql","host"),
			user=config.get("mysql","user"),
			passwd=config.get("mysql","passwd"),
			db=config.get("mysql","db"), 
			cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
cursor = conn.cursor()

io = Serial('COM4', 9600, timeout=1)

shell = win32com.client.Dispatch("WScript.Shell")

def checkCard(cardid_hex):
	print "card id is " + cardid_hex
	cursor.execute("SELECT * FROM `rfid` WHERE `card_id`=%(cardid)s", {'cardid': cardid_hex})
	result = cursor.fetchone()
	print result
	shell.SendKeys(result['username'] + "{enter}")

while True:
	p = Packet(ISO14443A.Request)
	reply = p.execute(io)
	p = Packet(ISO14443A.Anticollision)
	reply = p.execute(io)
	cardid = reply.data
	if cardid:
		cardid_hex = "".join(map(lambda x: "%.2X" % x , cardid))
		if cardid_hex != prevcardid:
			prevcardid = cardid_hex
			checkCard(cardid_hex)
	else:
		prevcardid = None
	time.sleep(0.1)