"""
Workflow Orchestrator
Manages the execution of all agents in the correct sequence
"""

from typing import Optional
from loguru import logger
import uuid
from datetime import datetime

from core.state import ContractState, create_initial_state, ProcessingStatus
from agents.parser_agent import ParserAgent
from agents.legal_agent import LegalAgent
from agents.risk_agent import RiskAgent
from agents.coordinator_agent import CoordinatorAgent


class ContractAnalysisOrchestrator:
    """
    Orchestrates the complete contract analysis workflow
    """

    def __init__(self):
        """Initialize all agents"""
        logger.info("Initializing Contract Analysis Orchestrator")

        try:
            self.parser = ParserAgent()
            self.legal = LegalAgent()
            self.risk = RiskAgent()
            self.coordinator = CoordinatorAgent()

            logger.success("All agents initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise

    async def analyze_contract(
        self,
        filename: str,
        file_size: int,
        user_instructions: Optional[str] = None,
        priority_level: str = "medium"
    ) -> ContractState:
        """
        Run the complete contract analysis workflow

        Args:
            filename: Name of the contract file
            file_size: Size of the file in bytes
            user_instructions: Optional user instructions for analysis
            priority_level: Priority level (low/medium/high/critical)

        Returns:
            Final contract state with all analysis results
        """
        # Generate unique contract ID
        contract_id = f"CONTRACT-{uuid.uuid4().hex[:8].upper()}"

        logger.info("=" * 80)
        logger.info(f"Starting Contract Analysis Workflow: {contract_id}")
        logger.info(
            f"File: {filename} | Size: {file_size} bytes | Priority: {priority_level}")
        logger.info("=" * 80)

        # Create initial state
        state = create_initial_state(
            contract_id=contract_id,
            filename=filename,
            file_size=file_size,
            user_instructions=user_instructions,
            priority_level=priority_level
        )

        try:
            # STEP 1: Parse Document
            logger.info("\n📄 STEP 1/4: Document Parsing")
            logger.info("─" * 60)
            state = await self.parser.handle_processing(state)

            if state["status"] == ProcessingStatus.FAILED:
                raise Exception("Parser agent failed")

            logger.success(
                f"✓ Parsing complete: {len(state['parser_output']['structured_sections'])} sections")

            # STEP 2: Legal Analysis
            logger.info("\n⚖️  STEP 2/4: Legal Analysis")
            logger.info("─" * 60)
            state = await self.legal.handle_processing(state)

            if state["status"] == ProcessingStatus.FAILED:
                raise Exception("Legal agent failed")

            logger.success(
                f"✓ Legal analysis complete: {len(state['legal_analysis']['clauses_identified'])} clauses")

            # STEP 3: Risk Assessment
            logger.info("\n🎯 STEP 3/4: Risk Assessment")
            logger.info("─" * 60)
            state = await self.risk.handle_processing(state)

            if state["status"] == ProcessingStatus.FAILED:
                raise Exception("Risk agent failed")

            logger.success(
                f"✓ Risk assessment complete: Score {state['risk_assessment']['overall_risk_score']}/10")

            # STEP 4: Final Synthesis
            logger.info("\n🧠 STEP 4/4: Report Synthesis")
            logger.info("─" * 60)
            state = await self.coordinator.handle_processing(state)

            if state["status"] == ProcessingStatus.FAILED:
                raise Exception("Coordinator agent failed")

            logger.success("✓ Report synthesis complete")

            # Mark completion time
            state["completed_at"] = datetime.utcnow().isoformat()

            logger.info("\n" + "=" * 80)
            logger.success(f"✅ Analysis Complete: {contract_id}")
            logger.success(f"Status: {state['status'].value}")
            logger.success(
                f"Recommendation: {state['final_report']['approval_recommendation']}")
            logger.info("=" * 80)

            return state

        except Exception as e:
            logger.error(f"\n❌ Workflow failed: {str(e)}")
            logger.exception(e)

            # Update state with error
            state["status"] = ProcessingStatus.FAILED
            state["completed_at"] = datetime.utcnow().isoformat()

            raise

    def get_status(self) -> dict:
        """Get orchestrator status"""
        return {
            "orchestrator_ready": True,
            "agents": {
                "parser": "ready",
                "legal": "ready",
                "risk": "ready",
                "coordinator": "ready"
            }
        }
