from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from bson import ObjectId
from bson.errors import InvalidId

from app.config import CORS_ORIGINS
from app.db import ensure_indexes, reviews_collection
from app.github_client import GitHubRateLimitError, PRNotFoundError, fetch_pr, parse_pr_url
from app.models import PRMetadata, ReviewDetail, ReviewSummary, StaticAnalysisResult
from app.static_analysis import run_static_analysis
from app.streaming import stream_review


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await ensure_indexes()
    except Exception as exc:
        print(f"MongoDB unavailable at startup, persistence disabled: {exc}")
    yield


app = FastAPI(title="ReviewBot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/pr", response_model=PRMetadata)
async def get_pr(pr_url: str):
    try:
        owner, repo, number = parse_pr_url(pr_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return await fetch_pr(owner, repo, number)
    except PRNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GitHubRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.get("/api/static-analysis", response_model=StaticAnalysisResult)
async def get_static_analysis(pr_url: str):
    try:
        owner, repo, number = parse_pr_url(pr_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        pr = await fetch_pr(owner, repo, number)
    except PRNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GitHubRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    return await run_static_analysis(pr)


@app.get("/api/review/stream")
async def review_stream(pr_url: str):
    try:
        parse_pr_url(pr_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        stream_review(pr_url),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


REVIEW_SUMMARY_PROJECTION = {
    "_id": 1,
    "pr_url": 1,
    "repo_owner": 1,
    "repo_name": 1,
    "pr_number": 1,
    "pr_title": 1,
    "overall_score": 1,
    "dimension_scores": 1,
    "created_at": 1,
}


def _with_id(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/api/reviews", response_model=list[ReviewSummary])
async def list_reviews(repo_owner: str | None = None, repo_name: str | None = None, limit: int = 20):
    query = {}
    if repo_owner:
        query["repo_owner"] = repo_owner
    if repo_name:
        query["repo_name"] = repo_name

    cursor = (
        reviews_collection.find(query, REVIEW_SUMMARY_PROJECTION)
        .sort("created_at", -1)
        .limit(limit)
    )
    return [_with_id(doc) async for doc in cursor]


@app.get("/api/repo/{owner}/{name}/trend", response_model=list[ReviewSummary])
async def repo_trend(owner: str, name: str):
    cursor = reviews_collection.find(
        {"repo_owner": owner, "repo_name": name}, REVIEW_SUMMARY_PROJECTION
    ).sort("created_at", 1)
    return [_with_id(doc) async for doc in cursor]


@app.get("/api/reviews/{review_id}", response_model=ReviewDetail)
async def get_review(review_id: str):
    try:
        object_id = ObjectId(review_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid review id") from exc

    doc = await reviews_collection.find_one({"_id": object_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Review not found")

    return _with_id(doc)
