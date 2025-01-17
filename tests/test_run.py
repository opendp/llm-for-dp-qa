from llm_for_dp_qa.run import get_scores


def test_get_scores():
    q_and_a = [
        {
            "human": {
                "q1": [
                    {"expected": True, "actual": True},
                    {"expected": True, "actual": True},
                ]
            },
            "llm": {
                "q1": [
                    {"expected": True, "actual": False},
                    {"expected": True, "actual": False},
                ]
            },
        },
        {
            "human": {
                "q1": [
                    {"expected": False, "actual": False},
                ],
                "q2": [
                    {"expected": False, "actual": False},
                ],
            },
            "llm": {
                "q1": [
                    {"expected": False, "actual": True},
                ],
                "q2": [
                    {"expected": False, "actual": False},  # Let it get one right.
                ],
            },
        },
    ]
    assert get_scores(q_and_a) == {"human": "4 / 4", "llm": "1 / 4"}
