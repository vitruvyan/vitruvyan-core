#!/usr/bin/env python3
"""
API Orthodoxy Wardens — Usage Examples

This script demonstrates how to interact with the API Orthodoxy Wardens service
for compliance evaluation, truth validation, and verdict rendering.

Prerequisites:
- API Orthodoxy Wardens service running on localhost:8002
- Or adjust BASE_URL accordingly

Run with: python examples/example_api_usage.py
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8002"

def evaluate_output(input_text: str, output_text: str, ruleset_version: str = "1.0") -> Dict[str, Any]:
    """Evaluate output text against compliance rules."""
    payload = {
        "input_text": input_text,
        "output_text": output_text,
        "ruleset_version": ruleset_version
    }

    try:
        response = requests.post(f"{BASE_URL}/judge/evaluate", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error evaluating output: {e}")
        return {}

def classify_input(input_text: str) -> Dict[str, Any]:
    """Classify input by category and severity."""
    payload = {
        "input_text": input_text
    }

    try:
        response = requests.post(f"{BASE_URL}/judge/classify", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error classifying input: {e}")
        return {}

def get_verdict_history(limit: int = 10) -> Dict[str, Any]:
    """Get recent verdict history."""
    try:
        response = requests.get(f"{BASE_URL}/judge/history?limit={limit}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting history: {e}")
        return {}

def get_rules_versions() -> Dict[str, Any]:
    """Get available ruleset versions."""
    try:
        response = requests.get(f"{BASE_URL}/rules/versions")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting rules versions: {e}")
        return {}

def confess_and_judge(input_text: str, output_text: str) -> Dict[str, Any]:
    """Submit a confession for judgment (full tribunal process)."""
    payload = {
        "input_text": input_text,
        "output_text": output_text,
        "metadata": {
            "source": "example_script",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }

    try:
        response = requests.post(f"{BASE_URL}/tribunal/confess", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error submitting confession: {e}")
        return {}

def main():
    """Run example API calls."""
    print("⚖️ API Orthodoxy Wardens — Judgment & Compliance Examples")
    print("=" * 60)

    # Example 1: Evaluate blessed output
    print("\n1. Evaluating compliant output:")
    result = evaluate_output(
        "What is the capital of France?",
        "The capital of France is Paris.",
        "1.0"
    )
    if result:
        print(f"   Verdict: {result.get('verdict', 'unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")
        evidence = result.get('evidence', [])
        print(f"   Evidence items: {len(evidence)}")

    # Example 2: Evaluate heretical output
    print("\n2. Evaluating non-compliant output (hallucination):")
    result = evaluate_output(
        "What is Apple's revenue?",
        "Apple's annual revenue is $10 trillion.",
        "1.0"
    )
    if result:
        print(f"   Verdict: {result.get('verdict', 'unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")
        if 'evidence' in result:
            evidence = result.get('evidence', [])
            print(f"   Evidence items: {len(evidence)}")

    # Example 3: Classify input
    print("\n3. Classifying input text:")
    classification = classify_input("Tell me about financial markets")
    if classification:
        print(f"   Category: {classification.get('category', 'unknown')}")
        print(f"   Severity: {classification.get('severity', 'unknown')}")
        print(f"   Urgency: {classification.get('urgency', 'unknown')}")

    # Example 4: Rules versions
    print("\n4. Available ruleset versions:")
    versions = get_rules_versions()
    if versions:
        rulesets = versions.get('versions', [])
        print(f"   Found {len(rulesets)} versions")
        for v in rulesets[:3]:  # Show first 3
            print(f"   Version {v.get('version', 'unknown')}: {v.get('description', 'no desc')}")

    # Example 5: Tribunal confession
    print("\n5. Submitting confession to tribunal:")
    confession = confess_and_judge(
        "What is the market cap of Tesla?",
        "Tesla's market capitalization is approximately $800 billion."
    )
    if confession:
        print(f"   Confession ID: {confession.get('confession_id', 'unknown')}")
        print(f"   Status: {confession.get('status', 'unknown')}")
        if 'verdict' in confession:
            verdict = confession.get('verdict', {})
            print(f"   Verdict: {verdict.get('verdict', 'pending')}")

    # Example 6: Verdict history
    print("\n6. Recent verdict history:")
    history = get_verdict_history(5)
    if history:
        verdicts = history.get('verdicts', [])
        print(f"   Found {len(verdicts)} recent verdicts")
        for i, v in enumerate(verdicts):
            print(f"   Verdict {i+1}: {v.get('verdict', 'unknown')} "
                  f"(confidence: {v.get('confidence', 0):.2f})")

    print("\n✅ Examples completed!")
    print("\n💡 Tip: Start the service with:")
    print("   cd services/api_orthodoxy_wardens && python main.py")
    print("   Or: docker compose up -d api_orthodoxy_wardens")

if __name__ == "__main__":
    main()