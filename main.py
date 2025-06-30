from fastapi import FastAPI

app = FastAPI()

ncu_settings = {
    "response_hex": True,
    "kafka_message_long": True, # received_datetime:command|request_datetime:command|response_datetime:command
    "kafka_ipaddress_port": "192.168.0.107:9092",
    "kafka_topic": "ncu"
}

ncu_commands = {
    "getstate_": "02",
    "_getstate": "300335",
    "unlock_": "02",
    "_unlock": "310338",
    "getallstates": "02F0320327",
    "openall_": "02",
    "_openall": "330338",
    "querytime": "020037033C",
    "queryaddressstate_": "02",
    "_queryaddressstate": "3A033F",
    "querybusstate_": "02",
    "_querybusstate": "3A032F"
}

#1
@app.get("/getstate/{address}")
async def getstate(address: str):
    command = ncu_commands["getstate_"] + address + ncu_commands["_getstate"]
#    return {"message": f"GetState {command} for {address}"}
#    return {"response": f"{command}"}
    if (ncu_settings["response_hex"]):
        response = f"{command}"
    else:
        response = f"All OK"

    if(ncu_settings["kafka_message_long"]):
        kafka_message = f"/getstate/{address}" + "|" + response
    print(kafka_message)
    return response

#2
@app.put("/unlock/{address}")
async def unlock(address: str):
    return {"response": f"Unlock for {address}"}

#3
@app.get("/getallstates")
async def getallstates():
    return {"response": "States..."}

#4
@app.put("/openall/{bus}")
async def openall(bus: str):
    return {"response": f"Openall... for {bus}"}

#5.1
@app.get("/querytime")
async def querytime():
    return {"response": f"QueryTime... "}

#8.1
@app.get("/queryaddresstate/{address}")
async def queryaddresstate(address: str):
    return {"response": f"QueryAddrState for {address}"}

#8.2
@app.get("/querybusstate/{bus}")
async def querytime(bus: str):
    return {"response": f"QueryBusState for {bus}"}
