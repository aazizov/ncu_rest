import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json
import serial
import time

load_dotenv()
api_key = os.getenv("API_KEY")

class Request_Json(BaseModel):
    data_time: datetime.now()
    request_hex: str
    request_dec: str

class Response_Json(BaseModel):
    data_time: datetime.now()
    response_hex: str
    response_dec: str

class Request_485(BaseModel):
    data_time: datetime.now()
    stx: str = '02'     # Static
    addr: str
    command: str
    data: str
    etx: str = '03'     # Static
    summa: hex

class Response_485(BaseModel):
    data_time: datetime.now()
    result_hex: str
    result_dec: str

app = FastAPI()


producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    api_version=(0,11,5),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


kafka_topic = 'ncu_topic'
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

# def check_sum()

def serial_txrx(send: str):
    # Send data to the serial device
    ser.write(bytes.fromhex(send))
    # Wait a moment for the device to respond
    time.sleep(0.1)
    # Read data from the serial device
    # Read all bytes waiting in the input buffer
    if ser.in_waiting > 0:
        received_data = ser.read(ser.in_waiting)
        print(f"Received: {received_data}")
    else:
        print("No data received.")
    return {"response": f"{received_data}"}


#1
#@app.get("/getstate/{address}")    # By URL
@app.get("/getstate/{address}")     # By Json
async def getstate(address: str):
    if (ncu_settings["request_hex"]):
        command = ncu_commands["getstate_"] + address + ncu_commands["_getstate"]
    return {"response": f"{serial_txrx(command)}"}

#2
@app.put("/unlock/{address}")
async def unlock(address: str):
    if (ncu_settings["request_hex"]):
        command = ncu_commands["unlock_"] + address + ncu_commands["_unlock"]
        bytes_to_send = bytes.fromhex(command)
        # Send data to the serial device
        ser.write(bytes_to_send)
        print(f"Sending: {bytes_to_send.hex()}")

        # Wait a moment for the device to respond
        time.sleep(0.1)

    return {"response": "None"}

#3
@app.get("/getallstates")
async def getallstates():
    if (ncu_settings["request_hex"]):
        command = ncu_commands["getallstates"]
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
#            print(f"Received: {received_data.decode().strip()}")
            print(f"Received: {received_data}")
        else:
            print("No data received.")

    return {"response": {received_data}}

#4
@app.put("/openall/{bus}")      # Default: '0200330338'
async def openall(bus: str):
    if (ncu_settings["request_hex"]):
        command = ncu_commands["openall_"] + bus + ncu_commands["_openall"]
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
#            print(f"Received: {received_data.decode().strip()}")
            print(f"Received: {received_data}")
        else:
            print("No data received.")
            return {"response": f"None"}
    return {"response": f"{received_data}"}

#5.1
@app.get("/querytime")
async def querytime():
    if (ncu_settings["request_hex"]):
        command = ncu_commands["querytime"]
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

    return {"response": {received_data}}


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
