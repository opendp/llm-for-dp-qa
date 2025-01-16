#!/usr/bin/env python3
from yaml import safe_load, dump
import requests
from pathlib import Path
import json
import re
from datetime import datetime
import subprocess
import argparse
import logging


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--temperature", type=float, default=0)
    args = parser.parse_args()
    return {
        "model": args.model,
        "temperature": args.temperature,
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


def ask_one_question(question, model, temperature):
    logging.info(f"Q: {question}")
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
    start_time = datetime.now()
    response = requests.request(
        method="POST",
        url=f"{api_base}/chat/completions",
        headers=headers,
        data=payload,
    )
    end_time = datetime.now()
    response.raise_for_status()
    answers = [choice["message"]["content"] for choice in response.json()["choices"]]
    for answer in answers:
        logging.info(f"A: {answer}")
    return answers, (end_time - start_time)


def ask_evaluation(question, answer, evaluation):
    # For the evaluation, we want boring, reliable answers,
    # even as we change the parameters for the primary query.
    # Might surface these as a separate config at some point.
    model = "gpt-4o-mini"
    temperature = 0
    question_answer_evaluation = f"""First, read the following question and answer pair:

Question: {question}

Answer:
'''
{answer}
'''

Considering the response above, answer the following question with "yes" or "no":
{evaluation}
"""
    return ask_one_question(question_answer_evaluation, model, temperature)


def evaluate(question, answer, evaluations_in):
    evaluations_out = []
    for expected in [True, False]:
        for evaluation in evaluations_in[expected]:
            actual, _runtime = ask_evaluation(question, answer, evaluation)
            evaluations_out.append(
                {
                    "evalution": evaluation,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return evaluations_out


def ask_all_questions(config):
    q_and_a_in = load_yaml("q-and-a.yaml")
    q_and_a_out = []
    for q_a in q_and_a_in:
        question = q_a["Q"]

        human_answers = q_a["A"]
        human_answers_evaluation = {}
        for answer in human_answers:
            evaluation = evaluate(question, answer, q_a["evaluations"])
            human_answers_evaluation[answer] = evaluation

        llm_answers, runtime = ask_one_question(question, **config)
        llm_answers_evaluation = {}
        for answer in llm_answers:
            evaluation = evaluate(question, answer, q_a["evaluations"])
            llm_answers_evaluation[answer] = evaluation

        q_and_a_out.append(
            {
                "question": question,
                "human": human_answers_evaluation,
                "llm": llm_answers_evaluation,
                "runtime": str(runtime),
            }
        )
    return q_and_a_out


def save_results(datetime_now, results):
    yaml_out = dump(
        results,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    timestamp = re.sub(r"\..*", "", datetime_now).replace(":", "-")
    out_path = Path(__file__).parent / "outputs" / f"{timestamp}.yaml"
    out_path.write_text(yaml_out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    datetime_now = datetime.now().isoformat()
    metadata = {
        "config": config,
        "datetime": datetime_now,
        "git_hash": get_git_hash(),
    }
    q_and_a = ask_all_questions(config)
    results = {"metadata": metadata, "q_and_a": q_and_a}
    save_results(datetime_now, results)
