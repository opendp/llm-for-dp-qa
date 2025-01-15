from yaml import safe_load, dump
import requests
from pathlib import Path
import json
import re
from datetime import datetime

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
    q_and_a_in = safe_load((Path(__file__).parent / 'q-and-a.yaml').open())
    q_and_a_out = []
    for question in q_and_a_in:
        answers = ask(question)
        q_and_a_out.append({
            'q': question,
            'a': answers,
        })
    yaml_out = dump(q_and_a_out, sort_keys=False, allow_unicode=True, default_flow_style=False)
    print(yaml_out)
    timestamp = re.sub(r'\..*', '', datetime.now().isoformat()).replace(':', '-')
    out_path = Path(__file__).parent / 'outputs' / f'{timestamp}.yaml'
    out_path.write_text(yaml_out)


