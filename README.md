# llm-for-dp-qa
Experiments with LLMs for Q+A about DP

To get started:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

Fill in `credentials-template.yaml` with the [key and secret for this app](https://portal.apis.huit.harvard.edu/my-apps/6dce5383-bcb6-4c9f-bd14-8f59d356b221), and then copy into place:
```
cp credentials-template.yaml credentials.yaml
```

You should then be able to run the queries against the API, and there should be a new output file:
```
run.py
ls outputs
```
