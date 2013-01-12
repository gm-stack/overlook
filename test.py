from serial import Serial
from rdm880 import *

io = Serial('COM4', 9600, timeout=1)

while True:
	p = Packet(ISO14443A.Request)
	reply = p.execute(io)
	p = Packet(ISO14443A.Anticollision)
	reply = p.execute(io)
	if reply.data:
		print reply.data