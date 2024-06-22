import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote, urlparse

load_dotenv()

album = "album/"
media_type = "image"
query = "nature scenes"
formatted_query = quote(query)

headers = {"Authorization": os.getenv("PEXEL_API_KEY")}
vid_prefix = "https://api.pexels.com/videos/search?"
img_prefix = "https://api.pexels.com/v1/search?"
suffix = f"query={formatted_query}&per_page=1"


def download_media(media_url):
    response = requests.get(media_url)
    response.raise_for_status()

    parsed_url = urlparse(media_url)
    filename = os.path.basename(parsed_url.path)

    with open(album + filename, "wb") as file:
        file.write(response.content)

    print(f"Image downloaded and saved as {filename}")


if media_type == "video":
    url = vid_prefix + suffix
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    media_url = response.json()["videos"][0]["video_files"][0]["link"]
    download_media(media_url)

elif media_type == "image":
    url = img_prefix + suffix
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    media_url = response.json()["photos"][0]["src"]["landscape"]
    download_media(media_url)
