import os
from datetime import datetime

from cleo.io.null_io import NullIO
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json
import serial
import time
import binascii

stx = '02'
etx = '03'

class Request_Json(BaseModel):
#    data_time: datetime.now()
#    request_hex: str
#    request_dec: str
    stx: str = '02'     # Static
    addr: str = ''
    cmd: str = ''
    data: str = ''
    etx: str = '03'     # Static

class Response_Json(BaseModel):
#    data_time: datetime.now()
#    response_hex: str
#    response_dec: str
    lock: str = 'Open'
    infrared: str = '01'

class GetState_Json(BaseModel):
    addr_dec: int = '1'
    addr_hex: str = ''

class Unlock_Json(BaseModel):
    addr_ncu_dec: int = 1
    addr_ncu_hex: str = ''
    addr_lock_dec: int = 1
    addr_lock_hex: str = ''

class Openall_Json(BaseModel):
    addr_ncu_dec: int = 1
    addr_ncu_hex: str = ''

class Getunlocktime_Json(BaseModel):
    addr_ncu_dec: int = 1
    addr_ncu_hex: str = ''

class Setunlocktime_Json(BaseModel):
    addr_ncu_dec: int = 1
    addr_ncu_hex: str = ''
    set_unlocktime_ms_dec: int = 550     # ==550ms   # ==0x27*10=550 ms
    set_unlocktime_ms_hex: str = ''

app = FastAPI()

load_dotenv()
api_key = os.getenv("API_KEY")
kafka_address = os.getenv("KAFKA_ADDRESS")
kafka_port = os.getenv("KAFKA_PORT")
kafka_topic = os.getenv("KAFKA_TOPIC")

'''
producer = KafkaProducer(
    bootstrap_servers= kafka_address+':'+kafka_port, #'localhost:9092',
    api_version=(0,11,5),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
'''

rs485_address = '/dev/cu.usbserial-B000KAZT' #   port= 'COM3',  # PC RS232 (USB-CAT5)   # Serial port name

'''
class Response(BaseModel):
    date_time1 : datetime.now()
    rest_command : str
    date_time2 : datetime.now()
    rest_command : in_485
    date_time3 : datetime.now()
    rest_command : in_485
'''

ncu_settings = {
    "request_hex": True,        # HEX for address, bus
    "response_hex": True,
    "kafka_message_long": True, # received_datetime:command|request_datetime:command|response_datetime:command
    "kafka_ipaddress_port": "192.168.0.107:9092",
    "kafka_topic": "ncu"
}

ncu_commands = {
    "_STX_": "02",
    "_getstate_": "30",
    "_unlock_": "31",
    "_getallstates_": "32",
    "_openall_": "33",
    "_setup_unlock_time_": "37",
    "_setup_unlock_delay_": "39",
    "_get_detection_status_": "3A",
    "_ETX_": "03",
    "getstate_": "02",              # 1
    "_getstate": "300335",          # 1
    "unlock_": "02",                # 2
    "_unlock": "310338",            # 2
    "getallstates": "02F0320327",   # 3
    "openall_": "02",               # 4
    "_openall": "330338",           # 4
    "querytime": "020037033C",      # 5.1
    "queryaddressstate_": "02",     # 8.1
    "_queryaddressstate": "3A033F", # 8.1
    "querybusstate_": "02",         # 8.2
    "_querybusstate": "3A032F"      # 8.2
}

# Commented Temporary
ser = serial.Serial(
    port= rs485_address, # '/dev/cu.usbserial-B000KAZT', # MacBook RS232 'COM1',     # Serial port name
    baudrate=19200,          # Baud rate
    parity=serial.PARITY_NONE, # Parity setting (e.g., serial.PARITY_ODD, serial.PARITY_EVEN)
    stopbits=serial.STOPBITS_ONE, # Stop bits (e.g., serial.STOPBITS_TWO)
    bytesize=serial.EIGHTBITS,  # Data bits (e.g., serial.SEVENBITS)
    timeout=1               # Read timeout in seconds
)

def check_sum(request_json: Request_Json):
    return hex(int(('0x' + request_json.stx), 16)
                + int(('0x' + request_json.addr), 16)
                + int(('0x' + request_json.cmd), 16)
                #                     + int(('0x'+data),16)
                + int(('0x' + request_json.etx), 16))[-2:]  # last 1(one)[2 symbols] byte from summa

def check_sum2(address: str, command: str, data: str):
    return hex(int(('0x' + stx), 16)
                + int(('0x' + address), 16)
                + int(('0x' + command), 16)
                #                     + int(('0x'+data),16)
                + int(('0x' + etx), 16))[-2:]  # last 1(one)[2 symbols] byte from summa

def check_sum3(address: str, command: str, data: str):
    return hex(int(('0x' + stx), 16)
                + int(('0x' + address), 16)
                + int(('0x' + command), 16)
                + int(('0x' + data),16)
                + int(('0x' + etx), 16))[-2:]  # last 1(one)[2 symbols] byte from summa


def serial_txrx(send: str):
    # Send data to the serial device
    ser.write(bytes.fromhex(send))
    # Wait a moment for the device to respond
    time.sleep(0.1)
    # Read data from the serial device
    # Read all bytes waiting in the input buffer
    if ser.in_waiting > 0:
        # We have to exclude symbol ';' from the end of NCU16 response.
        received_data = ser.read(ser.in_waiting).replace(b';', b'')
        print(f"Received: {received_data}")
    else:
        received_data = bytes("None Response", 'utf-8')
        print("No data received.")
    return {'response_time': datetime.now(),
            'response_bytes': received_data,
            'response_hex': received_data.hex() #,
            #'response_bin': bin(int(received_data, 16))[2:].zfill(len(received_data) * 4)
            }

#1
#@app.get("/getstate/{address}")    # By URL
@app.put("/getstate/")     # By Json
async def getstate(getstate_json: GetState_Json):
    time_received = datetime.now()
    if getstate_json.addr_dec != '':
        getstate_json.addr_dec = getstate_json.addr_dec - 1
#        addr = getstate_json.addr_dec
        addr = str(getstate_json.addr_dec.to_bytes(1, byteorder='little'))[4:6]
    else:
        addr = getstate_json.addr_hex

    cmd = '30'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command)
#    print(response['response_hex'][6:10])
#    result = response['response_hex'][6:10]
    result = response['response_hex'][8:10] + response['response_hex'][6:8] # reverse bytes = 0900 -> 0009
    result_bin = bin(int(result))

    if result == '0000':
        lock_state = "unlocked"
    else :
        lock_state = "locked"

    return {"received_time": time_received,
            "received_parameters": {"command": "getstate", "address": addr},
            "request_time": time_sent,
            "request_command": command,
            "response_time": response["response_time"],
            "response_bytes": response["response_bytes"],
            "response_hex": response["response_hex"],
            "response_result": {
#                "infrared": "0",
                "lock_response": response['response_hex'][6:10],
                "lock_state": lock_state,
            },
    }

#2
#@app.put("/unlock/{address}")
@app.put("/unlock/")
#async def unlock(address: str):
async def unlock(unlock_json: Unlock_Json):
    time_received = datetime.now()
    if unlock_json.addr_ncu_dec != '':
        unlock_json.addr_ncu_dec = unlock_json.addr_ncu_dec - 1
        addr_ncu = str(unlock_json.addr_ncu_dec.to_bytes(1, byteorder='little'))[4:6]
    else:
        addr_ncu = str(unlock_json.addr_ncu_hex)

    if unlock_json.addr_lock_dec != '':
        unlock_json.addr_lock_dec = unlock_json.addr_lock_dec - 1
        addr_lock = str(unlock_json.addr_lock_dec.to_bytes(1, byteorder='little'))[4:6]
    else:
        addr_lock = str(unlock_json.addr_lock_hex)

    addr_ncu =  addr_ncu[1:2]
    addr_lock = addr_lock[1:2]
    addr = addr_ncu + addr_lock

    cmd = '31'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs

    return {"received_time": time_received,
            "received_parameters": {"command": "unlock", "addr_ncu": addr_ncu, "addr_lock": addr_lock},
            "request_time": time_sent,
            "request_command": command,
            "response": response,
    }

#3
@app.put("/getallstates/")  # '02F0320327'
async def getallstates():
    time_received = datetime.now()
    cmd = '32'
    addr = 'F0'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command)

    return {"received_time": time_received,
            "received_parameters": {"address": addr, "command": "getallstates"},
            "request_time": time_sent,
            "request_command": command,
            "response_time": response["response_time"],
            "response_bytes": response["response_bytes"],
            "response_hex": response["response_hex"],
#            "response_result": {
#                "infrared":"0",
#                "lock":"0",
#                },
            }

#4
@app.put("/openall/")      # Default: '0200330338'
async def openall(openall_json: Openall_Json):
    time_received = datetime.now()
    if openall_json.addr_ncu_dec != '':
        openall_json.addr_ncu_dec = openall_json.addr_ncu_dec - 1
        addr_ncu = str(openall_json.addr_ncu_dec.to_bytes(2, byteorder='little'))[4:6]
    else:
        addr_ncu = str(openall_json.addr_ncu_hex)

    addr = addr_ncu

    cmd = '33'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs

    return {"received_time": time_received,
            "received_parameters": {"command": "openall", "addr_ncu": addr_ncu},
            "request_time": time_sent,
            "request_command": command,
            "response": response,
    }

#5.1
@app.put("/getunlocktime/")
async def getunlocktime(getunlocktime_json: Getunlocktime_Json):
    time_received = datetime.now()
    if getunlocktime_json.addr_ncu_dec != '':
        getunlocktime_json.addr_ncu_dec = getunlocktime_json.addr_ncu_dec - 1
        addr_ncu = str(getunlocktime_json.addr_ncu_dec.to_bytes(1, byteorder='little'))[4:6]
    else:
        addr_ncu = str(getunlocktime_json.addr_ncu_hex)

    addr = addr_ncu

    cmd = '37'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs

    return {"received_time": time_received,
            "received_parameters": {"command": "getsetunlocktime", "addr_ncu": addr_ncu},
            "request_time": time_sent,
            "request_command": command,
            "response": response,
    }

@app.put("/setunlocktime/")
async def setunlocktime(setunlocktime_json: Setunlocktime_Json):
    time_received = datetime.now()
    if setunlocktime_json.addr_ncu_dec != '':
        setunlocktime_json.addr_ncu_dec = setunlocktime_json.addr_ncu_dec - 1
        addr_ncu = str(setunlocktime_json.addr_ncu_dec.to_bytes(1, byteorder='little'))[4:6]
        data_hex = hex(setunlocktime_json.set_unlocktime_ms_dec)
        data_hex_10 = hex(setunlocktime_json.set_unlocktime_ms_dec // 10)
        data = hex(setunlocktime_json.set_unlocktime_ms_dec // 10)[2:4]
    else:
        addr_ncu = str(setunlocktime_json.addr_ncu_hex)

    addr = addr_ncu
#    data = addr_ncu

    cmd = '37'
    summa = check_sum3(addr, cmd, data)
    command = stx + addr + cmd + '00' + '00' + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs

    return {"received_time": time_received,
            "received_parameters": {"command": "getsetunlocktime", "addr_ncu": addr_ncu},
            "request_time": time_sent,
            "request_command": command,
            "response": response,
    }


#8.1
@app.get("/queryaddresstate/{address}")
async def queryaddresstate(address: str):
    if (ncu_settings["request_hex"]):
        command = ncu_commands["queryaddressstate_"] + address + ncu_commands["_queryaddressstate"]
        bytes_to_send = bytes.fromhex(command)
        # Send data to the serial device
        ser.write(bytes_to_send)
        print(f"Sending: {bytes_to_send.hex()}")

        # Wait a moment for the device to respond
        time.sleep(0.1)

        # Read data from the serial device
        # Read all bytes waiting in the input buffer
        if ser.in_waiting > 0:
            received_data = ser.read(ser.in_waiting)
            print(f"Received: {received_data}")
        else:
            print("No data received.")
            return {"response": "None"}
    return {"response": f"{received_data}"}


#8.2
@app.get("/querybusstate/{bus}")
async def querytime(bus: str):
    if (ncu_settings["request_hex"]):
        command = ncu_commands["querybusstate_"] + bus + ncu_commands["_querybusstate"]
        bytes_to_send = bytes.fromhex(command)
        # Send data to the serial device
        ser.write(bytes_to_send)
        print(f"Sending: {bytes_to_send.hex()}")

        # Wait a moment for the device to respond
        time.sleep(0.1)

        # Read data from the serial device
        # Read all bytes waiting in the input buffer
        if ser.in_waiting > 0:
            received_data = ser.read(ser.in_waiting)
            print(f"Received: {received_data}")
        else:
            print("No data received.")
            return {"response": "None"}
    return {"response": f"{received_data}"}

