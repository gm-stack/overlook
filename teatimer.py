import pygame
import wave
import os
import time
pygame.mixer.pre_init(44100,-16,2,256)
pygame.mixer.init()
sounds = {}
wavlist = os.listdir("ingress")
for wav in wavlist:
	if wav.endswith(".ogg"):
		wav2 = wav
		if wav.startswith("speech_number_"):
			wav2 = int(wav2[14:17])
		else:
			wav2 = wav2[7:-4]
		sounds[wav2] = pygame.mixer.Sound("ingress/" + wav)

def playwait(sound):
	sounds[sound].play()
	while pygame.mixer.get_busy():
		time.sleep(0.1)

def saytime(remaintime):
	minutes = int(remaintime/60)
	seconds = remaintime % 60
	if remaintime == 60:
		seconds = 60
		minutes = 0
	if minutes:
		playwait(minutes)
		playwait('minutes')
	if seconds:
		playwait(seconds)
		playwait('seconds')
	if minutes or seconds:
		playwait('remaining')
	else:
		playwait('complete')

starttime = int(time.time())
duration = 60
remaintime = duration
while remaintime > 0:
	elapsed = (int(time.time())-starttime)
	remaintime = duration - elapsed
	print remaintime
	time.sleep(1)
	if ((remaintime % 60 == 0) or 
		((remaintime < 180) and (remaintime % 30 == 0)) or 
		((remaintime < 60) and (remaintime % 10 == 0)) or 
		((remaintime < 30) and (remaintime % 5 == 0))):
			saytime(remaintime)

