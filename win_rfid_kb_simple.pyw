from serial import Serial
from rdm880 import *
import time
import win32com.client
import sys
import winsound
from argparse import ArgumentParser


shell = win32com.client.Dispatch("WScript.Shell")


def checkCard(cardid, base, prefix, suffix):
	"""
	Called when a card is scanned by the reader.
	"""
	if base == 2:
		o = ''.join((bin(x)[2:].rjust(8, '0') for x in cardid))
	elif base == 8:
		o = ''.join(('%03o' % x for x in cardid))
	elif base == 10:
		o = ''.join(('%03d' % x for x in cardid))
	elif base == 16:
		o = ''.join(('%02X' % x for x in cardid))
	print "Card: %s" % o
	shell.SendKeys(prefix + o + suffix)


def main():
	parser = ArgumentParser()
	
	parser.add_argument('--baud', '-b',
		type=int,
		default=9600,
		help='Baud rate for RFID reader (default: %(default)s)')
	
	parser.add_argument('--device', '-d',
		default='COM4',
		help='Serial device that RFID reader is attached to (default: %(default)s)')
	
	parser.add_argument('--prefix', '-p',
		default='c',
		help='Keys to send before the RFID card ID (default: %(default)r)')

	parser.add_argument('--suffix', '-s',
		default='{enter}',
		help='Keys to send after the RFID card ID (default: %(default)r)')
		
	parser.add_argument('--beep', '-t',
		default='bell',
		help='Plays a tone after a successful scan from the reader, as (frequency,duration_ms).  Set to "none" to disable beeping, or "bell" to play the default system sound (normally ding.wav).  (default: %(default)r)')	
	
	group = parser.add_mutually_exclusive_group()
	
	group.add_argument('--bin', '-2',
		action='store_true', help='Type card ID in 8-bit binary')
	group.add_argument('--oct', '-8',
		action='store_true', help='Type card ID in 3-digit octal (default)')
	group.add_argument('--dec', '-0',
		action='store_true', help='Type card ID in 3-digit decimal')	
	group.add_argument('--hex', '-f',
		action='store_true', help='Type card ID in 2-digit hexadecimal')
	
	options = parser.parse_args()
	
	# define a "beep function".
	if options.beep == 'none':
		beepfn = lambda: False
	elif options.beep == 'bell':
		beepfn = winsound.MessageBeep
	else:
		freq, dur = [int(x) for x in options.beep.split(',', 2)]
		beepfn = lambda: winsound.Beep(freq, dur)

	base = 8
	if options.bin:
		base = 2
	elif options.dec:
		base = 10
	elif options.hex:
		base = 16
		
	prevcardid = None
	while True:
		try:
			io = Serial(options.device, options.baud, timeout=1)
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
							checkCard(cardid, base, options.prefix, options.suffix)
							beepfn()
					else:
						prevcardid = None
					time.sleep(0.1)
				except KeyboardInterrupt:
					return
				except:
					print sys.exc_info()[0]
					break
		except KeyboardInterrupt:
			print "Got control-c, quitting!"
			break
		except:
			# these are other errors that we should just swallow
			pass

if __name__ == '__main__':
	main()
