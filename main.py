import os
import json

from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json
import serial
import time

stx = '02'  # Start Byte of majority of commands
etx = '03'  # Stop Byte of majority of commands

class Request_Json(BaseModel):
    stx: str = '02'     # Static
    addr: str = ''
    cmd: str = ''
    data: str = ''
    etx: str = '03'     # Static

class Response_Json(BaseModel):
    lock: str = 'Open'
    infrared: str = '01'

class GetVersion_Json(BaseModel):
    addr_board_dec: int = 1     # Board#1

class GetStateBoard_Json(BaseModel):
    board: int = 1

class GetStateLock_Json(BaseModel):
    board: int = 1
    lock: int = 1

class Unlock_Json(BaseModel):
    board: int = 1
    lock: int = 1

class UnlockAll_Json(BaseModel):
    board: int = 1

class Getunlocktime_Json(BaseModel):
    board: int = 1

class Setunlocktime_Json(BaseModel):
    board: int = 1
    set_unlocktime_ms_dec: int = 550     # ==550ms   # ==0x27*10=550 ms


load_dotenv()
api_key = os.getenv("API_KEY")
kafka_address = str(os.getenv("KAFKA_IP"))
kafka_port = str(os.getenv("KAFKA_PORT"))
kafka_topic = os.getenv("KAFKA_TOPIC")
rs485_address = os.getenv("COM_PORT")
max_retries = int(os.getenv("MAX_RETRIES"))
retry_delay_seconds = int(os.getenv("RETRY_DELAY_SECONDS"))


producer = KafkaProducer(
    bootstrap_servers= kafka_address+':'+kafka_port, #'localhost:9092',
    api_version=(0,11,5),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

for attempt in range(int(max_retries)):
    try:
        ser = serial.Serial(
            port=rs485_address,  # '/dev/cu.usbserial-B000KAZT', # MacBook RS232 'COM1',     # Serial port name
            baudrate=19200,  # Baud rate
            parity=serial.PARITY_NONE,  # Parity setting (e.g., serial.PARITY_ODD, serial.PARITY_EVEN)
            stopbits=serial.STOPBITS_ONE,  # Stop bits (e.g., serial.STOPBITS_TWO)
            bytesize=serial.EIGHTBITS,  # Data bits (e.g., serial.SEVENBITS)
            timeout=1  # Read timeout in seconds
        )
        print(ser)
        break  # Exit loop if operation succeeds
    except serial.SerialException as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay_seconds} seconds...")
            time.sleep(retry_delay_seconds)
        else:
            print("Maximum retries reached. Operation failed permanently.")
            try:
                producer.send(kafka_topic, f"Attempt at {datetime.now()} to Connect to {rs485_address} failed")
            except Exception as e:
                print(f"Failed to send message to {kafka_address+':'+kafka_port} topic {kafka_topic}; {e}")

'''
# Start of Program Initialization
try:
# To Find and Connect to Serial Port
    ser = serial.Serial(
        port= rs485_address, # '/dev/cu.usbserial-B000KAZT', # MacBook RS232 'COM1',     # Serial port name
        baudrate=19200,          # Baud rate
        parity=serial.PARITY_NONE, # Parity setting (e.g., serial.PARITY_ODD, serial.PARITY_EVEN)
        stopbits=serial.STOPBITS_ONE, # Stop bits (e.g., serial.STOPBITS_TWO)
        bytesize=serial.EIGHTBITS,  # Data bits (e.g., serial.SEVENBITS)
        timeout=1               # Read timeout in seconds
    )
except serial.SerialException as e:
    print(f"Cannot open COM Port. {e}")
'''


app = FastAPI()


#1
@app.put("/getstateboard/")     # By Json
async def getstateboard(getstate_json: GetStateBoard_Json):
    '''
    We can get state of all Locks(1..16) for any Board(1..10).
    We have to Request number of Board(1..10).
    '''
    time_received = datetime.now()
    getstate_json.board = getstate_json.board - 1
    addr_ncu = str(getstate_json.board.to_bytes(1, byteorder='little').hex()) #[5:6]
    addr = addr_ncu[::-1] # + '0'

    cmd = '30'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command)

    result = response['response_hex'][8:10] + response['response_hex'][6:8] # reverse bytes = 0900 -> 0009
    result_bin = format(int(result, 16), 'b')[::-1]
    if len(result_bin) < 16:
        result_bin = result_bin.ljust(16, '0')

    lock_index = 0
    locks_array = [None] * 16   # Initial empty Array

    while lock_index < 16:
        locks_array[lock_index] = result_bin[lock_index]
        lock_index = lock_index + 1

    return {"received_time": time_received,
            "received_parameters": {"command": "getstate", "address": addr},
            "request_time": time_sent,
            "request_command": command,
            "response_time": response["response_time"],
            "response_hex": response["response_hex"],
            "response_result": {
                "result": result_bin,
                "locks_state": "All Locks Locked",
            },
    } if result_bin == '1111111111111111' \
        else {"received_time": time_received,
            "received_parameters": {"command": "getstate", "address": addr},
            "request_time": time_sent,
            "request_command": command,
            "response_time": response["response_time"],
            "response_hex": response["response_hex"],
            "response_result": {
                "result": result_bin,
                "Board": getstate_json.board + 1,
                "Lock#1": locks_array[0],
                "Lock#2": locks_array[1],
                "Lock#3": locks_array[2],
                "Lock#4": locks_array[3],
                "Lock#5": locks_array[4],
                "Lock#6": locks_array[5],
                "Lock#7": locks_array[6],
                "Lock#8": locks_array[7],
                "Lock#9": locks_array[8],
                "Lock#10": locks_array[9],
                "Lock#11": locks_array[10],
                "Lock#12": locks_array[11],
                "Lock#13": locks_array[12],
                "Lock#14": locks_array[13],
                "Lock#15": locks_array[14],
                "Lock#16": locks_array[15],
            },
    }

@app.put("/getstatelock/")     # By Json
async def getstatelock(getstate_json: GetStateLock_Json):
    '''
    We can get state of one requested Lock(1..16) for any Board(1..10).
    We have to Request number of Board(1..10) and number of Lock(1..16).
    '''
    time_received = datetime.now()
    getstate_json.board = getstate_json.board - 1
    getstate_json.lock = getstate_json.lock - 1
    addr_ncu = str(getstate_json.board.to_bytes(1, byteorder='little').hex()) #[5:6]
    addr = addr_ncu[::-1] # + '0'

    cmd = '30'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command)
    result = response['response_hex'][8:10] + response['response_hex'][6:8] # reverse bytes = 0900 -> 0009

    result_bin = format(int(result, 16), 'b')[::-1]

    if len(result_bin) < 16:
        result_bin = result_bin.ljust(16, '0')

    lock_index = 0
    locks_array = [None] * 16   # Initial empty Array

    while lock_index < 16:
        locks_array[lock_index] = result_bin[lock_index]
        lock_index = lock_index + 1

    return {"received_time": time_received,
            "received_parameters": {"command": "getstate", "address": addr},
            "request_time": time_sent,
            "request_command": command,
            "response_time": response["response_time"],
            "response_hex": response["response_hex"],
            "response_result": {
                "result": result_bin,
                "Board": getstate_json.board + 1,
                "Lock#"+str(getstate_json.lock+1): locks_array[getstate_json.lock],
            },
    }


@app.put("/unlock/")
async def unlock(unlock_json: Unlock_Json):
    '''
    We can unlock any Lock on any Board.
    We have to Request number of Board(1..10), and number of Lock(1..16).
    Response is absent.
    '''
    time_received = datetime.now()

    unlock_json.board = unlock_json.board - 1
    addr_ncu = str(unlock_json.board.to_bytes(1, byteorder='little').hex()) #[4:6]
    unlock_json.lock = unlock_json.lock - 1
    addr_lock = str(unlock_json.lock.to_bytes(1, byteorder='little').hex()) #[4:6]
    addr = addr_ncu[1:2] + addr_lock[1:2]

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
@app.put("/getstatesall/")  # '02F0320327'
async def getstatesall():
    '''
    We can get the state of all locks (1..16) for all boards (1..10) at the same time.
    Request parameters are not required.
    '''
    time_received = datetime.now()
    cmd = '32'
    addr = 'F0'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command)

    count_of_board = len(response["response_hex"])/18       # Length of one BoardResponse = 18 symbols
    i = 1
    while i <= count_of_board:
        if i == 1:
            data = [analyze_response(i, response["response_hex"][0:18])]
        elif i <= count_of_board:
            data.append(analyze_response(i, response["response_hex"][0:18]))

        response['response_hex'] = response['response_hex'][18:]    # Trim Left 18 symbols for One Board
        i = i + 1

    return {"received_time": time_received,
            "received_parameters": {"address": addr, "command": "getallstates"},
            "request_time": time_sent,
            "request_command": command,
            "response_time": response["response_time"],
            "response_hex": response["response_hex"],
            "response_result": data,
            }

#4
@app.put("/unlockall/")      # Default: '0200330338'
async def unlockall(unlockall_json: UnlockAll_Json):
    '''
    We can unlock all Locks on any Board.
    We have to Request number of Board(1..10).
    Response is absent.
    '''
    time_received = datetime.now()
    unlockall_json.board = unlockall_json.board - 1
    addr_ncu = str(unlockall_json.board.to_bytes(1, byteorder='little').hex()) #[5:6]
    addr = addr_ncu[::-1] # Reverse Board Address # 00 - board 1, 10 - board 2, 20 - board 3

    cmd = '33'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs

    return {"received_time": time_received,
            "received_parameters": {"command": "unlockall", "addr_ncu": addr_ncu},
            "request_time": time_sent,
            "request_command": command,
            "response": response,
    }

#5.1
@app.put("/getunlocktime/")
async def getunlocktime(getunlocktime_json: Getunlocktime_Json):
    '''
    ! GetUnlockTime NOT work with current version of Software. Will work after upgrade of Software.
    '''
    time_received = datetime.now()
    if getunlocktime_json.board != '':
        getunlocktime_json.board = getunlocktime_json.board - 1
        addr_ncu = str(getunlocktime_json.board.to_bytes(1, byteorder='little'))[4:6]
    else:
        addr_ncu = str(getunlocktime_json.addr_ncu_hex)

    addr = addr_ncu

    cmd = '37'
    summa = check_sum2(addr, cmd, '')
    command = stx + addr + cmd + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs

    return {"received_time": time_received,
            "received_parameters": {"command": "getunlocktime", "addr_ncu": addr_ncu},
            "request_time": time_sent,
            "request_command": command,
            "response": response,
    }

@app.put("/setunlocktime/")
async def setunlocktime(setunlocktime_json: Setunlocktime_Json):
    '''
    ! SetUnlockTime NOT work with current version of Software. Will work after upgrade of Software.
    '''
    time_received = datetime.now()
    if setunlocktime_json.board != '':
        setunlocktime_json.board = setunlocktime_json.board - 1
        addr_ncu = str(setunlocktime_json.board.to_bytes(1, byteorder='little'))[4:6]
        data_hex = hex(setunlocktime_json.set_unlocktime_ms_dec)
        data_hex_10 = hex(setunlocktime_json.set_unlocktime_ms_dec // 10)
        data = hex(setunlocktime_json.set_unlocktime_ms_dec // 10)[2:4]
    else:
        addr_ncu = str(setunlocktime_json.addr_ncu_hex)

    addr = addr_ncu

    cmd = '37'
    summa = check_sum3(addr, cmd, data)
    command = stx + addr + cmd + '00' + '00' + etx + summa
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs

    return {"received_time": time_received,
            "received_parameters": {"command": "setunlocktime", "addr_ncu": addr_ncu},
            "request_time": time_sent,
            "request_command": command,
            "response": response,
    }


@app.put("/getversion/")
async def getversion(getversion_json: GetVersion_Json):
    '''
    ! GetVersion and other OTA functions(0xB5 & 0xB6) NOT work with current old Board CU-V2.1 20201-06-08. Will work after upgrade of Board and Software.
    '''
    time_received = datetime.now()
    getversion_json.addr_board_dec = getversion_json.addr_board_dec - 1
    addr_board = str(getversion_json.addr_board_dec.to_bytes(1, byteorder='little'))[4:6]
    cmd = 'B6'
    command = 'F5' + cmd + addr_board + '005F' + '0A'
    time_sent = datetime.now()
    response = serial_txrx(command) # Response No by Docs
    return {"received_time": time_received,
            "received_parameters": {#"address": addr,
                                    "command": "getversion"},
            "request_time": time_sent,
            "request_command": command,
            "response_time": response["response_time"],
            "response_hex": response["response_hex"],
            }

''' ! Also Not Response - May be Unsupported on this old Board/Software
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
'''

# Functions
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
            'response_hex': received_data.hex()
            }

def analyze_response(board_number: int, result_one_board: str):
    result = result_one_board[8:10] + result_one_board[6:8]  # reverse bytes = 0900 -> 0009
    result_bin = format(int(result, 16), 'b')[::-1]
    if len(result_bin) < 16:
        result_bin = result_bin.ljust(16, '0')

    lock_index = 0
    locks_array = [None] * 16  # Initial empty Array
    while lock_index < 16:
        locks_array[lock_index] = result_bin[lock_index]
        lock_index = lock_index + 1

    return {"Board#": board_number,
     "Lock#1": locks_array[0],
     "Lock#2": locks_array[1],
     "Lock#3": locks_array[2],
     "Lock#4": locks_array[3],
     "Lock#5": locks_array[4],
     "Lock#6": locks_array[5],
     "Lock#7": locks_array[6],
     "Lock#8": locks_array[7],
     "Lock#9": locks_array[8],
     "Lock#10": locks_array[9],
     "Lock#11": locks_array[10],
     "Lock#12": locks_array[11],
     "Lock#13": locks_array[12],
     "Lock#14": locks_array[13],
     "Lock#15": locks_array[14],
     "Lock#16": locks_array[15],
     }
