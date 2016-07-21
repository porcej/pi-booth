# pi-booth
Raspberry Pi Photobooth
#Pi Photobooth
##Requirements
 * Raspberry Pi > 2 (3 or newer strongly recommended)
 * Pi Camera Module (Version 2.1 or newer rcommended)
 * 4 momentary pushbuttons, with indicator leds
 * 1 momentary pushbutton for shutdown switch
 * Relay board
 * 2 or more flash modules [https://porcej.com/pi/flash]

##Hardware Configuration
 * TODO

##Pi Configuration and Software Installation
 * Burn Raspbian to a micro-sd card [https://www.raspberrypi.org/downloads/raspbian/]
 * Install said micro-sd card in Raspberry pi
 * Boot the Pi
 * Run rasp-config
 * Expand file system
  * Rename host name (photobooth)
  * Enable camera interface
  * Enable auto-login (cli)
 * Reboot
 * sudo apt-get update && sudo apt-get upgrade
 * sudo apt-get dist-upgrade
 * sudo apt-get update
 * sudo apt-get install python-pip
 * sudo apt-get install python-picamera
 * sudo apt-get install python-dev python-setuptools
 * sudo apt-get install python-imaging
 * sudo apt-get install python-pygame
 * sudo apt-get install cups
 * sudo usermod -a -G lpadmin pi
 * sudo apt-get install python-cups
 * Follow the steps here [http://www.howtogeek.com/169679/how-to-add-a-printer-to-your-raspberry-pi-or-other-linux-computer/]
 * $ lpoptions -p printername -o StpiShrinkOutput=Expand
$* $ lpoptions -p printername -o StpBorderless=True


 ## Add shutdown.py and camera.py to auto-load
 * sudo nano /etc/rc.local
 * sudo python /home/pi/Scripts/shutdown_pi.py &
