import numpy as np


def weighted_epic_score(p_epic, p_medium, p_medium_thin, p_thin):
    if p_epic >= 0.99:
        return 100.0
    thin_score = 10 + (1 - p_thin) * 10
    score = p_epic * 95 + p_medium * 80 + p_medium_thin * 50 + p_thin * thin_score
    return float(np.clip(score, 0, 100))


def classify_epicness(score):
    if score >= 95:
        return (
            "🏆 En legendarisk mustasch",
            "Våra experter är mållösa. Mustaschen föreslås statligt kulturarvsskydd.",
            "assets/abbe/video/legendarisk.mp4"
        )
    elif score >= 80:
        return (
            "🔥 En episk mustasch",
            "En mustasch med styrka. Kraft. Själ.",
            "assets/abbe/video/episk.mp4"
        )
    elif score >= 60:
        return (
            "🎩 En respektabel mustasch",
            "En värdig representant för svensk mustaschkultur.",
            "assets/abbe/video/respektabel.mp4"
        )
    elif score >= 25:
        return (
            "🌱 En lovande mustasch",
            "Ett litet steg för överläppen. Ett stort steg för mänskligheten.",
            "assets/abbe/video/lovande.mp4"
        )
    else:
        return (
            "🪶 En fjunig mustasch",
            "Mustaschen existerar mest som ett teoretiskt koncept.",
            "assets/abbe/video/fjunig.mp4"
        )
