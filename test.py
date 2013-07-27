from serial import Serial
from rdm880 import *
import time

io = Serial('/dev/ttyAMA0', 9600, timeout=1)

while True:
	p = Packet(ISO14443A.Request)
	reply = p.execute(io)
	print reply
	p = Packet(ISO14443A.Anticollision)
	reply = p.execute(io)
	print reply
	time.sleep(0.1)
