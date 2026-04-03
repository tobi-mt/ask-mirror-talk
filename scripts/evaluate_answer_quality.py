#!/usr/bin/env python3
"""
Evaluate Ask Mirror Talk answer quality against a small curated audit set.

This script can:
1. Send a question set to a live Ask Mirror Talk API.
2. Capture answer text, citations, latency, and cache status.
3. Optionally score each answer with an OpenAI model using a quality rubric.

Examples:
  .venv/bin/python scripts/evaluate_answer_quality.py
  .venv/bin/python scripts/evaluate_answer_quality.py --base-url https://ask-mirror-talk-production.up.railway.app
  .venv/bin/python scripts/evaluate_answer_quality.py --no-eval
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))


DEFAULT_BASE_URL = os.getenv("ASK_MIRROR_TALK_API_URL", "https://ask-mirror-talk-production.up.railway.app")

DEFAULT_QUESTIONS = [
    "What does resurrection hope change about how I face suffering today?",
    "How do I know when faith is becoming performative instead of real?",
    "What is a wise first step when I feel spiritually numb?",
    "How can I rebuild self-worth after repeated rejection?",
    "What does courage look like when the cost is relational?",
    "How do I grieve without losing my sense of purpose?",
    "What can I do when forgiveness feels morally confusing, not freeing?",
    "How do I tell the difference between healing and avoidance?",
]


@dataclass
class AnswerSample:
    question: str
    answer: str
    citations: list[dict]
    latency_ms: int | None
    cached: bool | None
    follow_ups: list[str]


def fetch_answer(base_url: str, question: str, timeout_s: float = 90.0) -> AnswerSample:
    url = base_url.rstrip("/") + "/ask"
    with httpx.Client(timeout=timeout_s) as client:
        response = client.post(url, json={"question": question})
        response.raise_for_status()
        payload = response.json()
    return AnswerSample(
        question=question,
        answer=str(payload.get("answer", "")).strip(),
        citations=list(payload.get("citations", []) or []),
        latency_ms=payload.get("latency_ms"),
        cached=payload.get("latency_ms") == 0 or payload.get("cached"),
        follow_ups=list(payload.get("follow_up_questions", []) or []),
    )


def fetch_answer_local(question: str) -> AnswerSample:
    from app.core.db import get_session_local
    from app.qa.service import answer_question

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        payload = answer_question(
            db,
            question,
            user_ip="audit-local",
            log_interaction=False,
            bypass_cache=True,
        )
    finally:
        try:
            db.close()
        except Exception:
            pass

    return AnswerSample(
        question=question,
        answer=str(payload.get("answer", "")).strip(),
        citations=list(payload.get("citations", []) or []),
        latency_ms=payload.get("latency_ms"),
        cached=bool(payload.get("cached", False)),
        follow_ups=list(payload.get("follow_up_questions", []) or []),
    )


def make_uncached_questions(questions: list[str], seed: str | None = None) -> list[str]:
    marker = seed or str(int(time.time()))
    return [f"{question} [audit:{marker}:{idx + 1}]" for idx, question in enumerate(questions)]


def build_eval_prompt(sample: AnswerSample) -> str:
    citations_summary = []
    for citation in sample.citations[:5]:
        title = citation.get("episode_title", "Unknown episode")
        quote = str(citation.get("text", "")).strip()
        if quote:
            citations_summary.append(f"- {title}: {quote}")
        else:
            citations_summary.append(f"- {title}")
    citation_block = "\n".join(citations_summary) if citations_summary else "- No citations provided"

    return f"""Evaluate this Ask Mirror Talk answer.

Question:
{sample.question}

Answer:
{sample.answer}

Citations:
{citation_block}

Score each category from 1 to 5:
- directness
- specificity
- grounding
- usefulness
- warmth
- distinctiveness
- overall

Rubric:
- directness: does the answer answer the question immediately and clearly?
- specificity: does it avoid generic filler and say something concrete?
- grounding: does it feel meaningfully rooted in the cited wisdom?
- usefulness: does it leave the user with a practical takeaway, next step, or clear reframe?
- warmth: does it feel human and emotionally intelligent without getting vague?
- distinctiveness: does it avoid sounding like a generic inspirational essay?
- overall: overall quality for a premium reflective product

Return ONLY valid JSON in this shape:
{{
  "scores": {{
    "directness": 0,
    "specificity": 0,
    "grounding": 0,
    "usefulness": 0,
    "warmth": 0,
    "distinctiveness": 0,
    "overall": 0
  }},
  "strengths": ["..."],
  "weaknesses": ["..."],
  "summary": "..."
}}
"""


def evaluate_with_openai(samples: list[AnswerSample], model: str = "gpt-4.1-mini") -> list[dict]:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for evaluation mode")

    client = OpenAI(api_key=api_key)
    results: list[dict] = []

    for sample in samples:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a rigorous but fair evaluator of reflective question-answer systems. "
                        "Return only JSON and keep judgments specific."
                    ),
                },
                {"role": "user", "content": build_eval_prompt(sample)},
            ],
        )
        text_out = getattr(response, "output_text", "").strip()
        results.append(json.loads(text_out))

    return results


def print_capture_report(samples: list[AnswerSample]) -> None:
    print("\n" + "=" * 80)
    print("  ASK MIRROR TALK - ANSWER CAPTURE")
    print("=" * 80 + "\n")
    for idx, sample in enumerate(samples, 1):
        print(f"{idx}. {sample.question}")
        print(f"   Latency: {sample.latency_ms}ms | Citations: {len(sample.citations)} | Cached: {sample.cached}")
        print(f"   Answer: {sample.answer[:700]}")
        print()


def print_eval_report(samples: list[AnswerSample], evaluations: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("  ASK MIRROR TALK - ANSWER QUALITY REPORT")
    print("=" * 80 + "\n")

    aggregate: dict[str, list[float]] = {
        "directness": [],
        "specificity": [],
        "grounding": [],
        "usefulness": [],
        "warmth": [],
        "distinctiveness": [],
        "overall": [],
    }

    for idx, (sample, evaluation) in enumerate(zip(samples, evaluations), 1):
        scores = evaluation["scores"]
        for key in aggregate:
            aggregate[key].append(float(scores[key]))

        print(f"{idx}. {sample.question}")
        print(
            "   Scores: "
            f"D {scores['directness']}/5 | "
            f"S {scores['specificity']}/5 | "
            f"G {scores['grounding']}/5 | "
            f"U {scores['usefulness']}/5 | "
            f"W {scores['warmth']}/5 | "
            f"X {scores['distinctiveness']}/5 | "
            f"O {scores['overall']}/5"
        )
        print(f"   Summary: {evaluation['summary']}")
        if evaluation.get("strengths"):
            print(f"   Strengths: {'; '.join(evaluation['strengths'][:2])}")
        if evaluation.get("weaknesses"):
            print(f"   Weaknesses: {'; '.join(evaluation['weaknesses'][:2])}")
        print()

    print("-" * 80)
    print("AVERAGES")
    for key, values in aggregate.items():
        print(f"  {key.capitalize():14s} {statistics.mean(values):.2f}/5")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Ask Mirror Talk answers with a curated audit set.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of the Ask Mirror Talk API")
    parser.add_argument("--question", action="append", dest="questions", help="Question to evaluate (repeatable)")
    parser.add_argument("--timeout", type=float, default=90.0, help="HTTP timeout in seconds")
    parser.add_argument("--eval-model", default="gpt-4.1-mini", help="OpenAI model to use for grading")
    parser.add_argument("--no-eval", action="store_true", help="Capture answers only; do not score them")
    parser.add_argument("--mode", choices=["api", "local"], default="local", help="Use live API or local service evaluation path")
    parser.add_argument("--uncached", action="store_true", help="Append a unique audit marker so questions bypass cache")
    parser.add_argument("--audit-seed", help="Stable seed to reuse for uncached question variants")
    args = parser.parse_args()

    questions = args.questions or DEFAULT_QUESTIONS
    if args.uncached:
        questions = make_uncached_questions(questions, seed=args.audit_seed)
    samples: list[AnswerSample] = []

    source_label = args.base_url if args.mode == "api" else "local service"
    print(f"Fetching {len(questions)} answers from {source_label} ...")
    for question in questions:
        if args.mode == "api":
            samples.append(fetch_answer(args.base_url, question, timeout_s=args.timeout))
        else:
            samples.append(fetch_answer_local(question))

    if args.no_eval:
        print_capture_report(samples)
        return

    evaluations = evaluate_with_openai(samples, model=args.eval_model)
    print_eval_report(samples, evaluations)


if __name__ == "__main__":
    main()
