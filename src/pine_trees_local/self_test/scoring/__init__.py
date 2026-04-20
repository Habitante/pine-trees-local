"""Scoring pipeline for self-test runs.

Assembles blinded judge prompts, dispatches them to GPT and Gemini,
collects 0-4 scores, computes Cohen's weighted kappa, and plots the
results. See ``self-test/SCORING_BUILD_SPEC.md`` for the full spec.
"""
