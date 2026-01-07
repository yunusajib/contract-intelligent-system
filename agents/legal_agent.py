"""
Legal Analysis Agent
Analyzes contract terms, clauses, and obligations using Crew.AI
"""

from typing import Dict, Any
from crewai import Agent, Crew, Process
from loguru import logger
import json
import re

from core.base_agent import BaseContractAgent
from core.state import (
    ContractState, AgentType, MessageType,
    ProcessingStatus, LegalAnalysis
)


class LegalAgent(BaseContractAgent):
    """
    Legal Agent specializes in:
    - Identifying contract parties and relationships
    - Analyzing key terms and definitions
    - Extracting obligations and deadlines
    - Identifying legal clauses (liability, indemnification, termination, etc.)
    - Determining jurisdiction and governing law
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.LEGAL,
            model="gpt-4-turbo-preview"
        )

    def get_role(self) -> str:
        return "Senior Contract Attorney and Legal Analyst"

    def get_goal(self) -> str:
        return "Thoroughly analyze contract terms, identify all obligations, extract key clauses, and provide comprehensive legal assessment"

    def get_backstory(self) -> str:
        return """You are a seasoned contract attorney with 15+ years of experience in corporate law, 
        specializing in commercial contracts. You have reviewed thousands of NDAs, service agreements, 
        partnership contracts, and licensing deals. You excel at identifying subtle legal implications, 
        unfavorable terms, and potential liabilities. Your expertise includes contract law across multiple 
        jurisdictions, with deep knowledge of Delaware corporate law, California business regulations, 
        and New York commercial practices. You can quickly identify non-standard clauses, one-sided terms, 
        and provisions that may create future problems."""

    def _create_agent(self) -> Agent:
        """Create the Crew.AI legal agent"""
        return Agent(
            role=self.get_role(),
            goal=self.get_goal(),
            backstory=self.get_backstory(),
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )

    async def process(self, state: ContractState) -> ContractState:
        """
        Main processing: Analyze legal aspects of the contract
        """
        try:
            # Update status
            state = self.update_status(state, ProcessingStatus.ANALYZING)

            # Validate we have parser output
            if not state.get("parser_output"):
                raise ValueError("Parser output not available")

            parser_output = state["parser_output"]
            contract_id = state["contract_metadata"]["contract_id"]

            self.log_processing_step(
                state, f"Starting legal analysis for {contract_id}")

            # Create legal analysis task
            analysis_task = self.create_task(
                description=f"""Conduct a comprehensive legal analysis of this contract:

CONTRACT SECTIONS:
{json.dumps(parser_output['structured_sections'], indent=2)}

RAW TEXT EXCERPT:
{parser_output['raw_text'][:1500]}...

Your analysis must include:

1. CONTRACT TYPE: What type of agreement is this?
2. PARTIES: Identify all parties involved (full legal names)
3. KEY TERMS: Extract and define critical terms (at least 3-5)
4. OBLIGATIONS: List all obligations for each party with deadlines
5. CLAUSES: Identify major clauses (confidentiality, liability, indemnification, termination, etc.)
6. JURISDICTION: What jurisdiction/governing law applies?
7. DATES: Effective date, termination date, any critical deadlines

Provide output in this JSON format:
{{
    "contract_type": "e.g., Non-Disclosure Agreement",
    "parties_involved": ["Party 1 Legal Name", "Party 2 Legal Name"],
    "key_terms": [
        {{"term": "Term Name", "definition": "Definition", "importance": "high|medium|low"}}
    ],
    "obligations": [
        {{
            "party": "Party Name",
            "description": "What they must do",
            "deadline": "When or duration",
            "consequence": "What happens if not met"
        }}
    ],
    "clauses_identified": [
        {{
            "type": "Clause type (e.g., Confidentiality)",
            "summary": "Brief summary of the clause",
            "risk_level": "low|medium|high",
            "favorability": "favorable|neutral|unfavorable"
        }}
    ],
    "jurisdiction": "State/Country",
    "effective_date": "YYYY-MM-DD or description",
    "termination_date": "YYYY-MM-DD or description"
}}""",
                expected_output="JSON formatted legal analysis"
            )

            # Execute analysis
            analysis_crew = Crew(
                agents=[self.agent],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=False
            )

            self.log_processing_step(state, "Executing legal analysis task")
            result = analysis_crew.kickoff()

            # Parse result
            analysis_data = self._parse_crew_result(result)

            # Create LegalAnalysis
            legal_analysis: LegalAnalysis = {
                "key_terms": analysis_data.get("key_terms", []),
                "obligations": analysis_data.get("obligations", []),
                "parties_involved": analysis_data.get("parties_involved", []),
                "contract_type": analysis_data.get("contract_type", "Unknown"),
                "jurisdiction": analysis_data.get("jurisdiction"),
                "effective_date": analysis_data.get("effective_date"),
                "termination_date": analysis_data.get("termination_date"),
                "clauses_identified": analysis_data.get("clauses_identified", [])
            }

            # Add to state
            state["legal_analysis"] = legal_analysis

            # Send message
            state = self.send_message(
                state,
                to_agent=AgentType.RISK,
                message_type=MessageType.ANALYSIS_RESULT,
                content={
                    "clauses_found": len(legal_analysis["clauses_identified"]),
                    "obligations_count": len(legal_analysis["obligations"]),
                    "contract_type": legal_analysis["contract_type"]
                }
            )

            self.log_processing_step(
                state,
                f"Legal analysis complete: {len(legal_analysis['clauses_identified'])} clauses analyzed"
            )

            return state

        except Exception as e:
            state = self.add_error(state, f"Legal analysis failed: {str(e)}")
            raise

    def _parse_crew_result(self, result: Any) -> Dict[str, Any]:
        """Parse Crew.AI result into structured format"""
        try:
            result_str = str(result)

            # Try to parse as JSON
            try:
                return json.loads(result_str)
            except json.JSONDecodeError:
                # Extract JSON from markdown
                json_match = re.search(
                    r'```json\s*(\{.*?\})\s*```', result_str, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

                # Extract any JSON object
                json_match = re.search(
                    r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_str, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))

                # Fallback
                return self._create_fallback_analysis()

        except Exception as e:
            logger.error(f"Failed to parse legal analysis result: {str(e)}")
            return self._create_fallback_analysis()

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """Create a basic analysis structure if parsing fails"""
        return {
            "contract_type": "Unknown",
            "parties_involved": ["Unknown"],
            "key_terms": [],
            "obligations": [],
            "clauses_identified": [],
            "jurisdiction": None,
            "effective_date": None,
            "termination_date": None
        }

    def validate_input(self, state: ContractState) -> bool:
        """Validate that we have parser output"""
        return state.get("parser_output") is not None
