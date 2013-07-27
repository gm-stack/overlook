from serial import Serial
from rdm880 import *
import time
import win32com.client
import sys
import binascii

shell = win32com.client.Dispatch("WScript.Shell")

def checkCard(cardid):
	# openbravo only likes numeric cards
	print cardid
	o = ''.join(('%03o' % x for x in cardid))
	print "card id is %s" % o
	
	shell.SendKeys("c" + o + "{enter}")

while True:
	try:
		io = Serial('COM4', 9600, timeout=1)
		while True:
			try:
				p = Packet(ISO14443A.Request)
				reply = p.execute(io)
				p = Packet(ISO14443A.Anticollision)
				reply = p.execute(io)
				cardid = reply.data
				if cardid:
					if cardid != prevcardid:
						prevcardid = cardid
						checkCard(cardid)
				else:
					prevcardid = None
				time.sleep(0.1)
			except KeyboardInterrupt:
				sys.exit()
			except:
				print sys.exc_info()[0]
				break;
	except:
		pass
