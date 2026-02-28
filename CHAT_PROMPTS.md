# CHAT_PROMPTS.md

## Chat System Prompt Strategy

Chat mode reuses the same retriever/vector store as assessment mode.

Prompt objectives:

1. Maintain multi-turn coherence using recent session context.
2. Keep answers grounded only in retrieved NG12 chunks.
3. Encourage graceful fallback when evidence is weak.

### Core Prompt

- Role: NG12 guideline assistant.
- Rules:
  - Answer naturally but only from retrieved evidence.
  - Never invent referral thresholds.
  - If evidence does not support an answer, clearly state uncertainty.

### Grounding Behavior

- Retrieved passages are injected as explicit evidence block.
- The same Chroma collection used by `/assess` is reused for `/chat`; chat never rebuilds the index per request.
- Recent conversation turns are included in the retrieval query and answer prompt to support follow-up questions.
- Safety validator checks claim-level support and may force `abstain`.
- If the safety validator abstains, the assistant response is replaced with a safer fallback message.
- Citations are returned for all pathway claims.
