import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from adafruit_bme280 import advanced as adafruit_bme280
import adafruit_tsl2561
import adafruit_veml7700
import adafruit_ccs811

from pms5003 import PMS5003

# i2c codes for light sensors (alternatives)
TSL2561_CODE = 0x39
VEML7700_CODE = 0x10

def ok(sensor):
    print('----- ' + sensor + ' OK -----')
    return

def err(sensor):
    print('***** ' + sensor + ' ERROR *****')
    return


try:
    sensor = 'TSL2561 or VEML7700'
    light = None
    i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
    devices = i2c.scan()
    if TSL2561_CODE in devices:
        light = adafruit_tsl2561.TSL2561(i2c)
    elif VEML7700_CODE in devices:
        light = adafruit_veml7700.VEML7700(i2c)
    else:
        raise Exception('no I2C light sensor detected')
    
    print('Lux: {}'.format(light.lux))
    ok(sensor)
except Exception as ex:
    err(sensor)
    print(ex)
    pass

try:
    sensor = 'ccs811'
    ccs811 = adafruit_ccs811.CCS811(i2c)
    while not ccs811.data_ready:
        pass
    print("CO2: %1.0f PPM" % ccs811.eco2)
    print("TVOC: %1.0f PPM" % ccs811.tvoc)
    ok(sensor)
except Exception as ex:
    err(sensor)
    print(ex)
    pass
    

try:
    ##i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = 'bme280'
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

    print("\nTemperature: %0.1f C" % bme280.temperature)
    print("Humidity: %0.1f %%" % bme280.humidity)
    print("Pressure: %0.1f hPa" % bme280.pressure)
    ok(sensor)
except Exception as ex:
    err(sensor)
    print(ex)
    pass





try:
    sensor = 'MCP3008'
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    cs = digitalio.DigitalInOut(board.D5)
    mcp = MCP.MCP3008(spi, cs)

    sound = AnalogIn(mcp, MCP.P0)
    print('raw sound: ', sound.value)
    mq135 = AnalogIn(mcp, MCP.P1)
    print('raw mq135: ', mq135.value)
    ok(sensor)
except Exception as ex:
    err(sensor)
    print(ex)
    pass



try:
    sensor = 'pms5003'
    pms5003 = PMS5003(
        device='/dev/ttyAMA0',
        baudrate=9600,
        pin_enable=22,
        pin_reset=27
    )
    data = pms5003.read()
    print(data)
    ok(sensor)
except Exception as ex:
    err(sensor)
    print(ex)
    pass

