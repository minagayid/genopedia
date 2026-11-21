"""Model adapter boundary for the future Genopedia LLM.

The web app talks to this module only. While no trained model endpoint is
configured, the API answers honestly with an explicit unavailable state instead
of fabricated output. Once the Genopedia model finishes training and passes
evaluation, point AI_MODEL_BASE_URL at any OpenAI-compatible server (local
vLLM/Ollama or a hosted endpoint) and set AI_MODEL_STATE=available.
"""

from __future__ import annotations

import json

import httpx
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session

from .config import AI_MODEL_API_KEY,AI_MODEL_BASE_URL,AI_MODEL_NAME,AI_MODEL_STATE,AI_MODEL_TIMEOUT
from .database import get_db
from .deps import get_current_user
from .models import Analysis,User

router=APIRouter(prefix="/ai",tags=["ai"])

SYSTEM_PROMPT=(
 "You are the Genopedia research assistant. You answer questions about DNA/RNA "
 "sequence analysis results for research purposes only. You never provide medical "
 "diagnosis, treatment advice, or propose DNA edits, and you say when evidence is "
 "insufficient. Keep answers concise and cite the numbers from the provided analysis."
)
_UNAVAILABLE_DETAIL="The Genopedia model is still in training and evaluation. This assistant activates automatically once a validated model endpoint is configured."

class AIQuery(BaseModel):
    question:str=Field(min_length=1,max_length=4000)
    analysis_id:int|None=None

def _configured()->bool:
    return bool(AI_MODEL_BASE_URL and AI_MODEL_NAME) and AI_MODEL_STATE=="available"

def _status()->dict:
    configured=bool(AI_MODEL_BASE_URL and AI_MODEL_NAME)
    return {
        "available":_configured(),
        "state":AI_MODEL_STATE if configured else (AI_MODEL_STATE or "training"),
        "model":AI_MODEL_NAME or None,
        "message":"Model endpoint configured and available." if _configured() else _UNAVAILABLE_DETAIL,
    }

@router.get("/status")
def ai_status():
    return _status()

@router.post("/query")
def ai_query(payload:AIQuery,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if not _configured():
        raise HTTPException(503,detail={"state":_status()["state"],"message":_UNAVAILABLE_DETAIL})
    context=""
    if payload.analysis_id is not None:
        item=db.get(Analysis,payload.analysis_id)
        if item is None or item.user_id!=user.id:raise HTTPException(404,"Analysis not found")
        summary=item.summary_json
        if len(summary)>8000:summary=summary[:8000]+"...[truncated]"
        context=f"\n\nAnalysis '{item.name}' summary (JSON):\n{summary}"
    headers={"Content-Type":"application/json"}
    if AI_MODEL_API_KEY:headers["Authorization"]=f"Bearer {AI_MODEL_API_KEY}"
    body={"model":AI_MODEL_NAME,"messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":payload.question+context}],"max_tokens":800,"temperature":0.2}
    try:
        response=httpx.post(f"{AI_MODEL_BASE_URL}/chat/completions",headers=headers,json=body,timeout=AI_MODEL_TIMEOUT)
        response.raise_for_status()
        data=response.json()
        answer=data["choices"][0]["message"]["content"]
    except httpx.HTTPError as exc:
        raise HTTPException(502,detail=f"Model endpoint error: {type(exc).__name__}") from exc
    except (KeyError,IndexError,ValueError,TypeError) as exc:
        raise HTTPException(502,detail="Model endpoint returned an unexpected response shape") from exc
    return {"answer":answer,"model":AI_MODEL_NAME,"analysis_id":payload.analysis_id}
