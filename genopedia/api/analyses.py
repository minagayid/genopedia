"""Per-user sequence analyses: create, list, inspect, compare, delete."""

from __future__ import annotations

import json

from fastapi import APIRouter,Depends,HTTPException,Request
from starlette.datastructures import UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel,Field
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from .analysis_service import AnalysisInputError,compare_sequences,run_analysis
from .config import ANALYSIS_MAX_BYTES,ANALYSIS_MAX_PER_USER
from .database import get_db
from .deps import get_current_user
from .models import Analysis,User

router=APIRouter(prefix="/analyses",tags=["analyses"])
from .app import limiter  # shared rate limiter instance


class AnalysisCreate(BaseModel):
    name:str=Field(min_length=1,max_length=200)
    content:str=Field(min_length=1)
    format:str="auto"
    molecule:str=Field(default="DNA",pattern="^(DNA|RNA|PROTEIN)$")

class CompareRequest(BaseModel):
    reference_id:int
    sample_id:int
    chromosome:str=Field(default="chr1",max_length=40)

def _out(item:Analysis,detail:bool=False)->dict:
    base={"id":item.id,"name":item.name,"input_format":item.input_format,"molecule":item.molecule,"record_count":item.record_count,"variant_count":item.variant_count,"total_bases":item.total_bases,"sequence_sha256":item.sequence_sha256,"created_at":item.created_at.isoformat()}
    if detail:
        base["summary"]=json.loads(item.summary_json)
        base["records"]=json.loads(item.records_json)
        base["report_url"]=f"/analyses/{item.id}/report"
    return base

def _get_owned(analysis_id:int,user:User,db:Session)->Analysis:
    item=db.get(Analysis,analysis_id)
    if item is None or item.user_id!=user.id:raise HTTPException(404,"Analysis not found")
    return item

def _store(user:User,db:Session,*,name:str,molecule:str,content:bytes,filename:str,requested_format:str)->Analysis:
    count=db.scalar(select(func.count(Analysis.id)).where(Analysis.user_id==user.id)) or 0
    if count>=ANALYSIS_MAX_PER_USER:raise HTTPException(429,f"Analysis limit of {ANALYSIS_MAX_PER_USER} reached; delete old analyses first")
    if len(content)>ANALYSIS_MAX_BYTES:raise HTTPException(413,f"Input exceeds the {ANALYSIS_MAX_BYTES}-byte limit")
    try:result=run_analysis(content,filename=filename,requested_format=requested_format,molecule=molecule)
    except AnalysisInputError as exc:raise HTTPException(422,str(exc)) from exc
    item=Analysis(user_id=user.id,name=name.strip()[:200] or "Untitled analysis",molecule=molecule,**result)
    db.add(item);db.commit();db.refresh(item)
    return item

@router.post("",status_code=201)
@limiter.limit("10/minute")
async def create_analysis(request:Request,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    content_type=request.headers.get("content-type","")
    if content_type.startswith("multipart/form-data"):
        form=await request.form()
        upload=form.get("file")
        if not isinstance(upload,UploadFile):raise HTTPException(422,"multipart requests need a file field")
        name=str(form.get("name") or upload.filename or "Untitled analysis")
        molecule=str(form.get("molecule") or "DNA").upper()
        fmt=str(form.get("format") or "auto")
        content=await upload.read(ANALYSIS_MAX_BYTES+1)
        item=_store(user,db,name=name,molecule=molecule,content=content,filename=upload.filename or "",requested_format=fmt)
    else:
        try:payload=AnalysisCreate.model_validate(await request.json())
        except Exception as exc:raise HTTPException(422,f"invalid JSON body: {exc}") from exc
        item=_store(user,db,name=payload.name,molecule=payload.molecule,content=payload.content.encode(),filename="",requested_format=payload.format)
    return _out(item,detail=True)

@router.get("")
def list_analyses(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    items=db.scalars(select(Analysis).where(Analysis.user_id==user.id).order_by(Analysis.created_at.desc())).all()
    return {"analyses":[_out(item) for item in items],"count":len(items)}

@router.get("/{analysis_id}")
def get_analysis(analysis_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return _out(_get_owned(analysis_id,user,db),detail=True)

@router.get("/{analysis_id}/report",response_class=HTMLResponse)
def get_analysis_report(analysis_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return HTMLResponse(_get_owned(analysis_id,user,db).report_html)

@router.delete("/{analysis_id}",status_code=204)
def delete_analysis(analysis_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=_get_owned(analysis_id,user,db);db.delete(item);db.commit()

@router.post("/compare")
@limiter.limit("10/minute")
def compare_analyses(request:Request,payload:CompareRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    reference=_get_owned(payload.reference_id,user,db);sample=_get_owned(payload.sample_id,user,db)
    ref_records=json.loads(reference.records_json);sample_records=json.loads(sample.records_json)
    if not ref_records or not sample_records:raise HTTPException(422,"Both analyses need at least one stored sequence record to compare")
    return compare_sequences(ref_records[0]["sequence"],sample_records[0]["sequence"],chromosome=payload.chromosome)
