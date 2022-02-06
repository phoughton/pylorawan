from machine import Pin, ADC, UART
import math
import time
import pylorawan 
import creds_config    

sensor_temp = ADC(4)
conversion_factor = 3.3 / (65535)

decoded_data = ""
led = Pin(25, Pin.OUT)
uart = UART(1, 115200)  # use UART 1 for the RAK device
uart_debug = UART(0, 115200)  # use UART 0 for debug (Optional)

# Flash LED to indicate its running
print("Flash LED")
led.value(1)
time.sleep(1)
led.value(0)

thermistor = ADC(28)
# Convert float with 2 decimal ppoint required presicion into hex int
def hex_int_from_2dp_celcius(temp_in_c):
    cel_enc = int(round((temp_in_c+40)*100))
    return f"{cel_enc:0>4X}"
    
# Calc temp using external thermistor 
def get_temp_celcius():
    temperature_value = thermistor.read_u16()
    Vr = 3.3 * float(temperature_value) / 65535
    Rt = 10000 * Vr / (3.3 - Vr)
    temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15+25)))
    return temp - 273.15

# Set up the modem and output the status
# Credentials are stored in seperate file: credsconfig
modem = pylorawan.LorawanModem(uart, debug=True, uart_debug=uart_debug)
logger = pylorawan.Utils(debug=True, uart_debug=uart_debug)
modem.configure_otaa(region="EU868", dev_eui=creds_config.dev_eui, app_eui=creds_config.app_eui, app_key=creds_config.app_key)
modem.set_data_rate(3)
logger.log_debug(modem.status_info())
logger.log_debug()

logger.log_debug("Next try to join")
if modem.join():

    location = "01" # Arbitrary location identifier, sent to server, but not used anywhere yet

    while True:
        encoded_temp = hex_int_from_2dp_celcius(get_temp_celcius())
        logger.log_debug(f"Sending Temperature:{encoded_temp}")
        modem.send_data(f"{location}{encoded_temp}", channel=2)
        logger.log_debug(time.time())
        logger.log_debug("Sleeping...")
        for count in range(3):
            time.sleep(100)
            logger.log_debug(f"Slept 100, {count+1}/3")
        logger.log_debug()

