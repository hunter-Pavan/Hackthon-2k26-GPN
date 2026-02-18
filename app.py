from fastapi import FastAPI
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import re
import matplotlib.pyplot as plt
from textblob import TextBlob
import uuid
import os

app = FastAPI()

# -----------------------------
# INPUT MODEL
# -----------------------------

class VideoURL(BaseModel):
    url: str


# -----------------------------
# UTILITY: Extract YouTube ID
# -----------------------------

def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


# -----------------------------
# NLP RISK ANALYSIS
# -----------------------------

def analyze_risk(text):

    text_lower = text.lower()
    score = 3.0
    risky_keywords = []

    risk_dict = {
        "100x": 2.5,
        "1000%": 2.5,
        "guaranteed": 2.0,
        "moonshot": 1.8,
        "explosive": 2.0,
        "life savings": 3.0,
        "act fast": 1.5,
        "secret": 1.5,
        "insider": 1.7,
        "rich quick": 2.2,
        "leverage": 1.6,
        "fomo": 1.8
    }

    for word, points in risk_dict.items():
        if word in text_lower:
            score += points
            risky_keywords.append(word)

    # Disclaimer detection
    disclaimer_missing = True
    if "not financial advice" in text_lower:
        disclaimer_missing = False
        score -= 1.5

    # Sentiment Analysis
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment > 0.6:
        score += 1.2

    score = max(0, min(10, round(score, 1)))

    return score, risky_keywords, disclaimer_missing


# -----------------------------
# SUMMARY GENERATION
# -----------------------------

def generate_summary(text):
    sentences = text.split(".")
    summary = ". ".join(sentences[:3])
    return summary


# -----------------------------
# GRAPH GENERATION
# -----------------------------

def generate_graph(score):

    fig = plt.figure()
    plt.bar(["Risk Score"], [score])
    plt.ylim(0, 10)
    plt.title("Finfluencer Risk Score (0-10)")
    plt.ylabel("Risk Level")

    filename = f"{uuid.uuid4()}.png"
    filepath = f"static/{filename}"

    os.makedirs("static", exist_ok=True)
    plt.savefig(filepath)
    plt.close(fig)

    return filepath


# -----------------------------
# MAIN API ENDPOINT
# -----------------------------

@app.post("/analyze")
def analyze_video(data: VideoURL):

    video_id = extract_video_id(data.url)

    if not video_id:
        return {"error": "Invalid YouTube URL"}

    transcript = YouTubeTranscriptApi.get_transcript(video_id)

    full_text = " ".join([t["text"] for t in transcript])

    score, keywords, disclaimer_missing = analyze_risk(full_text)

    summary = generate_summary(full_text)

    graph_path = generate_graph(score)

    return {
        "summary": summary,
        "risk_score": score,
        "risky_keywords": keywords,
        "disclaimer_missing": disclaimer_missing,
        "graph_image": graph_path
    }

