import csv
import json
from typing import Dict, List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


mData: List[Dict[str, str | int]] = json.load(open("data/q-vercel-python.json"))

cReader = csv.reader(open("data/q-fastapi.csv"))
cData: Dict[str, List[Dict[str, str]]] = dict(students=[])

next(cReader)
for d in cReader:
    cData["students"].append({"studentId": d[0], "class": d[1]})

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/api")
async def marksApi(request: Request):
    if q := request.query_params.getlist("name"):
        return dict(
            marks = [list(filter(lambda d: d["name"] == name, mData))[0]["marks"] for name in q]
        )
    if c := request.query_params.getlist("class"):
        return dict(
            students = [s for s in cData["students"] if s["class"] in c]
        )
    return cData

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
