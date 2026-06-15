import os

import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ["GITHUB_TOKEN"]

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

response = httpx.get("https://api.github.com/rate_limit", headers=headers)
response.raise_for_status()
data = response.json()

core = data["resources"]["core"]
print(f"Authenticated as token type: {data.get('rate', {}).get('limit')}")
print(f"Rate limit: {core['limit']} requests/hour")
print(f"Remaining: {core['remaining']}")
