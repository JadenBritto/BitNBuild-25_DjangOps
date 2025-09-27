# ml/ml_module.py
"""
Review Radar - ML module
Provides:
 - load_model() automatically (local checkpoint fallback -> HF pretrained)
 - analyze_reviews(reviews, ...) -> rich JSON
 - compare_reviews(reviews_a, reviews_b) -> comparative JSON
 - export_to_csv(result, path)
"""

import os
os.environ.setdefault("WANDB_DISABLED", "true")

from typing import List, Dict, Any
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import re, math, csv, json

# -------- Config --------
MODEL_DIR = "./reviewradar-final"   # backend: place fine-tuned model here if available
FALLBACK_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

# Aspect keywords (extendable)
ASPECT_KEYWORDS = {
    "battery": ["battery", "charge", "charging", "power", "duration"],
    "screen": ["screen", "display", "glass", "touch", "resolution", "crack", "cracked"],
    "camera": ["camera", "photo", "selfie", "lens", "pixel"],
    "sound": ["sound", "speaker", "audio", "volume", "bass"],
    "delivery": ["delivery", "packaging", "shipping", "arrived", "late"]
}

# -------- Model load (fallback) --------
def load_pipeline(model_path: str = MODEL_DIR):
    try:
        p = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path, device=-1)
        print("Loaded local fine-tuned model from", model_path)
    except Exception:
        p = pipeline("sentiment-analysis", model=FALLBACK_MODEL, device=-1)
        print("Using pretrained sentiment model:", FALLBACK_MODEL)
    return p

clf = load_pipeline()

# -------- Helpers --------
def top_keywords(reviews: List[str], k: int = 6) -> List[str]:
    if not reviews:
        return []
    vec = TfidfVectorizer(stop_words="english", max_features=200)
    X = vec.fit_transform(reviews)
    sums = X.sum(axis=0).A1
    terms = vec.get_feature_names_out()
    idx = sums.argsort()[::-1][:k]
    return [terms[i] for i in idx]

def map_aspects(reviews: List[str]) -> Dict[str,int]:
    counts = {a: 0 for a in ASPECT_KEYWORDS}
    for r in reviews:
        t = r.lower()
        for a, kws in ASPECT_KEYWORDS.items():
            for kw in kws:
                if kw in t:
                    counts[a] += 1
                    break
    return counts

def extractive_summary(reviews: List[str], n_sentences: int = 3) -> str:
    if not reviews:
        return ""
    text = " ".join(reviews)
    sentences = re.split(r'(?<=[.!?]) +', text)
    if len(sentences) <= n_sentences:
        return " ".join(sentences)
    vect = CountVectorizer(stop_words="english").fit([text])
    word_counts = vect.transform([text]).toarray().ravel()
    vocab = vect.get_feature_names_out()
    word_score = dict(zip(vocab, word_counts))
    def sentence_score(s):
        tokens = re.findall(r'\w+', s.lower())
        if not tokens: 
            return 0.0
        return sum(word_score.get(t,0) for t in tokens) / math.sqrt(len(tokens))
    scored = [(sentence_score(s), s) for s in sentences]
    best = sorted(scored, key=lambda x: x[0], reverse=True)[:n_sentences]
    return " ".join(s for _, s in best)

# Lightweight heuristic AI-score (fast, CPU safe)
def heuristic_ai_score(text: str) -> float:
    s = 0.0
    tokens = text.split()
    if len(tokens) < 5: s += 0.35
    if len(tokens) > 200: s += 0.3
    if text.isupper(): s += 0.2
    if text.count("!") > 3: s += 0.1
    return min(1.0, s)

# -------- Main analysis function --------
def analyze_reviews(reviews: List[str],
                    n_keywords: int = 6,
                    summary_sentences: int = 3,
                    flag_threshold: float = 0.8) -> Dict[str,Any]:
    # sanitize
    clean = [r.strip() for r in reviews if r and r.strip()]
    if not clean:
        return {"error":"no reviews provided", "meta": {"n_reviews": 0}}

    # sentiment (batched)
    results = clf(clean)
    labels = [r["label"] for r in results]
    scores = [float(r.get("score", 0.0)) for r in results]

    # ai score + flags
    ai_scores = [heuristic_ai_score(r) for r in clean]
    flags = [s >= flag_threshold for s in ai_scores]

    # per-review structure
    per_review = [
        {"text": text, "label": lab, "score": scr, "ai_score": ai, "flag": fl}
        for text, lab, scr, ai, fl in zip(clean, labels, scores, ai_scores, flags)
    ]

    # keywords / aspects
    top_kw = top_keywords(clean, k=n_keywords)
    pos_reviews = [t for t,l in zip(clean,labels) if l.upper().startswith("POS")]
    neg_reviews = [t for t,l in zip(clean,labels) if l.upper().startswith("NEG")]
    pos_kw = top_keywords(pos_reviews, k=n_keywords) if pos_reviews else []
    neg_kw = top_keywords(neg_reviews, k=n_keywords) if neg_reviews else []

    aspects_counts = map_aspects(clean)
    aspect_stats = {}
    for asp, mentions in aspects_counts.items():
        pos = sum(1 for t,l in zip(clean, labels) if asp in t.lower() and l.upper().startswith("POS"))
        neg = sum(1 for t,l in zip(clean, labels) if asp in t.lower() and l.upper().startswith("NEG"))
        pos_pct = round(pos / mentions, 3) if mentions>0 else 0.0
        neg_pct = round(neg / mentions, 3) if mentions>0 else 0.0
        aspect_stats[asp] = {"mentions": mentions, "pos": pos, "neg": neg, "pos_pct": pos_pct, "neg_pct": neg_pct}

    # recommendations (template rules)
    recommendations = []
    for asp, stats in aspect_stats.items():
        if stats["mentions"] >= 5 and stats["neg_pct"] >= 0.35:
            recommendations.append({
                "aspect": asp,
                "reason": f"neg_pct={stats['neg_pct']}",
                "action": f"High negative mentions for {asp}. Investigate supply/packaging or add clearer product notes/warranty."
            })

    # summaries: all + excluding flagged
    summary_all = extractive_summary(clean, n_sentences=summary_sentences)
    unflagged = [t for t,f in zip(clean, flags) if not f]
    summary_excl_flagged = extractive_summary(unflagged, n_sentences=summary_sentences)

    # aggregates
    sentiment_counts = {}
    for lab in labels:
        sentiment_counts[lab] = sentiment_counts.get(lab,0) + 1

    meta = {"n_reviews": len(clean), "n_flagged": sum(flags)}

    return {
        "meta": meta,
        "sentiment_counts": sentiment_counts,
        "top_keywords": top_kw,
        "positive_keywords": pos_kw,
        "negative_keywords": neg_kw,
        "aspect_stats": aspect_stats,
        "recommendations": recommendations,
        "summary_all": summary_all,
        "summary_excluding_flagged": summary_excl_flagged,
        "reviews": per_review
    }

# -------- Compare function --------
def compare_reviews(reviews_a: List[str], reviews_b: List[str], n_keywords: int = 6) -> Dict[str,Any]:
    a = analyze_reviews(reviews_a, n_keywords=n_keywords)
    b = analyze_reviews(reviews_b, n_keywords=n_keywords)
    # per-aspect delta of pos_pct
    deltas = {}
    for asp in set(list(a["aspect_stats"].keys()) + list(b["aspect_stats"].keys())):
        ap = a["aspect_stats"].get(asp, {}).get("pos_pct", 0.0)
        bp = b["aspect_stats"].get(asp, {}).get("pos_pct", 0.0)
        deltas[asp] = round(ap - bp, 3)
    # verdict: top 3 aspects by absolute delta
    sorted_asps = sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    verdict = "; ".join([f"{asp}: delta {d:+.3f}" for asp,d in sorted_asps])
    return {"a": a, "b": b, "deltas": deltas, "verdict": verdict}

# -------- Export helper --------
def export_to_csv(result: Dict[str,Any], out_path: str = "export_reviews.csv") -> str:
    reviews = result.get("reviews", [])
    if not reviews:
        with open(out_path, "w") as f:
            f.write("No reviews\n")
        return out_path
    keys = ["text","label","score","ai_score","flag"]
    with open(out_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(keys)
        for r in reviews:
            writer.writerow([r.get(k,"") for k in keys])
    return out_path

# -------- Save example JSON (for frontend) --------
def save_example_json(result: Dict[str,Any], filename: str = "example_output.json") -> str:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return filename
