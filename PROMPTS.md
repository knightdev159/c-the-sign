# PROMPTS.md

## Assessment System Prompt Strategy

System prompt goals:

1. Constrain model to retrieved NG12 evidence only.
2. Avoid fabrication of thresholds, durations, or criteria.
3. Use a function-calling step to fetch structured patient data before reasoning.
4. Produce concise, clinically neutral reasoning suitable for CDS support.

### Core Prompt

- Role: Clinical decision support assistant.
- Rules:
  - Call the patient lookup tool exactly once using the supplied `patient_id`.
  - Use only provided evidence snippets.
  - If evidence is insufficient, explicitly say so.
  - Do not infer criteria not present in evidence.
  - Return one structured recommendation: `urgent_referral`, `urgent_investigation`, `no_urgent_action`, or `insufficient_evidence`.
  - Keep reasoning concise and traceable to citations.

### Why this prompt

The assessment flow now has two explicit stages:

1. Tool selection for structured patient lookup.
2. Grounded recommendation generation over retrieved NG12 evidence.

Prompting is designed to keep both stages auditable and compatible with downstream safety validation.

## Implementation Notes

- Vertex mode uses structured function-calling for the patient lookup step and structured output for the assessment payload.
- Mock mode keeps the same two-stage contract but returns deterministic local behavior for offline development.
- Safety validation runs after model output and can still downgrade the final response to `insufficient_evidence`.
