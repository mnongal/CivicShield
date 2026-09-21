# Reusable agent transport

`provider.py` has no CivicShield or database dependencies. It accepts instructions, context and an output schema. By default it calls a downloaded model through Ollama on loopback. An explicitly configured OpenAI alternative uses REST and Structured Outputs.

This module supports text interviews inside CivicShield. Call preparation and calendar export live separately in `app/call_planner.py`. See `docs/LOCAL_AI.md` for setup and current limits.
