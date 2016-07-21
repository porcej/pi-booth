#! /usr/bin/python

import picamera
import os
import RPi.GPIO as GPIO
import atexit
import time
from time import sleep
import PIL
from PIL import Image
import select
import sys
if 'threading' in sys.modules:
    del sys.modules['threading']
import threading


# Raspbery Pi Camera Moduls Max Resolution
# rev 1.3:  2592, 1944
# rev 2.1:  3280, 2464
#
# Standard Photosizes
# ========================================
# Print size (in.)    Image size (pixels)
# 4 x 6   1200 x 1800
# 5 x 7   1500 x 2100
# 8 x 8   2400 x 2400
# 8 x 10  2400 x 3000

########################
#   Variables Config   #
########################
CAPTURE_RESOLUTION = (2592, 1944)




########################
#      Initialize      #
########################
# Init Camera
# camera = picamera.PiCamera()
# camera.led = False
# camera.brightness = 45

# init GPIO for Flash
GPIO.setwarnings(False)     # disabled errors when ready LED is already ON
GPIO.setmode(GPIO.BCM)

# Handle Flash Pin
GPIO.setup(flash_gpio_pin, GPIO.OUT)    # flash relay
GPIO.output(flash_gpio_pin, False)       # Turn off flash relay

# Handle shutdown pin
GPIO.setup(shutdown_gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Prep the button input pins
for gpio_pin in button_gpio_pins:
    GPIO.setup(button_gpio_pins, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Prepare the output LEDs
for gpio_pin in ready_led_gpio_pins:
    GPIO.setup(gpio_pin, GPIO.OUT)    # ready LED
    GPIO.output(gpio_pin, False)

########################
#       Functions      #
########################


def displayStatus(message):
    print(str(message))


# Turn on all Indicator LEDs
def all_ready_on():
    for gpio_pin in ready_led_gpio_pins:
        GPIO.output(gpio_pin, True)       # Turn on indicator LEDs


# Turn off all Inficator LEDs except for idx
def ready_off_except(idx):
    for pdx in range(len(ready_led_gpio_pins)):
        if not pdx == idx:
            GPIO.output(ready_led_gpio_pins[pdx], False)


# Turn off all Indicator LEDs
def all_ready_off():
    for gpio_pin in ready_led_gpio_pins:
        GPIO.output(gpio_pin, False)       # Turn on indicator LEDs


# Create dir if it is not already there
def ensure_dir(f):
    if not os.path.exists(f):
        os.makedirs(f)


# capture image from camera
def take_pictures(imgPath, numPics=4):
    with picamera.PiCamera() as cam:
        counter = 0
        cam.awb_mode = 'auto'
        cam.iso = 300
        # cam.image_effect = 'oilpaint'
        cam.start_preview()
        for each in range(numPics):
            counter = counter + 1
            cam.annotate_text = 'Photo ' + str(counter) + ' of ' + str(numPics)
            cam.annotate_text = cam.annotate_text + '\n '
            # cam.start_preview()
            if counter == 1:    # length of preview time for first picture
                for trash in range(3):
                    time.sleep(1)
                    cam.annotate_text = cam.annotate_text + '|' * trash

                time.sleep(1)
            if counter > 1:     # length of preview time for pictures 2-4
                time.sleep(3)
            ensure_dir(imgPath)
            cam.annotate_text = ''
            cam.resolution = CAPTURE_RESOLUTION
            cam.capture('./' + imgPath + '/' + str(counter) + '.jpg')

        cam.stop_preview()


# Merge all photos onto one ready for printing
def combineImages(imgPath):
    displayStatus('Please wait. Processing Images')
    template = 'd'
    templates = {
        'a':{
            'size': (1800, 1200),
            'card': 'template_a.jpg',
            'images':[
                {'size': (807, 538), 'origin': (75, 443), 'rotation': 0},
                {'size': (807, 538), 'origin': (917, 443), 'rotation': 0}
            ]
        },
        'b': {
            'size': (1800, 1200),
            'card': 'template_b.jpg',
            'images':[
                {'size': (1089, 726), 'origin': (676, 57), 'rotation': 0},
                {'size': (540, 360), 'origin': (676, 796), 'rotation': 0},
                {'size': (540, 360), 'origin': (1225, 796), 'rotation': 0},
            ]
        },
        'c': {
            'size': (1800, 1200),
            'card': 'template_c.jpg',
            'images':[
                {'size': (1089, 726), 'origin': (35, 57), 'rotation': 0},
                {'size': (540, 360), 'origin': (35, 796), 'rotation': 0},
                {'size': (540, 360), 'origin': (584, 796), 'rotation': 0},
            ]
        },
        'd': {
            'size': (1800, 1200),
            'card': 'template_d.jpg',
            'images':[
                {'size': (579, 386), 'origin': (15, 609), 'rotation': 90},
                {'size': (579, 386), 'origin': (416, 609), 'rotation': 90},
                {'size': (579, 386), 'origin': (817, 609), 'rotation': 90},
                {'size': (579, 386), 'origin': (15, 15), 'rotation': 90},
                {'size': (579, 386), 'origin': (416, 15), 'rotation': 90},
                {'size': (579, 386), 'origin': (817, 15), 'rotation': 90},
            ]
        },
        'a_':{
            'size': (1280, 800),
            'card': 'template_a.jpg',
            'images':[
                {'size': (776, 485), 'origin': (18, 12), 'rotation': 90},
                {'size': (776, 485), 'origin': (521, 12), 'rotation': 90}
            ]
        },
        'b_': {
            'size': (1280, 800),
            'card': 'template_b.jpg',
            'images':[
                {'size': (472, 295), 'origin': (12, 70), 'rotation': 0},
                {'size': (472, 295), 'origin': (12, 435), 'rotation': 0},
                {'size': (472, 295), 'origin': (496, 70), 'rotation': 0},
                {'size': (472, 295), 'origin': (496, 435), 'rotation': 0}
            ]
        },
        'c_': {
            'size': (1280, 800),
            'card': 'template_a.jpg',
            'images':[
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

    photocard = Image.open('./img/' + templates[template]['card'])

    tempImage = []
    idx = 0
    # Do the image merging
    for subimage in templates[template]['images']:
        tempImage.append(Image.open(imgPath + '/' + str(idx+1) + '.jpg'))
        tempImage[idx] = tempImage[idx].resize(
                                              subimage['size'],
                                              PIL.Image.ANTIALIAS)
        tempImage[idx] = tempImage[idx].rotate(subimage['rotation'])
        photocard.paste(tempImage[idx], subimage['origin'])
        idx = idx + 1

    photocard.save(imgPath + '/photocard.jpg', 'JPEG', quality=100)




    # Do the merging
    # blankImage = Image.open('./img/template_b.jpg')

    # image1 = Image.open(imgPath + '/1.jpg')
    # image1 = image1.resize((472, 295), PIL.Image.ANTIALIAS)
    # # image1 = image1.rotate(90)
    # blankImage.paste(image1, (12, 70))

    # image2 = Image.open(imgPath + '/2.jpg')
    # image2 = image2.resize((472, 295), PIL.Image.ANTIALIAS)
    # # image2 = image2.rotate(90)
    # blankImage.paste(image2, (12, 435))

    # image3 = Image.open(imgPath + '/3.jpg')
    # image3 = image3.resize((472, 295), PIL.Image.ANTIALIAS)
    # # image3 = image3.rotate(90)
    # blankImage.paste(image3, (496, 70))

    # image4 = Image.open(imgPath + '/4.jpg')
    # image4 = image4.resize((472, 295), PIL.Image.ANTIALIAS)
    # # image4 = image4.rotate(90)
    # blankImage.paste(image4, (496, 435))

    # image4 = Image.open(imgPath + '/4.jpg')
    # image4 = image4.resize((177, 140), PIL.Image.ANTIALIAS)
    # blankImage.paste(image4, (177, 140))

    # blankImage.save(imgPath + '/combined.jpg', 'JPEG', quality=100)


# Detect a hard return or enter keypress (True) false otherwise
def heardEnter():
    i, o, e = select.select([sys.stdin], [], [], 0.0001)
    for s in i:
        if s == sys.stdin:
            # input = sys.stdin.readline()
            return True
    return False


# Clean up before exiting
def cleanup(channel=0):
    # Turn off flash and all ready indicators
    GPIO.output(flash_gpio_pin, False)  # Turn off flash
    all_ready_off()
    # GPIO.cleanup()


# Handle abrupt exit
def uncleanup():
    print("AHHHHH! Abruptly Going down.")
    cleanup()
atexit.register(cleanup)


# Exit
def exit_app(channel=0):
    print("Exiting photobooth.")
    time.sleep(3)
    sys.exit(0)


# Shutdown
def shutdown_app(channel):
    print("Going down for the long sleep.")
    cleanup(channel)
    os.system("sudo halt")

if __name__ == '__main__':

    # Add event listeners for shutdown and exit
    GPIO.add_event_detect(shutdown_gpio_pin,
                          GPIO.FALLING,
                          callback=shutdown_app,
                          bouncetime=2000)

    # GPIO.add_event_detect(button3_pin, GPIO.FALLING,
    # callback=exit_photobooth, bouncetime=300)


    #  camera.start_preview()
    print("Pi Photoboorh.  Please press <enter> to exit.")
    while True:
        all_ready_on()
        if heardEnter():
             exit_app()
        for idx in range(len(button_gpio_pins)):
            if not GPIO.input(button_gpio_pins[idx]):
                ready_off_except(idx)
                GPIO.output(flash_gpio_pin, True)
                now = time.strftime("%Y-%m-%d-%H:%M:%S")  # set timestamp
                sleep(0.2)
                take_pictures(now, 6)
                combineImages(now)
                #  camera.capture(now + '.jpg')
                sleep(0.1)
                GPIO.output(flash_gpio_pin, False)
