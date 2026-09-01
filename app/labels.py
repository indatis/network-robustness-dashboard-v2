from app.config import ATTACK_LABELS, RANKING_LABELS, OUTCOME_LABELS, COMMUNITY_LABELS

def pretty_token(value):
    if value is None:
        return "—"
    return str(value).replace("_", " ").strip().title()

def pretty_attack(value):
    return ATTACK_LABELS.get(str(value), pretty_token(value))

def pretty_ranking(value):
    return RANKING_LABELS.get(str(value), pretty_token(value))

def pretty_outcome(value):
    return OUTCOME_LABELS.get(str(value), pretty_token(value))

def pretty_community(value):
    return COMMUNITY_LABELS.get(str(value), pretty_token(value))

def pretty_scale(value):
    mapping = {
        "raw": "Raw value",
        "signed_delta": "Signed change from baseline",
        "absolute_delta": "Absolute change from baseline",
        "paired_delta_auc": "Paired ΔAUC",
        "anova": "ANOVA / post-hoc",
        "raw_signed_delta": "Raw + signed change",
    }
    return mapping.get(str(value), pretty_token(value))
