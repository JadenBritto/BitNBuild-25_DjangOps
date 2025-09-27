# web/streamlit_app.py
import streamlit as st, requests, json, pandas as pd
API = "http://127.0.0.1:8000"

st.title("Review Radar - Demo")

mode = st.radio("Input", ["Paste reviews", "Demo Good", "Demo Bad"])
if mode == "Paste reviews":
    txt = st.text_area("Paste reviews (one per line)")
    reviews = [l.strip() for l in txt.splitlines() if l.strip()]
elif mode == "Demo Good":
    with open("../data/example_good.json") as f: 
        example = json.load(f)
    reviews = [r["text"] for r in example["reviews"]]
elif mode == "Demo Bad":
    with open("../data/example_bad.json") as f:
        example = json.load(f)
    reviews = [r["text"] for r in example["reviews"]]

if st.button("Analyze"):
    with st.spinner("Analyzing..."):
        r = requests.post(API + "/analyze", json={"reviews": reviews}).json()
    st.subheader("Summary (All reviews)")
    st.write(r.get("summary_all") or r.get("summary"))
    st.subheader("Summary (Excluding flagged)")
    st.write(r.get("summary_excluding_flagged"))
    st.subheader("Sentiment counts")
    st.write(r.get("sentiment_counts"))
    st.subheader("Top keywords")
    st.write(r.get("top_keywords"))
    st.subheader("Aspect stats")
    st.write(pd.DataFrame(r.get("aspect_stats")).T)
    st.subheader("Recommendations")
    for rec in r.get("recommendations", []):
        st.info(rec["action"])
    st.subheader("Per-review (first 20)")
    df = pd.DataFrame(r["reviews"])[:20]
    st.dataframe(df)
