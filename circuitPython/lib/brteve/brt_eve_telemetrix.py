"""The Raspberry Pi Pico is a low-cost, high-performance microcontroller
   board with flexible digital interfaces"""
import os
import sys
import time
import struct
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "telemetrix_rpi_pico")))

from .telemetrix_rpi_pico.telemetrix_rpi_pico import TelemetrixRpiPico

# Convenience values for the pins.
# Note that the CS value is within a list
SPI_PORT = 0
MISO = 4
MOSI = 3
CLK = 2
CS = [5]
CS_PIN = 5

HIGH = 1
LOW  = 0

PIN_CS_EVE_ILI9488 = 9 #CSX pin of ILI9488
PIN_DCX_EVE_ILI9488 = 8 #D/CX pin of ILI9488

DUMMY_BYTE_LENGTH = 1  #2 for QSPI(Unsupported yet)
FREQ = 115200

class _eve_report:
    data = None

"""
 CALLBACKS
 These functions process the data returned from the Eve
"""
def the_device_callback(report):
    # callback returns a data list:
    #     [I2C_READ_REPORT, i2c_port, count of data bytes, i2c_device_address,
    #     data bytes, time-stamp]
    #[13, 0, 5, 0, 0, 0, 0, 0, 1638425262.7486722]
    number_of_bytes = (int)(report[2]) # exclude time stamp
    report = report[3:number_of_bytes+3]
    ret = bytes(struct.pack("B"*len(report),*report))
    _eve_report.data = ret

class BrtEveTelemetrix():
    """ Host platform RP2040 to control EVE, this class initialize,
    and set up SPI connection on RP2040, also set up the SDcard

    A host platform class must have below APIs:
     - transfer()
     - write_ili9488()
     - write_ili9488_cmd()
     - write_ili9488_data()
     - spi_sdcard -- SPI object of SDcard interface
    """
    def __init__(self):
        # Instantiate the TelemetrixRpiPico class accepting all default parameters.
        self.pico = TelemetrixRpiPico()
        # initialize the device
        # These are "non-standard" pin-numbers, and therefore
        # the qualify_pins parameter is set to FALSE
        self.pico.set_pin_mode_spi(SPI_PORT, MISO, MOSI, CLK, FREQ, CS, qualify_pins=False)
        _eve_report.data = None

    def transfer(self, write_data, bytes_to_read = 0):
        """ Transfer data via SPI"""
        self.pico.spi_cs_control(CS_PIN,  LOW)
        self.pico.spi_write_blocking(write_data, SPI_PORT) 

        if bytes_to_read != 0:
            _eve_report.data = None
            self.pico.spi_read_blocking(bytes_to_read, SPI_PORT, the_device_callback) 
            while _eve_report.data == None:
                time.sleep(0.001)
        self.pico.spi_cs_control(CS_PIN,  HIGH)  
        return _eve_report.data

    def write_ili9488(self,cmd,data):
        """ Write command and data to ili9488 LCD"""
        self.write_ili9488_cmd(cmd)
        self.write_ili9488_data(data)

    def write_ili9488_cmd(self, cmd):
        """ Write command to ili9488 LCD"""
        PIN_CS_EVE_ILI9488 = False
        PIN_DCX_EVE_ILI9488 = False

        self.pico.spi_write_blocking(cmd, SPI_PORT) 
        PIN_CS_EVE_ILI9488 = True

    def write_ili9488_data(self, data):
        """ Write data to ili9488 LCD"""
        PIN_CS_EVE_ILI9488 = False
        PIN_DCX_EVE_ILI9488 = True

        self.pico.spi_write_blocking(data, SPI_PORT) 
        PIN_CS_EVE_ILI9488 = True
