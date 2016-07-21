#! /usr/bin/python

# @author: porcej@gmail.com
# @date: 7/16/2016
# @description: A simple cups testing routin

import cups

conn = cups.Connection()
printers = conn.getPrinters()
printer_name = printers.keys()[0]
printers = conn.getPrinters()

for printer in printers:
    print printer, printers[printer]["device-uri"]
print(printer_name + " " + str(len(printers.keys())))
