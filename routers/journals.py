from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Set
from uuid import UUID, uuid5, NAMESPACE_URL
from urllib.parse import urlparse

import numpy as np
import requests
from exa_py import Exa
from sqlalchemy import or_, func

from core.config import settings
from core.deps import get_current_user
from database import get_db
from models.domain import User, Journal, SavedJournal
from schemas.domain import (
    JournalResponse,
    JournalSearchBundle,
    JournalSearchItem,
    SavedJournalResponse,
)

def get_embeddings(text: str) -> list[float]:
    api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
    headers = {}
    if settings.HUGGINGFACE_API_KEY:
        headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_API_KEY}"
    
    response = requests.post(api_url, headers=headers, json={"inputs": text}, timeout=15)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], float):
            return data
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            return data[0]
        return data
    else:
        raise ValueError(f"HF API Error: {response.status_code} - {response.text}")

def _journal_has_embedding(j: Journal) -> bool:
    if j.embedding is None:
        return False
    arr = np.asarray(j.embedding, dtype=np.float64)
    return arr.size > 0


def _scopus_indexed_clause():
    """Only journals explicitly marked Scopus-indexed in our corpus."""
    return func.coalesce(func.array_to_string(Journal.index_types, " "), "").ilike("%scopus%")


router = APIRouter()


@router.get("/search", response_model=JournalSearchBundle)
def search_journals_diverse(
    db: Session = Depends(get_db),
    search: str = Query(..., min_length=1),
    free_only: bool = Query(False),
):
    """
    Top 3 Scopus-indexed journals from the corpus plus up to 3 official Scopus.com /sources pages (Exa).
    """
    search = search.strip()
    if not search:
        return JournalSearchBundle(rag=[], exa=[], exa_key_configured=bool(settings.EXA_API_KEY))
    rag_rows = _rag_top_k(db, search, free_only, k=3)
    rag = [_journal_to_rag_item(j) for j in rag_rows]
    exclude: Set[str] = {u for u in (j.submission_url for j in rag_rows) if u}
    exa = _exa_scopus_directory_items(search, exclude, k=3)
    return JournalSearchBundle(
        rag=rag,
        exa=exa,
        exa_key_configured=bool(settings.EXA_API_KEY),
    )


@router.get("/", response_model=List[JournalResponse])
def get_journals(db: Session = Depends(get_db), search: str = Query(None), free_only: bool = Query(False)):
    query = db.query(Journal).filter(_scopus_indexed_clause())

    # Apply free filter if requested
    if free_only:
        query = query.filter(Journal.is_free == True)
        
    all_journals = query.all()
    
    search = (search or "").strip()
    if not search:
        return all_journals

    # Semantic Search Logic
    try:
        query_embedding = get_embeddings(search) # Use HF API Instead of CPU/PyTorch
        
        # Using pgvector distance function for high performance if possible
        # However, since the dataset is small (~30 journals) and to avoid complex 
        # pgvector-specific SQLAlchemy queries without full setup, we continue 
        # with a clean in-memory sort or use the vector attribute.
        
        scored_journals = []
        for j in all_journals:
            if not _journal_has_embedding(j):
                score = 0.0
            else:
                # Cosine similarity (dot product of normalized vectors)
                journal_vec = np.asarray(j.embedding, dtype=np.float64)
                qe = np.asarray(query_embedding, dtype=np.float64)
                denom = np.linalg.norm(qe) * np.linalg.norm(journal_vec)
                score = float(np.dot(qe, journal_vec) / denom) if denom > 0 else 0.0
            
            scored_journals.append((j, float(score)))
            
        # Sort by similarity score descending
        scored_journals.sort(key=lambda x: x[1], reverse=True)
        
        # Lowered threshold because MiniLM short queries have lower raw scores
        # Also return top matches regardless of threshold if they are the clear leaders
        results = [j for j, s in scored_journals if s > 0.05]
        
        # If no semantic results, fallback to basic search
        if not results:
            return _keyword_search_journals(query, search)
            
        return results

    except Exception as e:
        print(f"Semantic search error: {e}")
        return _keyword_search_journals(query, search)


def _keyword_search_journals(query, search: str):
    """Match name, domain, or any topic substring (partial words, case-insensitive)."""
    words = [w for w in search.strip().split() if w]
    if not words:
        return query.all()
    search_filters = []
    for word in words:
        f_word = f"%{word}%"
        topics_flat = func.coalesce(
            func.array_to_string(Journal.topics, " "),
            "",
        )
        search_filters.extend(
            [
                Journal.name.ilike(f_word),
                Journal.domain.ilike(f_word),
                topics_flat.ilike(f_word),
            ]
        )
    return query.filter(or_(*search_filters)).all()


def _journal_to_rag_item(j: Journal) -> JournalSearchItem:
    return JournalSearchItem(
        id=j.id,
        name=j.name,
        publisher=j.publisher,
        domain=j.domain,
        index_types=j.index_types or [],
        quartile=j.quartile,
        speed=j.speed,
        avg_weeks=j.avg_weeks,
        is_free=j.is_free,
        cost_note=j.cost_note,
        submission_url=j.submission_url,
        topics=j.topics or [],
        impact_factor=j.impact_factor,
        source="rag",
        snippet=None,
    )


def _rag_top_k(db: Session, search: str, free_only: bool, k: int = 3) -> List[Journal]:
    q = db.query(Journal).filter(_scopus_indexed_clause())
    if free_only:
        q = q.filter(Journal.is_free == True)
    all_journals = q.all()
    if not all_journals:
        return []
    try:
        query_embedding = get_embeddings(search)
        scored: List[tuple[Journal, float]] = []
        for j in all_journals:
            if not _journal_has_embedding(j):
                score = 0.0
            else:
                journal_vec = np.asarray(j.embedding, dtype=np.float64)
                qe = np.asarray(query_embedding, dtype=np.float64)
                denom = np.linalg.norm(qe) * np.linalg.norm(journal_vec)
                score = float(np.dot(qe, journal_vec) / denom) if denom > 0 else 0.0
            scored.append((j, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        if any(s > 1e-9 for _, s in scored):
            return [j for j, _ in scored[:k]]
    except Exception as e:
        print(f"RAG semantic ranking error: {e}")
    kw = _keyword_search_journals(q, search)
    return kw[:k]


def _scopus_url_quality(url: str) -> int:
    """
    Score URLs for ranking. Prefer actual journal homepages (Elsevier, Springer, Wiley, MDPI, etc.).
    """
    try:
        low = (url or "").lower()
        if ".pdf" in low:
            return -1
        p = urlparse(url)
        net = (p.netloc or "").lower()
        
        # We want journal homepages, not login pages
        if any(x in low for x in ("/login", "/signin", "/oauth", "/auth", "/register")):
            return -1
            
        quality = 40
        
        # Boost recognized publishers
        if any(pub in net for pub in ["sciencedirect.com", "elsevier.com", "springer.com", "nature.com", "wiley.com", "ieee.org", "tandfonline.com", "frontiersin.org", "mdpi.com"]):
            quality += 40
            
        if "journal" in low or "jrn" in low:
            quality += 20
            
        # Penalize scopus sources since that's what the user explicitly doesn't want
        if "scopus.com" in net:
            quality -= 50
            
        return quality
    except Exception:
        return -1


def _topic_tags_from_query(q: str) -> List[str]:
    words = [w.strip() for w in q.replace(",", " ").split() if len(w.strip()) > 2]
    return words[:3] or ["Scopus", "Indexed", "Official"]


def _exa_search_scopus_sources(query: str, num_results: int):
    """Multiple query/domain strategies — strict /sources-only filtering was yielding zero hits from Exa's index."""
    if not settings.EXA_API_KEY:
        return []
    client = Exa(settings.EXA_API_KEY)
    contents = {"text": {"max_characters": 1500}}
    attempts: List[tuple[str, dict]] = [
        (
            f"{query} official journal homepage Scopus-indexed",
            {"num_results": num_results, "contents": contents},
        ),
        (
            f"{query} submit manuscript journal scopus",
            {"num_results": num_results, "contents": contents},
        ),
        (
            f"{query} elsevier springer wiley journal home",
            {"num_results": num_results, "contents": contents},
        ),
    ]
    seen_urls: Set[str] = set()
    merged: List = []
    for q, kwargs in attempts:
        try:
            resp = client.search(q, **kwargs)
            for r in resp.results:
                url = (getattr(r, "url", None) or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                merged.append(r)

            if len(merged) >= num_results:
                break
        except Exception as e:
            print(f"Exa search error ({q[:48]}…): {e}")
    return merged


def _exa_scopus_directory_items(
    query: str,
    exclude_urls: Set[str],
    k: int = 3,
) -> List[JournalSearchItem]:
    raw = _exa_search_scopus_sources(query, num_results=max(k * 10, 30))
    ranked: List[tuple[float, object]] = []
    for r in raw:
        url = (getattr(r, "url", None) or "").strip()
        if not url or url in exclude_urls:
            continue
        qual = _scopus_url_quality(url)
        if qual < 0:
            continue
        exa = float(getattr(r, "score", None) or 0.0)
        ranked.append((qual * 1000.0 + exa, r))
    ranked.sort(key=lambda x: x[0], reverse=True)

    def _append_from_result(r: object, added: Set[str]) -> bool:
        if len(items) >= k:
            return False
        url = (getattr(r, "url", None) or "").strip()
        if not url or url in exclude_urls or url in added:
            return False
        title = (getattr(r, "title", None) or "Scopus source").strip()[:220]
        text = getattr(r, "text", None) or ""
        content = (text or "").strip()[:800]
        hid = uuid5(NAMESPACE_URL, url)
        items.append(
            JournalSearchItem(
                id=hid,
                name=title,
                publisher="Elsevier · Scopus",
                domain="Scopus · Source listing",
                index_types=["Scopus"],
                quartile="—",
                speed="—",
                avg_weeks=0,
                is_free=True,
                cost_note="Official Scopus Source page — confirm metrics on site.",
                submission_url=url,
                topics=_topic_tags_from_query(query),
                impact_factor="—",
                source="exa",
                snippet=content or None,
            )
        )
        added.add(url)
        exclude_urls.add(url)
        return True

    items: List[JournalSearchItem] = []
    added_urls: Set[str] = set()
    for _, r in ranked:
        if len(items) >= k:
            break
        url = (getattr(r, "url", None) or "").strip()
        if _scopus_url_quality(url) < 20:
            continue
        _append_from_result(r, added_urls)

    if len(items) < k:
        for _, r in ranked:
            if len(items) >= k:
                break
            url = (getattr(r, "url", None) or "").strip()
            if url in added_urls or not url:
                continue
            if _scopus_url_quality(url) < 0:
                continue
            _append_from_result(r, added_urls)

    return items


@router.get("/saved", response_model=List[SavedJournalResponse])
def get_saved_journals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SavedJournal).filter(SavedJournal.user_id == current_user.id).all()

@router.post("/{journal_id}/save")
def save_journal(journal_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(SavedJournal).filter(
        SavedJournal.user_id == current_user.id,
        SavedJournal.journal_id == journal_id
    ).first()
    
    if not existing:
        saved = SavedJournal(user_id=current_user.id, journal_id=journal_id)
        db.add(saved)
        db.commit()
    return {"message": "Journal saved"}

@router.delete("/{journal_id}/save")
def unsave_journal(journal_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(SavedJournal).filter(
        SavedJournal.user_id == current_user.id,
        SavedJournal.journal_id == journal_id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
    return {"message": "Journal unsaved"}
