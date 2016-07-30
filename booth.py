#! /usr/bin/python

# @author: porcej@gmail.com
# @date: 7/16/2016
# @description: A simple photobooth class for the raspberry pi

import pygame
import picamera
import os
import RPi.GPIO as GPIO
import time
from time import sleep
import PIL
from PIL import Image
import sys
import cups


class Photobooth(object):
    #  A simple photobooth class for the raspberry pi

    #  capture_resolution = (2592, 1944)    # Pycamera rev 1.3
    capture_resolution = (3280, 2464)       # Pycamera rev 2.1

    screen = object

    gpioPins = {
        'a': {'button': 17, 'indicator': 27},
        'b': {'button': 22, 'indicator': 5},
        'c': {'button': 6, 'indicator': 13},
        'd': {'button': 19, 'indicator': 26},
        'flash': {'indicator': 16},
        'shutdown': {'button': 4}
    }

    # Photocard Templates
    templates = {
        'a': {
            'size': (1800, 1200),
            'card': 'template_a.jpg',
            'images': [
                {'size': (807, 538), 'origin': (75, 443), 'rotation': 0},
                {'size': (807, 538), 'origin': (917, 443), 'rotation': 0}
            ]
        },
        'b': {
            'size': (1800, 1200),
            'card': 'template_b.jpg',
            'images': [
                {'size': (1089, 726), 'origin': (676, 57), 'rotation': 0},
                {'size': (540, 360), 'origin': (676, 796), 'rotation': 0},
                {'size': (540, 360), 'origin': (1225, 796), 'rotation': 0},
            ]
        },
        'c': {
            'size': (1800, 1200),
            'card': 'template_c.jpg',
            'images': [
                {'size': (1089, 726), 'origin': (35, 57), 'rotation': 0},
                {'size': (540, 360), 'origin': (35, 796), 'rotation': 0},
                {'size': (540, 360), 'origin': (584, 796), 'rotation': 0},
            ]
        },
        'd': {
            'size': (1800, 1200),
            'card': 'template_d.jpg',
            'images': [
                {'size': (579, 386), 'origin': (15, 609), 'rotation': 90},
                {'size': (579, 386), 'origin': (416, 609), 'rotation': 90},
                {'size': (579, 386), 'origin': (817, 609), 'rotation': 90},
                {'size': (579, 386), 'origin': (15, 15), 'rotation': 90},
                {'size': (579, 386), 'origin': (416, 15), 'rotation': 90},
                {'size': (579, 386), 'origin': (817, 15), 'rotation': 90},
            ]
        },
        'a_': {
            'size': (1280, 800),
            'card': 'template_a.jpg',
            'images': [
                {'size': (776, 485), 'origin': (18, 12), 'rotation': 90},
                {'size': (776, 485), 'origin': (521, 12), 'rotation': 90}
            ]
        },
        'b_': {
            'size': (1280, 800),
            'card': 'template_b.jpg',
            'images': [
                {'size': (472, 295), 'origin': (12, 70), 'rotation': 0},
                {'size': (472, 295), 'origin': (12, 435), 'rotation': 0},
                {'size': (472, 295), 'origin': (496, 70), 'rotation': 0},
                {'size': (472, 295), 'origin': (496, 435), 'rotation': 0}
            ]
        },
        'c_': {
            'size': (1280, 800),
            'card': 'template_a.jpg',
            'images': [
                {'size': (384, 240), 'origin': (12, 406), 'rotation': 90},
                {'size': (384, 240), 'origin': (264, 406), 'rotation': 90},
                {'size': (384, 240), 'origin': (516, 406), 'rotation': 90},
                {'size': (384, 240), 'origin': (768, 406), 'rotation': 90},
                {'size': (384, 240), 'origin': (12, 10), 'rotation': 90},
                {'size': (384, 240), 'origin': (264, 10), 'rotation': 90},
                {'size': (384, 240), 'origin': (516, 10), 'rotation': 90},
                {'size': (384, 240), 'origin': (768, 10), 'rotation': 90}
            ]
        }
    }

    # Default constructor
    def __init__(self):

        # Initilize the application
        # ====================================================================
        self.running = True
        self.currentAction = None

        # Initilize the printer(s)
        # ====================================================================
        self.printServer = cups.Connection()
        printers = self.printServer.getPrinters()
        self.currentPrinter = 0
        self.doPrint = False

        if len(printers.keys()) > 0:
            self.doPrint = True

        # Initilize screen
        # ====================================================================
        pygame.init()
        pygame.mouse.set_visible(0)
        screenSize = (pygame.display.Info().current_w,
                      pygame.display.Info().current_h)

        self.screen = pygame.display.set_mode(screenSize, pygame.FULLSCREEN)

        # Initilize GPIO
        # ====================================================================
        # disabled errors when ready LED is already ON
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Prepare GPIO to accept buttons
        for action, pins in Photobooth.gpioPins.iteritems():
            # Initialize flash
            if action is 'flash':
                # Handle Flash Pin
                GPIO.setup(pins['indicator'], GPIO.OUT)    # flash relay
                # Turn off flash relay
                GPIO.output(pins['indicator'], True)

            elif action is 'shutdown':
                GPIO.setup(pins['button'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            else:
                # Prepare buttons
                GPIO.setup(pins['button'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

                # Prepare indicator lamps
                GPIO.setup(pins['indicator'], GPIO.OUT)    # ready LED
                GPIO.output(pins['indicator'], False)

        # Initilize camera
        # ====================================================================
        self.cam = picamera.PiCamera()
        self.cam.awb_mode = 'auto'
        self.cam.iso = 125   # 300
        self.cam.annotate_text_size = 72

    # Incraments to the next printer
    def nextPrinter(self):
        printers = self.printServer.getPrinters()
        np = self.currentPrinter
        printerCount = len(printers.keys())
        if printerCount > 0:
            self.doPrint = True
            if np >= printerCount:
                self.currentPrinter = 0
            else:
                self.currentPrinter = np
        else:
            self.doPrint = False

    # On screen text message
    def displayStatus(self, status):
        self.screen.fill((0, 0, 0))

        font = pygame.font.SysFont("monospace", 72)
        text = font.render(status, True, (255, 255, 255))

        # Display in the center of the screen
        textrect = text.get_rect()
        textrect.centerx = self.screen.get_rect().centerx
        textrect.centery = self.screen.get_rect().centery

        self.screen.blit(text, textrect)

        pygame.display.flip()  # update the display

    # Handles a safe shutdown for the app
    def exitPhotobooth(self):
        if self.running:
            self.running = False
            self.displayStatus("Please hang on while Photobooth exits.")
            self.indicatorsOff()
            GPIO.output(Photobooth.gpioPins['flash']['indicator'], True)
            sleep(2)
            GPIO.cleanup()
            pygame.quit()
            sys.exit()

    # Shutdown
    def shutdownPi(self):
        if self.running:
            self.running = False
            self.displayStatus("Shutting down photobooth.")
            self.indicatorsOff()
            GPIO.output(Photobooth.gpioPins['flash']['indicator'], True)
            sleep(2)
            GPIO.cleanup()
        os.system("sudo halt")

    def getNumberOfPhotos(self):
        nP = 0
        if self.currentAction:
            try:
                nP = len(Photobooth.templates[self.currentAction]['images'])
            except:
                nP = 0
        return nP

    # Shutsdown everything if 'esc' key is pressed
    def checkForEscPress(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exitPhotobooth()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.exitPhotobooth()

    # Returns true if running, false otherwise
    def isRunning(self):
        return self.running

    # Turn on all Indicator LEDs
    def indicatorsOn(self):
        for action, pins in Photobooth.gpioPins.iteritems():
            if action not in ['flash', 'shutdown']:
                GPIO.output(pins['indicator'], True)
        # for gpio_pin in Photobooth.ready_led_gpio_pins:
        #     GPIO.output(gpio_pin, True)       # Turn on indicator LEDs

    # Turn off all Inficator LEDs except for idx
    def indicatorsOffExceptCurrent(self):
        for action, pins in Photobooth.gpioPins.iteritems():
            if action not in ['flash', 'shutdown']:
                if action is not self.currentAction:
                    GPIO.output(pins['indicator'], False)
                else:
                    GPIO.output(pins['indicator'], True)
        # for pdx in range(len(Photobooth.ready_led_gpio_pins)):
        #     if not pdx == idx:
        #         GPIO.output(Photobooth.ready_led_gpio_pins[pdx], False)

    # Turn off all Indicator LEDs
    def indicatorsOff(self):
        for action, pins in Photobooth.gpioPins.iteritems():
            if action not in ['flash', 'shutdown']:
                GPIO.output(pins['indicator'], False)

    # turn on Flash
    def flashOn(self):
        for action, pins in Photobooth.gpioPins.iteritems():
            if action is 'flash':
                GPIO.output(pins['indicator'], False)

    # turn off Flash
    def flashOff(self):
        for action, pins in Photobooth.gpioPins.iteritems():
            if action is 'flash':
                GPIO.output(pins['indicator'], True)

    # capture image from camera
    def takePictures(self, imgPath, numPics=4):
        counter = 0
        self.cam.awb_mode = 'auto'
        self.cam.iso = 125   # 300
        self.cam.start_preview()

        # Blank out screen
        self.screen.fill((0, 0, 0))
        pygame.display.update()

        for each in range(numPics):
            counter = counter + 1
            text = 'Photo ' + str(counter) + ' of ' + str(numPics)
            self.cam.annotate_text = text

            # # cam.start_preview()
            countdown = 4
            if counter == 1:    # length of preview time for first picture
                countdown = countdown + 10

            msg = self.cam.annotate_text
            for idx in range(countdown):
                timeClick = countdown + 1 - idx
                self.cam.annotate_text = msg + "\nSmile in " + str(timeClick)
                sleep(1)
            self.ensureDir(imgPath)
            self.cam.annotate_text = ''
            self.cam.resolution = Photobooth.capture_resolution
            self.cam.capture('./' + imgPath + '/' + str(counter) + '.jpg')
            self.cam.resolution = (1280, 800)

        self.cam.stop_preview()

    # Merge all photos onto one ready for printing
    def combineImages(self, imgPath):
        # self.displayStatus('Please wait. Processing Images')
        template = Photobooth.templates[self.currentAction]
        photocard = Image.open('./img/' + template['card'])

        tempImage = []
        idx = 0
        # Do the image merging
        for subimage in template['images']:
            tempImage.append(Image.open(imgPath + '/' + str(idx + 1) + '.jpg'))
            tempImage[idx] = tempImage[idx].resize(subimage['size'],
                                                   PIL.Image.ANTIALIAS)
            tempImage[idx] = tempImage[idx].rotate(subimage['rotation'])
            photocard.paste(tempImage[idx], subimage['origin'])
            idx = idx + 1

        photocard.save(imgPath + '/photocard.jpg', 'JPEG', quality=100)

    # Create dir if it is not already there
    def ensureDir(self, f):
        if not os.path.exists(f):
            os.makedirs(f)

    # Checks for button Press
    def checkForButtonPress(self):
        for action, pins in Photobooth.gpioPins.iteritems():
            if action is not 'flash':
                if not GPIO.input(pins['button']):
                    self.currentAction = action
                    if action is 'shutdown':
                        self.shutdownPi()
                    break

        # for idx in range(len(Photobooth.button_gpio_pins)):
        #     if not GPIO.input(Photobooth.button_gpio_pins[idx]):
        #         print(str(idx) + " --")
        #         return idx
        # return -1

    # Print photocard
    def printCard(self, imgPath):
        # self.displayStatus('Printing')
        conn = cups.Connection()
        printers = conn.getPrinters()
        printer_name = printers.keys()[0]
        self.displayStatus(printer_name)
        sleep(5)
        conn.printFile(printer_name,
                       imgPath + '/photocard.jpg',
                       imgPath, {'StpiShrinkOutput': 'Expand',
                                'StpBorderless': 'True'})

        time.sleep(2)



    # Start Shoot
    def startShoot(self):

        # Check if a shoot has been requested
        if self.currentAction:
            if self.currentAction is not 'flash' or 'shutdown':
                self.indicatorsOffExceptCurrent()
                self.flashOn()
                now = time.strftime("%Y-%m-%d-%H:%M:%S")  # set timestamp
                sleep(0.2)
                self.takePictures(now, self.getNumberOfPhotos())
                self.displayStatus("Your photo is printing to printer " + str(self.currentPrinter) + ".")
                sleep(0.1)
                self.flashOff()
                self.combineImages(now)
                self.printCard(now)
                self.currentAction = None
                self.nextPrinter()


def main():
    photobooth = Photobooth()
    try:
        while photobooth.isRunning():
            photobooth.indicatorsOn()
            photobooth.checkForEscPress()
            photobooth.displayStatus("hello")
            photobooth.checkForButtonPress()
            photobooth.startShoot()
            sleep(0.2)
    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])
        print(sys.exc_info()[2])
    finally:
        photobooth.exitPhotobooth()

if __name__ == '__main__':
    main()
