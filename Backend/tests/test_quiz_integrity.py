import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import re
from fastapi.testclient import TestClient
from main import app
from app.ai.gemini_service import get_gemini_service, QuizQuestion, QuizOption


client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-student-token-1"}


def test_quiz_diversity_and_answer_integrity():
    """Verify that generated quiz questions vary meaningfully across dimensions and maintain strict answer integrity."""
    gemini = get_gemini_service()
    topic = "Binary Search Trees"

    questions = gemini.generate_quiz(topic=topic, count=5, difficulty="medium")
    assert len(questions) == 5, f"Expected 5 questions, got {len(questions)}"

    # 1. Answer Key & Options Integrity
    valid_keys = {"A", "B", "C", "D"}
    question_texts = []

    for q in questions:
        assert isinstance(q.id, int)
        assert len(q.question.strip()) > 10
        question_texts.append(q.question.strip())

        # Options verification
        assert len(q.options) == 4, f"Question {q.id} must have exactly 4 options"
        option_keys = {o.key for o in q.options}
        assert option_keys == valid_keys, f"Question {q.id} options must have keys A, B, C, D"

        # Correct answer verification
        assert q.correct_answer in valid_keys, f"Question {q.id} correct_answer must be in A..D"
        matching_opts = [o for o in q.options if o.key == q.correct_answer]
        assert len(matching_opts) == 1, f"Question {q.id} correct_answer '{q.correct_answer}' not found in options"
        assert len(matching_opts[0].text.strip()) > 0

        # Explanation verification
        assert len(q.explanation.strip()) > 10, f"Question {q.id} must have a non-trivial explanation"

    # 2. Diversity Check: Compare pairwise Jaccard similarity across questions
    for i in range(len(question_texts)):
        for j in range(i + 1, len(question_texts)):
            tokens_i = set(re.findall(r"\w+", question_texts[i].lower()))
            tokens_j = set(re.findall(r"\w+", question_texts[j].lower()))
            if tokens_i and tokens_j:
                jaccard = len(tokens_i & tokens_j) / len(tokens_i | tokens_j)
                assert jaccard < 0.75, f"Questions {i+1} and {j+1} are too similar (Jaccard: {jaccard:.2f}):\nQ{i+1}: {question_texts[i]}\nQ{j+1}: {question_texts[j]}"


def test_quiz_deterministic_verification_api():
    """Verify that POST /api/study/quiz/verify deterministically scores user answers."""
    payload = {
        "topic": "Dynamic Programming",
        "answers": [
            {"question_id": 1, "selected_key": "A", "correct_answer": "A"},
            {"question_id": 2, "selected_key": "B", "correct_answer": "B"},
            {"question_id": 3, "selected_key": "c", "correct_answer": "C"},
            {"question_id": 4, "selected_key": "A", "correct_answer": "D"},
            {"question_id": 5, "selected_key": "B", "correct_answer": "C"}
        ]
    }

    res = client.post("/api/study/quiz/verify", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["topic"] == "Dynamic Programming"
    assert data["total"] == 5
    assert data["score"] == 3  # Q1, Q2, Q3 correct
    assert data["percentage"] == 60.0

    results = data["results"]
    assert len(results) == 5
    assert results[0]["is_correct"] is True
    assert results[1]["is_correct"] is True
    assert results[2]["is_correct"] is True  # case-insensitive 'c' == 'C'
    assert results[3]["is_correct"] is False
    assert results[4]["is_correct"] is False


def test_quiz_endpoint_generation():
    """Verify that POST /api/study/quiz returns compliant quiz structure."""
    res = client.post("/api/study/quiz", json={"topic": "Dijkstra Algorithm", "num_questions": 5}, headers=AUTH_HEADERS)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["topic"] == "Dijkstra Algorithm"
    assert len(data["questions"]) == 5
    for q in data["questions"]:
        assert q["correct_answer"] in {"A", "B", "C", "D"}
        assert len(q["options"]) == 4
