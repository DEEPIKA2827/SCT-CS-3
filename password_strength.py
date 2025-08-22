#!/usr/bin/env python3
import argparse
import math
import re
from typing import Dict, List

COMMON_WORDS = {
    "password", "admin", "welcome", "qwerty", "iloveyou", "letmein",
    "login", "user", "test", "secret", "dragon", "football", "monkey",
}
LEET_MAP = str.maketrans({"@":"a","$":"s","!":"i","1":"l","0":"o","3":"e","5":"s","7":"t"})

SEQUENCES = [
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "0123456789",
    "qwertyuiopasdfghjklzxcvbnm",
]

def _has_lower(p): return any(c.islower() for c in p)
def _has_upper(p): return any(c.isupper() for c in p)
def _has_digit(p): return any(c.isdigit() for c in p)
def _has_symbol(p): return any(not c.isalnum() for c in p)

def _char_pool_size(p: str) -> int:
    pool = 0
    if _has_lower(p): pool += 26
    if _has_upper(p): pool += 26
    if _has_digit(p): pool += 10
    if _has_symbol(p): pool += 33  # printable symbols rough count
    return max(pool, 1)

def _find_sequences(p: str) -> int:
    """Return number of distinct sequential patterns found (forward/backward, length>=3)."""
    count = 0
    lower = p.lower()
    for seq in SEQUENCES:
        for i in range(len(seq)-2):
            chunk = seq[i:i+3]
            if chunk in lower:
                count += 1
            if chunk[::-1] in lower:
                count += 1
    return count

def _repetition_penalty(p: str) -> int:
    """Return a penalty count for repeated runs or repeated n-grams."""
    penalties = 0
    # runs like aaaa
    if re.search(r"(.)\1{2,}", p):  # three or more of same char
        penalties += 1
    # repeated bigrams like abab
    if re.search(r"(..)\1{1,}", p):
        penalties += 1
    # repeated trigrams like abcabc
    if re.search(r"(...)\1{1,}", p):
        penalties += 1
    return penalties

def _dictionary_hits(p: str) -> int:
    """Count dictionary matches (plain or leetspeak-normalized)."""
    hits = 0
    plain = p.lower()
    norm = plain.translate(LEET_MAP)
    for w in COMMON_WORDS:
        if w in plain or w in norm:
            hits += 1
    return hits

def estimate_entropy_bits(p: str) -> float:
    pool = _char_pool_size(p)
    return len(p) * math.log2(pool)

def crack_time_estimates(bits: float, guesses_per_sec: float = 1e10) -> Dict[str, str]:
    # worst-case ~ 2^(bits-1) guesses on average
    expected_guesses = 2 ** max(bits - 1, 0)
    seconds = expected_guesses / guesses_per_sec
    def humanize(s: float) -> str:
        units = [("sec", 1), ("min", 60), ("hr", 3600), ("day", 86400),
                 ("yr", 31557600), ("century", 3155760000)]
        for name, span in units:
            if s < span*60 or name == "century":
                return f"{s/span:.2f} {name}"
        return f"{s:.2f} sec"
    return {
        "offline_fast": humanize(seconds),           # GPU/offline 1e10/s
        "online_slow": humanize(expected_guesses / 100),  # rate-limited ~100/s
    }

def score_password(p: str) -> Dict:
    if not p:
        return {
            "score": 0, "label": "Very Weak", "bits": 0.0,
            "feedback": ["Password is empty."], "estimates": crack_time_estimates(0)
        }

    bits = estimate_entropy_bits(p)
    score = 0
    feedback: List[str] = []

    # length
    L = len(p)
    if L < 6: score += 0; feedback.append("Use at least 8–12 characters.")
    elif L < 8: score += 10
    elif L < 12: score += 20
    elif L < 16: score += 30
    else: score += 40

    # variety
    varieties = sum([_has_lower(p), _has_upper(p), _has_digit(p), _has_symbol(p)])
    score += [0, 10, 20, 30, 35][varieties]  # none..four kinds

    # positive bonus for bits
    score += min(int(bits / 4), 25)  # cap bonus from entropy

    # penalties
    seqs = _find_sequences(p)
    reps = _repetition_penalty(p)
    dicts = _dictionary_hits(p)
    penalty = seqs*8 + reps*8 + dicts*12

    score = max(0, min(100, score - penalty))

    if seqs: feedback.append("Avoid sequential patterns (e.g., abc, 123, qwerty).")
    if reps: feedback.append("Avoid repeated patterns like aaa or abcabc.")
    if dicts: feedback.append("Avoid common or leetspeak words (e.g., 'p@ssw0rd').")
    if not _has_upper(p): feedback.append("Add uppercase letters.")
    if not _has_lower(p): feedback.append("Add lowercase letters.")
    if not _has_digit(p): feedback.append("Add digits.")
    if not _has_symbol(p): feedback.append("Add symbols (e.g., !@#$).")

    label = (
        "Very Weak" if score < 20 else
        "Weak" if score < 40 else
        "Moderate" if score < 60 else
        "Strong" if score < 80 else
        "Excellent"
    )

    return {
        "score": score,
        "label": label,
        "bits": round(bits, 2),
        "penalty_detail": {"sequences": seqs, "repeats": reps, "dictionary_hits": dicts},
        "feedback": feedback,
        "estimates": crack_time_estimates(bits),
    }

def main():
    parser = argparse.ArgumentParser(description="Password strength assessor (CLI).")
    parser.add_argument("--password", "-p", help="Password to evaluate")
    args = parser.parse_args()

    if not args.password:
        print("Usage: python password_strength.py -p \"YourPassword123!\"")
        return

    result = score_password(args.password)
    print(f"Score: {result['score']} / 100 → {result['label']}")
    print(f"Entropy: {result['bits']} bits")
    print(f"Est. crack time (offline fast): {result['estimates']['offline_fast']}")
    print(f"Est. crack time (online slow):  {result['estimates']['online_slow']}")
    if result["feedback"]:
        print("Suggestions:")
        for tip in result["feedback"]:
            print(f"  - {tip}")

if __name__ == "__main__":
    main()
