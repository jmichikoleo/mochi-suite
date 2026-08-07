import re

def detect_complexity(text):
    triggers = [
        r"\b[A-Z]{2,}\b",  # acronyms
        r"\d+\s*=\s*",     # equations
        r"\bmodel\b|\balgorithm\b|\barchitecture\b|\boptimization\b"
    ]

    for pattern in triggers:
        if re.search(pattern, text):
            return True

    return False