import datetime
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

INTERVAL_BETWEEN_SAMPLES = 5   # 5 second measurement interval
ERR_TIMEOUT = 10               # 10 second timeout after error
MAX_ERR = 10                   # after 10 errors on a sensor, give up

# i2c codes for light sensors (alternatives)
TSL2561_CODE = 0x39
VEML7700_CODE = 0x10

def err(sensor):
    print('---------' + sensor + ' error')
    sensor_ok[sensor] = False
    return

def initPMS():
    global pms5003
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
    return

def initCCS():
    global ccs811
    try:
        sensor = 'CCS811'
        ccs811 = adafruit_ccs811.CCS811(i2c)
        while not ccs811.data_ready:
            pass
        # when using, remember to calibrate on temp
        co2 = ccs811.eco2
        voc = ccs811.tvoc
        sensor_ok[sensor] = True
    except Exception as ex:
        err(sensor)
        print(ex)
        pass
    return


sensor_ok = {}   # sensor keys map to True if sensor working
sensor_ok['TSL2561 or VEML7700'] = False
sensor_ok['BME280'] = False
sensor_ok['CCS811'] = False
sensor_ok['MCP3008'] = False
sensor_ok['PMS5003'] = False

sensor_errors = {}
sensor_errors['TSL2561 or VEML7700'] = 0
sensor_errors['BME280'] = 0
sensor_errors['CCS811'] = 0
sensor_errors['MCP3008'] = 0
sensor_errors['PMS5003'] = 0


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

    sensor_ok[sensor] = True
    lux = light.lux
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

initCCS()
initPMS()


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
    
    if sensor_ok['TSL2561 or VEML7700']:
        try:
            lux = light.lux
        except Exception as ex:
            sensor_ok['TSL2561 or VEML7700'] = False
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
            sensor_errors['CCS811'] += 1
            print(ex)
            if sensor_errors['CCS811'] < MAX_ERR:
                # try to reset sensor
                time.sleep(ERR_TIMEOUT)
                ccs811.reset()
                initCCS()
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
            sensor_errors['PMS5003'] += 1
            print(ex)
            if sensor_errors['PMS5003'] < MAX_ERR:
                # try to reset sensor
                time.sleep(ERR_TIMEOUT)
                pms5003.reset()
                initPMS()
            pass


    # now write out single line of comma-separated data
    # ts,lux,temp,hum,press,co2,voc,vol,gas,pm1,pm25,pm10
    ts = str(datetime.datetime.now())
    print(ts,lux,temp,hum,press,co2,voc,vol,gas,pm1,pm25,pm10, sep=',', end='\n')
    
    time.sleep(INTERVAL_BETWEEN_SAMPLES) # in seconds
