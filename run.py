#!/usr/bin/env python3
from yaml import safe_load, dump
from pathlib import Path
import re
from datetime import datetime
import subprocess
import argparse
import logging
from openai import OpenAI, NOT_GIVEN
from pydantic import BaseModel
import json


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--system")
    args = parser.parse_args()
    return {
        "model": args.model,
        "temperature": args.temperature,
        "system": args.system,
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


class Evaluation(BaseModel):
    answer_satisfies_criteria: bool


def ask_one_question(question, model, temperature, system, is_evaluation=False):
    logging.info(f"Q: {question}")

    start_time = datetime.now()
    client = OpenAI(
        base_url="https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1",
        api_key=get_key(),
    )
    messages = [{"role": "user", "content": question}]
    if system:
        messages.append({"role": "system", "content": system})
    # Trying to use "client.chat.completions.create" produced an error:
    # > You tried to pass a `BaseModel` class to `chat.completions.create()`;
    # > You must use `beta.chat.completions.parse()` instead
    completions = client.beta.chat.completions.parse(
        messages=messages,  # type: ignore
        model=model,
        temperature=temperature,
        response_format=Evaluation if is_evaluation else NOT_GIVEN,
    )
    end_time = datetime.now()

    answers = [choice.message.content for choice in completions.choices]
    for answer in answers:
        logging.info(f"A: {answer}")
    if is_evaluation:
        answers = [
            json.loads(answer)["answer_satisfies_criteria"]
            for answer in answers
            if answer
        ][0]
    return answers, (end_time - start_time)


def ask_evaluation(question, answer, evaluation):
    # For the evaluation, we want boring, reliable answers,
    # even as we change the parameters for the primary query.
    # Might surface these as a separate config at some point.
    model = "gpt-4o-mini"
    temperature = 0
    system = None
    question_answer_evaluation = f"""First, read the following question and answer pair:

Question: {question}

Answer:
'''
{answer}
'''

Considering the response above, answer the following question with "True" or "False":
{evaluation}
"""
    return ask_one_question(
        question_answer_evaluation, model, temperature, system, is_evaluation=True
    )


def evaluate_one_answer(question, answer, evaluations_in):
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


def evaluate_all_answers(question, answers, evaluation_questions):
    evaluation_answers = {}
    for answer in answers:
        evaluation = evaluate_one_answer(question, answer, evaluation_questions)
        evaluation_answers[answer] = evaluation
    return evaluation_answers


def ask_all_questions(config):
    q_and_a_in = load_yaml("q-and-a.yaml")
    q_and_a_out = []
    for q_a in q_and_a_in:
        question = q_a["Q"]
        evaluations = q_a["evaluations"]

        human_answers = q_a["A"]
        human_answers_evaluations = evaluate_all_answers(
            question, human_answers, evaluations
        )

        llm_answers, runtime = ask_one_question(question, **config)
        llm_answers_evaluations = evaluate_all_answers(
            question, llm_answers, evaluations
        )

        q_and_a_out.append(
            {
                "question": question,
                "human": human_answers_evaluations,
                "llm": llm_answers_evaluations,
                "runtime": str(runtime),
            }
        )
    return q_and_a_out


def get_scores(q_and_a):
    scores = {}
    for human_llm in q_and_a:
        for agent in ["human", "llm"]:
            evaluations = human_llm[agent].values()
            flat_list = [e for e_list in evaluations for e in e_list]
            total = len(flat_list)
            correct = sum(1 for e in flat_list if e["expected"] == e["actual"])
            scores[agent] = f"{correct} / {total}"
    return scores


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
    scores = get_scores(q_and_a)
    results = {"metadata": metadata, "scores": scores, "q_and_a": q_and_a}
    save_results(datetime_now, results)
