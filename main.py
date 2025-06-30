from fastapi import FastAPI

app = FastAPI()


#1
@app.get("/getstate/{address}")
async def getstate(address: str):
    return {"message": f"GetState for {address}"}

#3
@app.get("/getallstates")
async def getallstates():
    return {"message": "States ..."}

#5.1
@app.get("/querytime/{address}")
async def querytime(address: str):
    return {"message": f"QueryTime for {address}"}

#8.1
@app.get("/queryaddresstate/{address}")
async def queryaddresstate(address: str):
    return {"message": f"QueryAddrState for {address}"}

#8.2
@app.get("/querybusstate/{bus}")
async def querytime(bus: str):
    return {"message": f"QueryBusState for {bus}"}
