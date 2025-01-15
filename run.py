from yaml import safe_load, dump
import requests
from pathlib import Path
import json

def ask(question, model="gpt-4o-mini", temperature=0.7):
    credentials = safe_load((Path(__file__).parent / 'credentials.yaml').open())
    key = credentials['key']

    url = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
        {
            "role": "user",
            "content": question
        }
        ],
        "temperature": temperature
    })
    headers = {
        'Content-Type': 'application/json',
        'api-key': key
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    response_json = response.json()
    answers = [
        choice['message']['content'] for choice in response_json['choices']
    ]
    return answers


if __name__ == '__main__':
    answers = ask('What is the capital of Georgia?')
    print(answers)


