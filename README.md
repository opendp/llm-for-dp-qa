# llm-for-dp-qa
Experiments with LLMs for Q+A about DP

To get started:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
cp llm_for_dp_qa/credentials{-template,}.yaml
```

Fill in the git-ignored `credentials.yaml` with the [key and secret for this app](https://portal.apis.huit.harvard.edu/my-apps/6dce5383-bcb6-4c9f-bd14-8f59d356b221).

You should then be able to run the queries against the API: The output will also be written to `outputs/`:
```
llm_for_dp_qa/run.py
ls llm_for_dp_qa/outputs
```
