import pygame, sys  # import pygame and sys

clock = pygame.time.Clock()  # set up the clock

from pygame.locals import *  # import pygame modules

pygame.init()  # initiate pygame

pygame.display.set_caption('Shafiq''s Pygame Window')  # set the window name

WINDOW_SIZE = (400, 400)  # set up window size

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)  # initiate screen

while True:  # game loop
    for event in pygame.event.get():  # event loop
        if event.type == QUIT:  # check for window quit
            pygame.quit()  # stop pygame
            sys.exit()  # stop script

    pygame.display.update()  # update display
    clock.tick(60)  # maintain 60 fps
