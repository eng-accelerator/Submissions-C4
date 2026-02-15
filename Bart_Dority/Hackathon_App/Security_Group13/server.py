from fastapi import FastAPI

app = FastAPI()

import json


with open("mock_logs.json") as MOCK_LOGS:
    MOCK_LOGS = json.load(MOCK_LOGS)


@app.get("/logs")
def get_logs():
    print ("got log request")
    return MOCK_LOGS
