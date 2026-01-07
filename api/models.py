"""
API Response Models
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: str
    version: str = "1.0.0"
    agents_status: Dict[str, str]


class ContractUploadResponse(BaseModel):
    """Response when contract is uploaded"""
    contract_id: str
    filename: str
    file_size: int
    status: str
    message: str
    started_at: str


class RiskMatrixResponse(BaseModel):
    """Risk matrix in the response"""
    overall_risk: str
    financial_risk: str
    legal_risk: str
    operational_risk: str


class DetailedAnalysisResponse(BaseModel):
    """Detailed analysis section"""
    contract_overview: str
    key_findings: List[str]
    legal_assessment: str
    risk_summary: str


class FinalReportResponse(BaseModel):
    """Final report structure"""
    executive_summary: str
    detailed_analysis: DetailedAnalysisResponse
    risk_matrix: RiskMatrixResponse
    action_items: List[str]
    approval_recommendation: str


class ContractAnalysisResponse(BaseModel):
    """Complete contract analysis response"""
    contract_id: str
    filename: str
    status: str
    started_at: str
    completed_at: Optional[str]

    # Analysis results (only present when completed)
    final_report: Optional[FinalReportResponse] = None

    # Processing metadata
    processing_time_seconds: Optional[float] = None
    errors: Optional[List[Dict[str, Any]]] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    timestamp: str
    contract_id: Optional[str] = None


class ContractMetadataResponse(BaseModel):
    """Contract metadata"""
    contract_id: str
    filename: str
    file_size: int
    upload_timestamp: str
    status: str
    priority_level: str


# Request models

class AnalysisRequest(BaseModel):
    """Optional request parameters for analysis"""
    user_instructions: Optional[str] = Field(
        None,
        description="Specific instructions or focus areas for the analysis"
    )
    priority_level: str = Field(
        default="medium",
        description="Priority level: low, medium, high, critical"
    )
