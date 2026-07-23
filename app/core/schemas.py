from typing import Optional, List
from pydantic import BaseModel


class PatientInfo(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None


class Diagnosis(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    date: Optional[str] = None


class Treatment(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None


class Metadata(BaseModel):
    document_type: Optional[str] = None
    institution: Optional[str] = None
    doctor: Optional[str] = None
    date: Optional[str] = None


class ExtractedData(BaseModel):
    patient_info: Optional[PatientInfo] = None
    diagnoses: Optional[List[Diagnosis]] = None
    treatments: Optional[List[Treatment]] = None
    metadata: Optional[Metadata] = None


class LLMRequest(BaseModel):
    model: str
    messages: List[dict]
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None
    truncated: bool = False
