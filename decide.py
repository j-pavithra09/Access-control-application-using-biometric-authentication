# decide.py
REGISTER = {
    "riya": {"enrolled": True, "suspended": False},
    "arjun": {"enrolled": True, "suspended": True},
}

def decide(person_id, score):
    rec = REGISTER.get(person_id)
    if rec is None:
        return "REVIEW", "Person not in register"
    if rec["suspended"]:
        return "DENY", "Suspended in register"
    if not rec["enrolled"]:
        return "DENY", "Not enrolled"
    if score >= 90:
        return "ALLOW", "Face match above threshold"
    if score >= 70:
        return "REVIEW", "Borderline face match"
    return "DENY", "Face match too low"