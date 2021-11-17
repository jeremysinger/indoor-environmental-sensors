import datetime
import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from adafruit_bme280 import advanced as adafruit_bme280
import adafruit_tsl2561
import adafruit_ccs811

from pms5003 import PMS5003

INTERVAL_BETWEEN_SAMPLES = 5

def err(sensor):
    print('---------' + sensor + ' error')
    sensor_ok[sensor] = False
    return

sensor_ok = {}   # sensor keys map to True if sensor working
sensor_ok['TSL2561'] = False
sensor_ok['BME280'] = False
sensor_ok['CCS811'] = False
sensor_ok['MCP3008'] = False
sensor_ok['PMS5003'] = False

try:
    sensor = 'TSL2561'
    i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
    light = adafruit_tsl2561.TSL2561(i2c)
    sensor_ok[sensor] = True
    lux = light.lux
except Exception as ex:
    err(sensor)
    print(ex)
    pass

try:
    sensor = 'CCS811'
    ccs811 = adafruit_ccs811.CCS811(i2c)
    while not ccs811.data_ready:
        pass
    # remember to calibrate on temp
    co2 = ccs811.eco2
    voc = ccs811.tvoc
    sensor_ok[sensor] = True
except Exception as ex:
    err(sensor)
    print(ex)
    pass
    

try:
    sensor = 'BME280'
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

    temp = bme280.temperature
    hum = bme280.humidity
    press = bme280.pressure
    sensor_ok[sensor] = True
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
    vol = sound.value
    mq135 = AnalogIn(mcp, MCP.P1)
    gas = mq135.value
    sensor_ok[sensor] = True
except Exception as ex:
    err(sensor)
    print(ex)
    pass



try:
    sensor = 'PMS5003'
    pms5003 = PMS5003(
        device='/dev/ttyAMA0',
        baudrate=9600,
        pin_enable=22,
        pin_reset=27
    )
    data = pms5003.read()
    pm1 = data.pm_ug_per_m3(1)
    pm25 = data.pm_ug_per_m3(2.5)
    pm10 = data.pm_ug_per_m3(10)
    sensor_ok[sensor] = True
except Exception as ex:
    err(sensor)
    print(ex)
    pass



while True:
    lux = 0
    temp = 0
    hum = 0
    press = 0
    co2 = 0
    voc = 0
    vol = 0
    gas = 0
    pm1 = 0
    pm25 = 0
    pm10 = 0
    
    if sensor_ok['TSL2561']:
        try:
            lux = light.lux
        except Exception as ex:
            sensor_ok['TSL2561'] = False
            print(ex)
            pass
            
            
    if sensor_ok['BME280']:
        try:
            temp = bme280.temperature
            hum = bme280.humidity
            press = bme280.pressure
        except Exception as ex:
            sensor_ok['BME280'] = False
            print(ex)
            pass

    if sensor_ok['CCS811']:
        try:
            ccs811.set_environmental_data(int(hum), float(temp))
            while not ccs811.data_ready:
                pass
            co2 = ccs811.eco2
            voc = ccs811.tvoc
        except Exception as ex:
            sensor_ok['CCS811'] = False
            print(ex)
            pass

    if sensor_ok['MCP3008']:
        try:
            vol = sound.value
            gas = mq135.value
        except Exception as ex:
            sensor_ok['MCP3008'] = False
            print(ex)
            pass

        
    if sensor_ok['PMS5003']:
        try:
            data = pms5003.read()
            pm1 = data.pm_ug_per_m3(1)
            pm25 = data.pm_ug_per_m3(2.5)
            pm10 = data.pm_ug_per_m3(10)
        except Exception as ex:
            sensor_ok['PMS5003'] = False
            print(ex)
            pass


    # now write out single line of comma-separated data
    # ts,lux,temp,hum,press,co2,voc,vol,gas,pm1,pm25,pm10
    ts = str(datetime.datetime.now())
    print(ts,lux,temp,hum,press,co2,voc,vol,gas,pm1,pm25,pm10, sep=',', end='\n')
    
    time.sleep(INTERVAL_BETWEEN_SAMPLES) # in seconds
