"""
Coordinator Agent using Crew.AI
Orchestrates the multi-agent workflow and synthesizes final reports
"""

from typing import Dict, Any
import json
from loguru import logger
from crewai import Agent, Crew, Process

from core.base_agent import BaseContractAgent
from core.state import (
    ContractState, AgentType, MessageType,
    ProcessingStatus, FinalReport
)


class CoordinatorAgent(BaseContractAgent):
    """
    The Coordinator Agent orchestrates all other agents using Crew.AI
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.COORDINATOR,
            model="gpt-4-turbo-preview"
        )

    def get_role(self) -> str:
        return "Senior Contract Analysis Coordinator"

    def get_goal(self) -> str:
        return "Orchestrate contract analysis workflow and synthesize comprehensive executive reports from all agent outputs"

    def get_backstory(self) -> str:
        return """You are a highly experienced contract analysis coordinator with 15+ years in legal operations. 
        You excel at synthesizing complex information from multiple sources into clear, actionable executive reports.
        You understand legal nuances, risk assessment, and business implications. Your reports are trusted by 
        C-level executives for critical business decisions."""

    def _create_agent(self) -> Agent:
        """Create the Crew.AI coordinator agent"""
        return Agent(
            role=self.get_role(),
            goal=self.get_goal(),
            backstory=self.get_backstory(),
            verbose=True,
            allow_delegation=True,  # Can delegate to other agents
            max_iter=5,
            llm=self.model
        )

    async def process(self, state: ContractState) -> ContractState:
        """
        Main coordination logic - synthesizes final report
        """
        current_status = state["status"]

        # If all agent outputs are available, synthesize final report
        if (state["parser_output"] and
            state["legal_analysis"] and
                state["risk_assessment"]):

            self.log_processing_step(
                state, "All agent outputs available, synthesizing final report")
            state = await self.synthesize_report(state)

        else:
            self.log_processing_step(
                state, f"Current status: {current_status.value}")

        return state

    async def synthesize_report(self, state: ContractState) -> ContractState:
        """
        Synthesize all agent outputs into a final comprehensive report
        """
        try:
            # Update status
            state = self.update_status(state, ProcessingStatus.SYNTHESIZING)

            # Build synthesis context
            synthesis_context = self._build_synthesis_context(state)

            # Create synthesis task
            synthesis_task = self.create_task(
                description=f"""Synthesize a comprehensive executive contract analysis report from the following data:

{synthesis_context}

Provide your analysis in the following JSON format:
{{
    "executive_summary": "3-4 paragraph executive summary highlighting key points",
    "detailed_analysis": {{
        "contract_overview": "Brief overview of contract type and parties",
        "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
        "legal_assessment": "Legal analysis summary",
        "risk_summary": "Risk assessment summary"
    }},
    "risk_matrix": {{
        "overall_risk": "Low|Medium|High|Critical",
        "financial_risk": "Low|Medium|High|Critical",
        "legal_risk": "Low|Medium|High|Critical",
        "operational_risk": "Low|Medium|High|Critical"
    }},
    "action_items": [
        "Specific action item 1",
        "Specific action item 2",
        "Specific action item 3"
    ],
    "approval_recommendation": "Approve|Approve with Modifications|Reject|Requires Legal Review"
}}""",
                expected_output="JSON formatted comprehensive contract analysis report"
            )

            # Create crew with just the coordinator
            synthesis_crew = Crew(
                agents=[self.agent],
                tasks=[synthesis_task],
                process=Process.sequential,
                verbose=True
            )

            # Execute synthesis
            self.log_processing_step(
                state, "Executing synthesis task via Crew.AI")
            result = synthesis_crew.kickoff()

            # Parse result
            report_data = self._parse_result(result)

            # Create FinalReport
            final_report: FinalReport = {
                "executive_summary": report_data.get("executive_summary", ""),
                "detailed_analysis": report_data.get("detailed_analysis", {}),
                "risk_matrix": report_data.get("risk_matrix", {}),
                "action_items": report_data.get("action_items", []),
                "approval_recommendation": report_data.get("approval_recommendation", "Requires Review")
            }

            # Add to state
            state["final_report"] = final_report

            # Update status to completed
            from datetime import datetime
            state = self.update_status(state, ProcessingStatus.COMPLETED)
            state["completed_at"] = datetime.utcnow().isoformat()

            # Send completion message
            state = self.send_message(
                state,
                to_agent=None,
                message_type=MessageType.COMPLETION,
                content={"message": "Contract analysis completed successfully"}
            )

            self.log_processing_step(
                state, "Final report synthesized successfully")

            return state

        except Exception as e:
            state = self.add_error(
                state,
                f"Failed to synthesize report: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            raise

    def _parse_result(self, result: Any) -> Dict[str, Any]:
        """Parse the Crew.AI result into JSON"""
        try:
            # If result is already a dict
            if isinstance(result, dict):
                return result

            # Convert to string
            result_str = str(result)

            # Try to parse as JSON
            try:
                return json.loads(result_str)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(
                    r'```json\s*(\{.*?\})\s*```', result_str, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

                # Try to find JSON object in the text
                json_match = re.search(
                    r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_str, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))

                raise ValueError("Could not extract JSON from result")

        except Exception as e:
            logger.error(f"Failed to parse result: {str(e)}")
            # Return a default structure
            return {
                "executive_summary": str(result)[:500],
                "detailed_analysis": {},
                "risk_matrix": {"overall_risk": "Medium"},
                "action_items": ["Review raw output for details"],
                "approval_recommendation": "Requires Review"
            }

    def _build_synthesis_context(self, state: ContractState) -> str:
        """Build the context for synthesis"""
        contract_id = state["contract_metadata"]["contract_id"]
        filename = state["contract_metadata"]["filename"]

        parser_data = state["parser_output"]
        legal_data = state["legal_analysis"]
        risk_data = state["risk_assessment"]

        context = f"""
CONTRACT INFORMATION:
- Contract ID: {contract_id}
- Filename: {filename}
- Pages: {parser_data.get('metadata', {}).get('num_pages', 'Unknown')}

DOCUMENT STRUCTURE:
Extraction Confidence: {parser_data.get('extraction_confidence', 0)}
Sections: {', '.join(list(parser_data.get('structured_sections', {}).keys())[:5])}

LEGAL ANALYSIS:
Contract Type: {legal_data.get('contract_type', 'Unknown')}
Parties: {', '.join(legal_data.get('parties_involved', []))}
Key Terms: {len(legal_data.get('key_terms', []))}
Obligations: {len(legal_data.get('obligations', []))}
Jurisdiction: {legal_data.get('jurisdiction', 'Not specified')}

Key Clauses:
{self._format_list(legal_data.get('clauses_identified', []), 'type', 'summary')}

RISK ASSESSMENT:
Overall Risk Score: {risk_data.get('overall_risk_score', 0)}/10
Critical Risks: {len(risk_data.get('critical_risks', []))}

Risk Categories:
{json.dumps(risk_data.get('risk_categories', {}), indent=2)}

Critical Risks:
{self._format_list(risk_data.get('critical_risks', []), 'category', 'description')}

Recommendations:
{chr(10).join([f"- {rec}" for rec in risk_data.get('recommendations', [])[:5]])}

USER INSTRUCTIONS: {state.get('user_instructions', 'None')}
PRIORITY: {state.get('priority_level', 'medium')}
"""
        return context

    def _format_list(self, items: list, key1: str, key2: str) -> str:
        """Format a list of dicts for display"""
        if not items:
            return "None identified"

        formatted = []
        for i, item in enumerate(items[:5], 1):
            formatted.append(
                f"  {i}. {item.get(key1, 'N/A')}: {item.get(key2, 'N/A')}")
        return "\n".join(formatted)

    def validate_input(self, state: ContractState) -> bool:
        """Coordinator can always process"""
        return True
