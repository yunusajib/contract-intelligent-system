"""
FastAPI Application
Main API endpoints for the Contract Intelligence System
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
import os
from loguru import logger

from api.models import (
    HealthResponse,
    ContractUploadResponse,
    ContractAnalysisResponse,
    ErrorResponse,
    FinalReportResponse,
    DetailedAnalysisResponse,
    RiskMatrixResponse
)
from core.orchestrator import ContractAnalysisOrchestrator
from core.config import get_settings

# Initialize FastAPI app
app = FastAPI(
    title="Contract Intelligence System",
    description="Multi-agent AI system for contract analysis and risk assessment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator (single instance for the app)
orchestrator: Optional[ContractAnalysisOrchestrator] = None

# Store analysis results in memory (in production, use database)
analysis_cache: dict = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup"""
    global orchestrator

    logger.info("Starting Contract Intelligence System API")

    try:
        orchestrator = ContractAnalysisOrchestrator()
        logger.success("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {str(e)}")
        raise


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with simple UI"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contract Intelligence System</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: white;
                color: #333;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            .upload-form {
                margin: 30px 0;
                padding: 20px;
                background: #f5f5f5;
                border-radius: 10px;
            }
            input[type="file"] {
                margin: 10px 0;
                padding: 10px;
            }
            textarea {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-family: inherit;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
            }
            button:hover {
                background: #764ba2;
            }
            .status {
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                display: none;
            }
            .status.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .status.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .status.processing {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            .links {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            .links a {
                color: #667eea;
                text-decoration: none;
                margin-right: 20px;
                font-weight: bold;
            }
            .links a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Contract Intelligence System</h1>
            <p><strong>Multi-Agent AI Contract Analysis</strong></p>
            
            <div class="upload-form">
                <h3>Upload Contract for Analysis</h3>
                <form id="uploadForm">
                    <div>
                        <label><strong>Select Contract File (PDF or Text):</strong></label><br>
                        <input type="file" id="fileInput" accept=".pdf,.txt" required>
                    </div>
                    <div>
                        <label><strong>Analysis Instructions (Optional):</strong></label>
                        <textarea id="instructions" rows="3" 
                            placeholder="e.g., Focus on liability clauses and payment terms"></textarea>
                    </div>
                    <div>
                        <label><strong>Priority Level:</strong></label>
                        <select id="priority" style="padding: 8px; margin: 10px 0;">
                            <option value="low">Low</option>
                            <option value="medium" selected>Medium</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                        </select>
                    </div>
                    <button type="submit">🚀 Analyze Contract</button>
                </form>
            </div>
            
            <div id="status" class="status"></div>
            
            <div class="links">
                <h3>API Documentation</h3>
                <a href="/docs" target="_blank">📘 Swagger Docs</a>
                <a href="/redoc" target="_blank">📗 ReDoc</a>
                <a href="/health" target="_blank">💚 Health Check</a>
            </div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const fileInput = document.getElementById('fileInput');
                const instructions = document.getElementById('instructions').value;
                const priority = document.getElementById('priority').value;
                const statusDiv = document.getElementById('status');
                
                if (!fileInput.files[0]) {
                    alert('Please select a file');
                    return;
                }
                
                // Show processing status
                statusDiv.className = 'status processing';
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = '⏳ Uploading and analyzing contract... This may take 30-60 seconds.';
                
                // Create form data
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('user_instructions', instructions);
                formData.append('priority_level', priority);
                
                try {
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        statusDiv.className = 'status success';
                        statusDiv.innerHTML = `
                            <h3>✅ Analysis Complete!</h3>
                            <p><strong>Contract ID:</strong> ${result.contract_id}</p>
                            <p><strong>Status:</strong> ${result.status}</p>
                            <p><strong>Recommendation:</strong> ${result.final_report.approval_recommendation}</p>
                            <p><strong>Overall Risk:</strong> ${result.final_report.risk_matrix.overall_risk}</p>
                            <br>
                            <p><a href="/api/results/${result.contract_id}" target="_blank">View Full Report (JSON)</a></p>
                        `;
                    } else {
                        throw new Error(result.detail || 'Analysis failed');
                    }
                } catch (error) {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = `
                        <h3>❌ Error</h3>
                        <p>${error.message}</p>
                    `;
                }
            });
        </script>
    </body>
    </html>
    """


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if orchestrator is None:
        raise HTTPException(
            status_code=503, detail="Orchestrator not initialized")

    status = orchestrator.get_status()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        agents_status=status["agents"]
    )


@app.post("/api/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    file: UploadFile = File(...),
    user_instructions: Optional[str] = Form(None),
    priority_level: str = Form("medium")
):
    """
    Upload and analyze a contract

    - **file**: Contract file (PDF or text)
    - **user_instructions**: Optional analysis instructions
    - **priority_level**: Priority (low/medium/high/critical)
    """
    logger.info(f"Received analysis request for: {file.filename}")

    # Validate file type
    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported"
        )

    try:
        # Read file content (in production, save to disk or S3)
        content = await file.read()
        file_size = len(content)

        logger.info(f"File uploaded: {file.filename} ({file_size} bytes)")

        # Run analysis
        state = await orchestrator.analyze_contract(
            filename=file.filename,
            file_size=file_size,
            user_instructions=user_instructions,
            priority_level=priority_level
        )

        # Cache the result
        analysis_cache[state["contract_metadata"]["contract_id"]] = state

        # Calculate processing time
        start_time = datetime.fromisoformat(state["started_at"])
        end_time = datetime.fromisoformat(state["completed_at"])
        processing_time = (end_time - start_time).total_seconds()

        # Build response
        if state["final_report"]:
            final_report = FinalReportResponse(
                executive_summary=state["final_report"]["executive_summary"],
                detailed_analysis=DetailedAnalysisResponse(
                    **state["final_report"]["detailed_analysis"]),
                risk_matrix=RiskMatrixResponse(
                    **state["final_report"]["risk_matrix"]),
                action_items=state["final_report"]["action_items"],
                approval_recommendation=state["final_report"]["approval_recommendation"]
            )
        else:
            final_report = None

        return ContractAnalysisResponse(
            contract_id=state["contract_metadata"]["contract_id"],
            filename=state["contract_metadata"]["filename"],
            status=state["status"].value,
            started_at=state["started_at"],
            completed_at=state["completed_at"],
            final_report=final_report,
            processing_time_seconds=processing_time,
            errors=state.get("errors", []) if state.get("errors") else None
        )

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/{contract_id}", response_model=ContractAnalysisResponse)
async def get_analysis_results(contract_id: str):
    """
    Get analysis results for a specific contract
    """
    if contract_id not in analysis_cache:
        raise HTTPException(
            status_code=404, detail="Contract analysis not found")

    state = analysis_cache[contract_id]

    # Calculate processing time if completed
    processing_time = None
    if state["completed_at"]:
        start_time = datetime.fromisoformat(state["started_at"])
        end_time = datetime.fromisoformat(state["completed_at"])
        processing_time = (end_time - start_time).total_seconds()

    # Build response
    if state["final_report"]:
        final_report = FinalReportResponse(
            executive_summary=state["final_report"]["executive_summary"],
            detailed_analysis=DetailedAnalysisResponse(
                **state["final_report"]["detailed_analysis"]),
            risk_matrix=RiskMatrixResponse(
                **state["final_report"]["risk_matrix"]),
            action_items=state["final_report"]["action_items"],
            approval_recommendation=state["final_report"]["approval_recommendation"]
        )
    else:
        final_report = None

    return ContractAnalysisResponse(
        contract_id=state["contract_metadata"]["contract_id"],
        filename=state["contract_metadata"]["filename"],
        status=state["status"].value,
        started_at=state["started_at"],
        completed_at=state["completed_at"],
        final_report=final_report,
        processing_time_seconds=processing_time,
        errors=state.get("errors", []) if state.get("errors") else None
    )


@app.get("/api/contracts")
async def list_contracts():
    """
    List all analyzed contracts
    """
    contracts = []

    for contract_id, state in analysis_cache.items():
        contracts.append({
            "contract_id": contract_id,
            "filename": state["contract_metadata"]["filename"],
            "status": state["status"].value,
            "started_at": state["started_at"],
            "completed_at": state["completed_at"]
        })

    return {"contracts": contracts, "total": len(contracts)}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
