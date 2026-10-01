from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class AIService:

    def __init__(self):

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = (
            "openai/gpt-oss-120b"
        )

    def analyze(
        self,
        detection_result: dict[str, Any],
    ) -> dict[str, Any]:

        risk_score = detection_result.get(
            "risk_score",
            0,
        )

        risk_level = detection_result.get(
            "risk_level",
            "LOW",
        )

        money_at_risk = detection_result.get(
            "money_at_risk",
            detection_result.get(
                "total_money_at_risk",
                0,
            ),
        )

        findings = detection_result.get(
            "findings",
            [],
        )

        risk_breakdown = detection_result.get(
            "risk_breakdown",
            {},
        )

        metrics = detection_result.get(
            "metrics",
            {},
        )

        engine_version = detection_result.get(
            "engine_version",
            "unknown",
        )

        legacy_risk = detection_result.get(
            "risk",
            {},
        )

        if isinstance(
            legacy_risk,
            dict,
        ):

            if not risk_score:

                risk_score = legacy_risk.get(
                    "score",
                    legacy_risk.get(
                        "risk_score",
                        0,
                    ),
                )

            if (
                not risk_level
                or risk_level == "LOW"
            ):

                risk_level = legacy_risk.get(
                    "level",
                    legacy_risk.get(
                        "risk_level",
                        risk_level,
                    ),
                )

        sorted_findings = sorted(
            findings,
            key=lambda finding: (
                0
                if str(
                    finding.get(
                        "severity",
                        "",
                    )
                ).lower() == "high"
                else 1
                if str(
                    finding.get(
                        "severity",
                        "",
                    )
                ).lower() == "medium"
                else 2
            ),
        )

        important_findings = []

        for finding in sorted_findings[:20]:

            important_findings.append(
                {
                    "transaction_id": finding.get(
                        "transaction_id"
                    ),
                    "type": finding.get(
                        "type"
                    ),
                    "severity": finding.get(
                        "severity"
                    ),
                    "title": finding.get(
                        "title"
                    ),
                    "message": finding.get(
                        "message"
                    ),
                    "amount_at_risk": finding.get(
                        "amount_at_risk",
                        0,
                    ),
                    "confidence": finding.get(
                        "confidence"
                    ),
                    "decision_rule": finding.get(
                        "decision_rule"
                    ),
                }
            )

        analysis_data = {
            "engine_version": engine_version,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "money_at_risk": money_at_risk,
            "risk_breakdown": risk_breakdown,
            "findings": important_findings,
            "metrics": {
                "rows_analyzed": metrics.get(
                    "rows_analyzed"
                ),
                "architecture": metrics.get(
                    "architecture"
                ),
                "baseline_trust": metrics.get(
                    "baseline_trust"
                ),
            },
        }

        prompt = f"""
You are an expert financial risk analyst.

You are analyzing financial transaction data
for a company using FinGuard.

FinGuard has already performed deterministic
and statistical risk detection.

Your role is NOT to detect new transactions.

Your role is to:
1. Explain the risks already detected.
2. Summarize their business impact.
3. Prioritize the most important findings.
4. Recommend concrete actions.
5. Remain strictly grounded in the detector output.

Here is the FinGuard detection engine output:

{json.dumps(
    analysis_data,
    indent=2,
    ensure_ascii=False,
    default=str,
)}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "executive_summary": "Short explanation of the overall financial risk.",
    "overall_assessment": {{
        "risk_level": "LOW | MEDIUM | HIGH",
        "risk_score": 0,
        "money_at_risk": 0,
        "explanation": "Why this risk level was assigned."
    }},
    "top_leaks": [
        {{
            "transaction_id": "Transaction ID if available",
            "type": "Finding type",
            "severity": "LOW | MEDIUM | HIGH",
            "title": "Short title",
            "explanation": "What FinGuard detected and why it matters.",
            "financial_impact": "Potential financial impact based only on provided information.",
            "recommended_action": "Concrete action the company should take.",
            "priority": "LOW | MEDIUM | HIGH"
        }}
    ],
    "recommendations": [
        "Actionable recommendation"
    ]
}}

Rules:
1. Never invent transactions.
2. Never invent amounts.
3. Never invent evidence.
4. Use only information present in the detector output.
5. Do not override FinGuard's risk score.
6. Do not override FinGuard's risk level.
7. Do not classify a transaction as suspicious unless it exists in findings.
8. Be conservative in financial interpretation.
9. Prioritize high-severity findings.
10. Mention transaction IDs when available.
11. Recommendations must be actionable.
12. Return valid JSON only.
13. Do not use Markdown.
14. Do not add text outside the JSON.
"""

        content = None

        try:

            response = (
                self.client
                .chat
                .completions
                .create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a senior "
                                "financial risk analyst. "
                                "You explain FinGuard "
                                "detector results without "
                                "inventing evidence."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.1,
                )
            )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            if content is None:

                raise ValueError(
                    "AI returned an empty response."
                )

            content = content.strip()

            if content.startswith(
                "```json"
            ):
                content = content[
                    len("```json"):
                ]
            elif content.startswith(
                "```"
            ):
                content = content[
                    len("```"):
                ]

            if content.endswith(
                "```"
            ):
                content = content[
                    :-3
                ]

            content = content.strip()

            result = json.loads(
                content
            )

            return {
                "success": True,
                "model": self.model,
                "analysis": result,
            }

        except json.JSONDecodeError as error:

            return {
                "success": False,
                "model": self.model,
                "error": (
                    "AI returned invalid JSON"
                ),
                "details": str(error),
                "raw_response": content,
            }

        except Exception as error:

            return {
                "success": False,
                "model": self.model,
                "error": str(error),
            }


ai_service = AIService()


def analyze(
    detection_result: dict[str, Any],
) -> dict[str, Any]:

    return ai_service.analyze(
        detection_result
    )
