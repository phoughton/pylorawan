import time

# This file provides a API to interact with RAK Wireless Lorawan devices.
# Tested on a RAK4200(H) Evaluation Board (868MHz)

REPEAT_SLEEP = 6

class Utils():

    def __init__(self, debug=False, uart_debug=None):
        self.debug=debug
        self.uart_debug = uart_debug

    def log_debug(self, msg=""):
        if self.debug:
            output = f"{time.time()} : {msg}"
            print(output)
            if self.uart_debug is not None:
                self.uart_debug.write(output + "\r\n")


class LorawanModem(Utils):
    
    RAK3172_region_lookup = {
        "EU433" : "0",
        "CN470" : "1",
        "IN865" : "3",
        "EU868" : "4",
        "US915" : "5",
        "AU915" : "6",
        "KR920" : "7",
        "AS923-1" : "8",
        "AS923-1" : "8-1",
        "AS923-2" : "8-2",
        "AS923-3" : "8-3",
        "S923-4" : "8-4",
        }
    
    RAK4200_region_list = [
        "EU433", "CN470", "IN865", "EU868", "US915", "AU915", "KR920", "AS923"
        ]
    
    RAK4200_lora_class_lookup = {
        "A": "0",
        "B": "1",
        "C": "2"
        }
    
    RAK3172_lora_class_list = [
        "A", "B", "C"
        ]
    
    # Provide:
    # a UART to communicate to the RAK device
    # The device type e.g. "RAK4200", "RAK3172"
    def __init__(self, uart, device_type, debug=False, uart_debug=None):
        self.uart = uart
        if device_type not in [None, "RAK4200", "RAK3172"]:
            raise ValueError("Device type has not been set correctly. Supported types: RAK4200 & RAK3172")
        
        self.device = device_type
        self.debug = debug
        self.uart_debug = uart_debug

    # Send the AT command to the RAK device and wait for the ewxpected delay time
    def send(self, command, rx_delay):
        self.log_debug(command)
        self.uart.write(command + "\r\n")
        time.sleep(rx_delay)
        
    # Used to keep reading for a while, and check for a desired response
    def wait_for_read(self, expected_response, time_to_listen=5):
        found=False
        read_text=""
        start_time = time.time()

        while not found and time.time() <= (start_time + time_to_listen):
            read_text += self.read()

            found = expected_response in read_text

        self.log_debug(f"Text found: {read_text}, Found?: {found}")
        return found, read_text

    # Read data from the RAK device over UART, try and decode to UTF-8 text
    def read(self):
        rx_data = bytes()
        while self.uart.any()>0:
            new_data = self.uart.read()
            if new_data is not None:
                rx_data += new_data
        try:
            rx_data.decode('utf-8')
        except UnicodeError:
            self.log_debug(f"UnicodeError with rx_data:\n{rx_data}")
            return f"UnicodeError in decode('utf-8'), The response was: {rx_data}"

        return rx_data.decode('utf-8')
        

    # Run a command and wait for the desired response.
    # You can configure retries etc.
    # rx_delay is the Rx1 delay
    def run_command(self, command=None, wanted_response=None, tries=1, debug=False, rx_delay=4.5):
        
        self.log_debug()
        self.log_debug(f"Command: {command}, wanted Response: {wanted_response}, How many tries to give it:{tries}")
        found = False
        resp_text=""

        while tries > 0 and not found:
            self.send(command, rx_delay)
            found, resp_text = self.wait_for_read(wanted_response)
            tries -= 1

            self.log_debug(f"Command: {command} Response:{resp_text}, Found: {found}")
    
            if not found:
                self.log_debug("Retrying send, after sleep...")
                time.sleep(REPEAT_SLEEP)

        return found, resp_text

    def region_translate(self, region):
        if self.device=="RAK4200":
            if isinstance(region, int):
                raise ValueError("Region was not a String, E.g. EU868")
            return region
        elif self.device=="RAK3172":
            return self.RAK3172_region_lookup[f"{region}"]

    def class_translate(self, lora_class):
        if isinstance(lora_class, int):
            raise ValueError("Lora Class should be string 'A', 'B' or 'C'")
            
        if self.device=="RAK4200":
            if lora_class == "1":
                raise ValueError("Lora Class 1 / B is not supported on this device")
            return self.RAK4200_lora_class_lookup[lora_class]
        
        elif self.device=="RAK3172":
            if lora_class not in self.RAK3172_lora_class_list:
                raise ValueError("Lora Class not found")
            return lora_class

    # Set the device up for Over The Air Activation (OTAA) with these keys etc.
    def configure_otaa(self, region=None, dev_eui=None, app_eui=None, app_key=None, lora_class=None):
        
        region = self.region_translate(region)
        lora_class = self.class_translate(lora_class)
        
        self.log_debug("Configure Modem:")
        if None in [region, dev_eui, app_eui, app_key, lora_class]:
            raise ValueError(f"Missing essential config, Region: {region}, Dev EUI: {dev_eui}, App EUI: {app_eui}, App Key: {app_key}, Lora Class: {lora_class}")

        if self.device == "RAK4200":
            self.run_command(command=f"at+set_config=lora:join_mode:0", wanted_response="OK", tries=1, rx_delay=0)
            self.run_command(command=f"at+set_config=lora:class:{lora_class}", wanted_response="OK", tries=1, rx_delay=0)
            self.run_command(command=f"at+set_config=lora:region:{region}", wanted_response= "OK", tries=1, rx_delay=0)
            self.run_command(command=f"at+set_config=lora:dev_eui:{dev_eui}", wanted_response="OK", tries=1, rx_delay=0)
            self.run_command(command=f"at+set_config=lora:app_eui:{app_eui}", wanted_response="OK", tries=1, rx_delay=0)
            self.run_command(command=f"at+set_config=lora:app_key:{app_key}", wanted_response="OK",tries=1, rx_delay=0)
        elif self.device == "RAK3172":
            self.run_command(command=f"AT+NWM=1", wanted_response="OK", tries=1, rx_delay=0)
            self.run_command(command=f"AT+NJM=1", wanted_response="OK", tries=1, rx_delay=0)
            self.run_command(command=f"AT+CLASS={lora_class}", wanted_response="OK", tries=1, rx_delay=0)
            self.run_command(command=f"AT+BAND={region}", wanted_response="OK", tries=1, rx_delay=0)
        else:
            raise ValueError("Device type not supported")
        

    # Set the data rate, this relates to Spreading Factor (SF)
    def data_rate(self, data_rate=5):
        if self.device=="RAK4200":
            return self.run_command(command=f"at+set_config=lora:dr:{data_rate}", wanted_response='OK', tries=1, rx_delay=0)
        elif self.device=="RAK3172":
            return self.run_command(command=f"AT+DR={data_rate}", wanted_response='OK', tries=1, rx_delay=0)

    # Join the Lorawan network 
    def join(self):
        self.log_debug("Join Network:")
        if self.device=="RAK4200":
            found, resp = self.run_command(command='at+join', wanted_response='OK Join Success', tries=8)
        elif self.device=="RAK3172":
            found, resp =  self.run_command(command='AT+JOIN=1:0:10:0', wanted_response='+EVT:JOINED', tries=8)
        return found

    # Send the data, I've been sending pairs of hex values, passed in as strings, a pair of Hex chars is 1 byte (8 bits)
    def send_data(self, data="", port=1, tries=1):
        if self.device=="RAK4200":
            return self.run_command(command=f"at+send=lora:{port}:{data}", wanted_response="OK", tries=tries)
        elif self.device=="RAK3172":
            return self.run_command(command=f"AT+SEND={port}:{data}", wanted_response="OK", tries=tries)

    # Return status information from the device (RAK4200 only)
    def status_info(self):
        if self.device=="RAK4200":
            return self.run_command(command='at+get_config=lora:status', wanted_response='DownLinkCounter', tries=1, rx_delay=0)
        elif self.device=="RAK3172":
            self.log_debug("Status command not supported on RAK3172")
    
    # Get supported regions for current device or which device_type is supplied
    def get_supported_regions(self, device_type=None):
        if device_type is None:
            device_type = self.device
        
        if device_type == "RAK4200":
            return self.RAK4200_region_list
        
        if device_type == "RAK3172":
            return list(self.RAK3172_region_lookup.keys())
    
        
            