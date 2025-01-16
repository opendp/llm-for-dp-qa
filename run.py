from yaml import safe_load, dump
import requests
from pathlib import Path
import json
import re
from datetime import datetime
import subprocess


def get_config(model="gpt-4o-mini", temperature=0):
    return {
        "model": model,
        "temperature": temperature,
    }


def get_git_hash():
    completed = subprocess.run(
        "git rev-parse --short HEAD", shell=True, capture_output=True
    )
    return completed.stdout.decode().strip()


def get_key():
    credentials = load_yaml("credentials.yaml")
    return credentials["key"]


def load_yaml(file_name):
    return safe_load((Path(__file__).parent / file_name).open())


api_base = "https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1"


def ask(question, model, temperature):
    headers = {
        "Content-Type": "application/json",
        "api-key": get_key(),
    }
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": question}],
            "temperature": temperature,
        }
    )
    response = requests.request(
        method="POST",
        url=f"{api_base}/chat/completions",
        headers=headers,
        data=payload,
    )
    response.raise_for_status()
    answers = [choice["message"]["content"] for choice in response.json()["choices"]]
    return answers


if __name__ == "__main__":
    config = get_config()
    q_and_a_in = load_yaml("q-and-a.yaml")
    q_and_a_out = []
    for q_a in q_and_a_in:
        question = q_a["Q"]
        human_answer = q_a["A"]
        start_time = datetime.now()
        llm_answers = ask(question, **config)
        end_time = datetime.now()
        q_and_a_out.append(
            {
                "question": question,
                "human answer": human_answer,
                "llm answers": llm_answers,
                "runtime": str(end_time - start_time),
            }
        )

    datetime_now = datetime.now()
    metadata = {
        "config": config,
        "git_hash": get_git_hash(),
        "datetime": datetime_now.isoformat(),
    }
    yaml_out = dump(
        {"metadata": metadata, "q_and_a": q_and_a_out},
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    print(yaml_out)
    timestamp = re.sub(r"\..*", "", datetime_now.isoformat()).replace(":", "-")
    out_path = Path(__file__).parent / "outputs" / f"{timestamp}.yaml"
    out_path.write_text(yaml_out)
