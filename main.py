import csv
import json
import re
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

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
    cData["students"].append({"studentId": int(d[0]), "class": d[1]})


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.get("/api")
async def marksApi(request: Request):
    if q := request.query_params.getlist("name"):
        return dict(
            marks=[
                list(filter(lambda d: d["name"] == name, mData))[0]["marks"]
                for name in q
            ]
        )
    if c := request.query_params.getlist("class"):
        return dict(students=[s for s in cData["students"] if s["class"] in c])
    return cData


@app.get("/wikipedia-outline", response_class=PlainTextResponse)
async def wikiOutlineApi(request: Request):
    if q := request.query_params.get("country"):
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"https://en.wikipedia.org/wiki/{q.replace(' ', '_')}"
            )
            soup = BeautifulSoup(res.text, "html.parser")
            headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            outline = ""
            for head in headings:
                outline += f"{'#' * int(head.name[1:])} {head.text}\n\n"

            return outline
    else:
        return "?country is required."


@app.get("/imbd", response_class=JSONResponse)
async def imbdApi(request: Request):
    title = request.query_params.get("title", "")
    rating = request.query_params.getlist("rating")
    if any([title, len(rating)]):
        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_1_4; en-US) AppleWebKit/536.49 (KHTML, like Gecko) Chrome/49.0.3696.199 Safari/535"
            }
        ) as client:
            res = await client.get(
                f"https://www.imdb.com/search/title/?title={title}&user_rating={','.join(rating)}"
            )
            soup = BeautifulSoup(res.text, "html.parser")

            data = []
            for item in soup.select(".ipc-metadata-list-summary-item"):
                try:
                    # IMDb ID from href
                    href = item.select_one(".ipc-title-link-wrapper")["href"]
                    imdb_id = re.search(r"(tt\d+)", href).group(1)

                    # Title
                    title = item.select_one(".ipc-title__text").text.strip()

                    # Year
                    year = item.select_one(".dli-title-metadata-item").text.strip()

                    # Rating
                    rating = item.select_one(".ipc-rating-star--rating").text.strip()

                    data.append(
                        {"id": imdb_id, "title": title, "year": year, "rating": rating}
                    )
                except Exception as e:
                    print(f"Skipped one entry due to error: {e}")
            return data
    else:
        return {"success": False, "message": "Provide either ?title or ?ratings."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
