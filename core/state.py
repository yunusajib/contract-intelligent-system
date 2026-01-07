"""
Agent State Management System
Defines the shared state structure across all agents in the multi-agent system
"""

from typing import TypedDict, List, Dict, Optional, Annotated, Any
from datetime import datetime
from enum import Enum
import operator


class AgentType(str, Enum):
    """Types of agents in the system"""
    COORDINATOR = "coordinator"
    PARSER = "parser"
    LEGAL = "legal"
    RISK = "risk"


class MessageType(str, Enum):
    """Types of messages agents can send"""
    TASK_ASSIGNMENT = "task_assignment"
    ANALYSIS_RESULT = "analysis_result"
    ERROR = "error"
    COMPLETION = "completion"
    REQUEST_INFO = "request_info"


class ProcessingStatus(str, Enum):
    """Status of contract processing"""
    PENDING = "pending"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    RISK_ASSESSMENT = "risk_assessment"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentMessage(TypedDict):
    """Standard message format for inter-agent communication"""
    from_agent: AgentType
    to_agent: Optional[AgentType]
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str
    message_id: str


class ContractMetadata(TypedDict):
    """Metadata about the contract being analyzed"""
    contract_id: str
    filename: str
    upload_timestamp: str
    file_size: int
    num_pages: Optional[int]


class ParserOutput(TypedDict):
    """Output from the Document Parser Agent"""
    raw_text: str
    structured_sections: Dict[str, str]
    metadata: Dict[str, Any]
    extraction_confidence: float


class LegalAnalysis(TypedDict):
    """Output from the Legal Analysis Agent"""
    key_terms: List[Dict[str, Any]]
    obligations: List[Dict[str, Any]]
    parties_involved: List[str]
    contract_type: str
    jurisdiction: Optional[str]
    effective_date: Optional[str]
    termination_date: Optional[str]
    clauses_identified: List[Dict[str, Any]]


class RiskAssessment(TypedDict):
    """Output from the Risk Assessment Agent"""
    overall_risk_score: float  # 0-10 scale
    risk_categories: Dict[str, Dict[str, Any]]
    critical_risks: List[Dict[str, Any]]
    recommendations: List[str]
    compliance_issues: List[Dict[str, Any]]


class FinalReport(TypedDict):
    """Final synthesized report from Coordinator"""
    executive_summary: str
    detailed_analysis: Dict[str, Any]
    risk_matrix: Dict[str, Any]
    action_items: List[str]
    approval_recommendation: str


class ContractState(TypedDict):
    """
    Main state object that gets passed between agents
    This is the core of the LangGraph state management
    """
    # Contract Information
    contract_metadata: ContractMetadata

    # Processing Status
    status: ProcessingStatus
    current_agent: AgentType

    # Agent Outputs
    parser_output: Optional[ParserOutput]
    legal_analysis: Optional[LegalAnalysis]
    risk_assessment: Optional[RiskAssessment]
    final_report: Optional[FinalReport]

    # Communication
    messages: Annotated[List[AgentMessage], operator.add]

    # Errors and Logs
    errors: Annotated[List[Dict[str, Any]], operator.add]
    processing_logs: Annotated[List[str], operator.add]

    # Timing
    started_at: str
    completed_at: Optional[str]

    # Additional Context
    user_instructions: Optional[str]
    priority_level: str  # "low", "medium", "high", "critical"


def create_initial_state(
    contract_id: str,
    filename: str,
    file_size: int,
    user_instructions: Optional[str] = None,
    priority_level: str = "medium"
) -> ContractState:
    """
    Factory function to create initial state for a new contract analysis
    """
    now = datetime.utcnow().isoformat()

    return ContractState(
        contract_metadata=ContractMetadata(
            contract_id=contract_id,
            filename=filename,
            upload_timestamp=now,
            file_size=file_size,
            num_pages=None
        ),
        status=ProcessingStatus.PENDING,
        current_agent=AgentType.COORDINATOR,
        parser_output=None,
        legal_analysis=None,
        risk_assessment=None,
        final_report=None,
        messages=[],
        errors=[],
        processing_logs=[],
        started_at=now,
        completed_at=None,
        user_instructions=user_instructions,
        priority_level=priority_level
    )


def create_agent_message(
    from_agent: AgentType,
    to_agent: Optional[AgentType],
    message_type: MessageType,
    content: Dict[str, Any]
) -> AgentMessage:
    """Helper function to create standardized agent messages"""
    import uuid

    return AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        content=content,
        timestamp=datetime.utcnow().isoformat(),
        message_id=str(uuid.uuid4())
    )
