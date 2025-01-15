from yaml import safe_load, dump
import requests
from pathlib import Path
import json

if __name__ == '__main__':
    credentials = safe_load((Path(__file__).parent / 'credentials.yaml').open())
    key = credentials['key']
    secret = credentials['secret']

    url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
        {
            "role": "user",
            "content": "What is 2+2?"
        }
        ],
        "temperature": 0.7
    })
    headers = {
        'Content-Type': 'application/json',
        'api-key': key
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    print(response.text)


