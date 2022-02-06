from machine import Pin, UART
import time
import pylorawan 
import creds_config

# Tested with a Raspberry PI Pico and a RAK4200(H) Evaluation Board (868MHz)

# Talk to the modem using the UART0 TRansmitter(Tx) / Receiver(Rx)
uart0 = UART(1, 115200)  # use RPI PICO

# The device uses AT commands like a traditional modem, so i'll rewfer to it as a modem.
modem = pylorawan.LorawanModem(uart0, debug=True)

# Configure it to use OTAA (rather ABP comms) using keys from the device itself and The Things Network Console
# dev_eui is printed in the top of the chip casing
modem.configure_otaa(region="EU868", dev_eui=creds_config.dev_eui, app_eui=creds_config.app_eui, app_key=creds_config.app_key)

# Try and join the network (often takes a few tries, it will automatically retry a few times)
if modem.join():

    # It worked...
    # Send some made up hex data to the TTN server on channel 1, TTN will recognise this string as Hex bytes   
    modem.send_data("AABBCCDD", channel=1)

else:
    # Could not join the network...
    print("Failed to Join, are your keys correct? Is there a gateway in range?")
