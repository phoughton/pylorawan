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

    def __init__(self, uart, debug=False, uart_debug=None):
        self.uart = uart
        self.debug = debug
        self.uart_debug = uart_debug


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

    # Set the device up for Over The Air Activation (OTAA) with these keys etc.
    def configure_otaa(self, region=None, dev_eui=None, app_eui=None, app_key=None, lora_class=0):
        self.log_debug("Configure Modem:")
        if None in [region, dev_eui, app_eui, app_key]:
            raise ValueError(f"Missing essential config, Region: {region}, Dev EUI: {dev_eui}, App EUI: {app_eui}, App Key: {app_key}")

        self.run_command(command=f"at+set_config=lora:join_mode:0", wanted_response="OK", tries=1, rx_delay=0),
        self.run_command(command=f"at+set_config=lora:class:{lora_class}", wanted_response="OK", tries=1, rx_delay=0),
        self.run_command(command=f"at+set_config=lora:region:{region}", wanted_response= "OK", tries=1, rx_delay=0),
        self.run_command(command=f"at+set_config=lora:dev_eui:{dev_eui}", wanted_response="OK", tries=1, rx_delay=0),
        self.run_command(command=f"at+set_config=lora:app_eui:{app_eui}", wanted_response="OK", tries=1, rx_delay=0),
        self.run_command(command=f"at+set_config=lora:app_key:{app_key}", wanted_response="OK",tries=1, rx_delay=0)

    # Set the data rate, this relates to Spreading Factor (SF)
    def set_data_rate(self, data_rate=5):
        return self.run_command(command=f"at+set_config=lora:dr:{data_rate}", wanted_response='OK', tries=1, rx_delay=0)

    # Join the Lorawan network 
    def join(self):
        self.log_debug("Join Network:")
        return self.run_command(command='at+join', wanted_response='OK Join Success', tries=8)

    # Send the data, I've been sending pairs of hex values, passed in as strings, a pair of Hex chars is 1 byte (8 bits)
    def send_data(self, data="", channel=1, tries=1):
        return self.run_command(command=f"at+send=lora:{channel}:{data}", wanted_response="OK", tries=tries)

    # Return status information from the device
    def status_info(self):
        return self.run_command(command='at+get_config=lora:status', wanted_response='DownLinkCounter', tries=1, rx_delay=0)
