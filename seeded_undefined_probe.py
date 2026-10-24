"""NEGATIVE CONTROL for the F821 gate (H7243, 24-10-2026).

Scratch branch only: references a name that is never defined, so
`ruff check --select F821` must report it and the F821 workflow must go red.
Delete with the scratch branch.
"""


def probe():
    return intentionally_undefined_gate_probe
