
import os
import json
from typing import Literal
from dataclasses import dataclass
from datetime import datetime
import uuid
import urllib.parse
import requests
import shutil

from lib.utils import *
from lib.config import *


@dataclass
class GoogleImage:
    result_index: int
    url: str
    context_url: str
    accessed: datetime
    request: dict
    search_parameters: dict
    width: int
    height: int
    byte_size: int
    file_format: str
    title: str = None
    query: str = None
    ext: str = None

    downloaded: bool = False
    local_path: Path = None

    def __post_init__(self):
        self.query = self.search_parameters["q"]
        self.ext = Path(self.url).suffix

    def download(self) -> bool:
        path = IMG_DIR / f"google-img-{self.accessed.strftime(STRFTIME_FULL)}-{(self.result_index+1):03}-{str(uuid.uuid4())[:4]}-{ESCAPE_PATH(self.query)}{self.ext}"
        # print(f"Downloading image at {self.url} ...")
        with open(path, "wb") as f:
            # res = requests.get(self.url, stream=True)
            res = requests.get(self.url, stream=True, headers={
                "User-Agent": "karaokay"
            })
            if not res.ok:
                return res.status_code
            shutil.copyfileobj(res.raw, f)
        self.downloaded = True
        self.local_path = path
        return res.status_code


def preprocess_query(query: str, language: str):
    # words = list(set(query.split(" ")))
    # words = [w for w in words if w not in query_stopwords[language]]
    # return " ".join(words)
    return query


# TODO types
def google_image_search(query: str,
                        save_results: bool = False,
                        output: bool = True,
                        num_downloads: int = 10,
                        num: int = 10,
                        imgSize="large",
                        fileType=None,
                        gl: str = "de",
                        hl: str = "de",
                        safe: Literal["off", "active"] = "off"):
    
    if num_downloads is not None and num is None:
        num = min(num, num_downloads)
    num = min(10, num)

    parameters = {
        "key": os.getenv("GOOGLE_PSE_API_KEY"),
        "cx": os.getenv("GOOGLE_PSE_ID"),
        "searchType": "image",
        "q": query,
        "num": num,
        "imgSize": imgSize,
        "gl": gl,  # Geolocation of end user
        "hl": hl,  # user interface language
        "safe": safe,
        "fileType": fileType
    }
    parameters = {k: v for k, v in parameters.items() if v is not None}
    url = f"https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(parameters)
    if not uri_validator(url):
        raise ValueError(f"Invalid URL: {url}")
    
    if output:
        print(f"Accessing Google image search ...")
    res = requests.get(url)

    if not res.ok:
        res_data = res.json()
        if "error" in res_data:
            if output:
                print(f"Error {res.status_code}: {res_data['error']['message']}")
        return [], res_data, parameters
        # print(json.dumps(res.json(), indent=2))
        # raise ValueError(f"Request failed (status code {res.status_code})")
    res = res.json()

    if save_results:
        path = SEARCH_RESULTS_DIR / f"google-result-{NOW()}-{ESCAPE_PATH(query)}.json"
        json.dump(res, open(path, "w", encoding="utf8"), indent=2)
        if output:
            print(f"Search results for query '{query}'\nSaved to {path}.")

    if "items" not in res:
        if output:
            print(f"No images found.")
        return [], res, parameters

    # Create Image objects
    # res = json.load(open(r"D:\GitProjects\karaokay\karaokay-backend\data\google-result-20240222-235231-BieberSpurenBaum.json", "r", encoding="utf8"))
    accessed = datetime.now()
    imgs = [GoogleImage(result_index=i,
                        url=item["link"],
                        context_url=item["image"]["contextLink"],
                        query=res["queries"]["request"][0]["searchTerms"],
                        request=res["queries"]["request"][0],
                        search_parameters=parameters,
                        width=item["image"]["width"],
                        height=item["image"]["height"],
                        byte_size=item["image"]["byteSize"],
                        file_format=item["fileFormat"],
                        accessed=accessed) for i, item in enumerate(res["items"])]
    
    # Filter and download the images
    download_counter = 0
    for img in imgs:
        # Image filters
        if img.ext not in [".png", ".jpg", ".jpeg", ".gif"]:
            continue
        if img.width / img.height > 16/9:
            continue
        if img.width < 200 or img.height < 200:
            continue
        img.download()
        if img.downloaded:
            download_counter += 1
        if num_downloads is not None and download_counter >= num_downloads:
            break
    
    imgs = [img for img in imgs if img.downloaded]
    if output:
        print(f"Downloaded {len(imgs)} images from Google.")
        # print(f"Downloaded {len(imgs)} images for the query '{query}'.")
    return imgs, res, parameters


if __name__ == "__main__":
    query = "Fugenschnurz"
    imgs, res, parameters = google_image_search(query=query, imgSize=None)
