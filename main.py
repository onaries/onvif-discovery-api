import os
from fastapi import FastAPI
from utils import discovery_streaming_devices, extract_ip

app = FastAPI()


@app.get("/discovery")
async def discovery():
    return discovery_streaming_devices()


if __name__ == "__main__":
    import uvicorn

    ip = extract_ip()
    with open("/share/ip.txt", "w") as f:
        f.write(ip)

    API_PORT = os.environ.get("API_PORT", 8000)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(API_PORT),
    )
