# api/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from ml.ml_module import analyze_reviews, compare_reviews, export_to_csv

app = FastAPI()

class RevIn(BaseModel):
    reviews: List[str]

class CompareIn(BaseModel):
    a: List[str]
    b: List[str]

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/analyze")
def analyze(in_data: RevIn):
    return analyze_reviews(in_data.reviews)

@app.post("/compare")
def compare(in_data: CompareIn):
    return compare_reviews(in_data.a, in_data.b)

@app.post("/export")
def export(in_data: RevIn):
    res = analyze_reviews(in_data.reviews)
    path = export_to_csv(res, out_path="exported_reviews.csv")
    return {"path": path}
