import pygame
pygame.mixer.pre_init(44100,-16,2,2048)
pygame.mixer.init()
sound = pygame.mixer.Sound("sounds/Ping.wav")
sound.play()

