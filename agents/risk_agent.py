"""
Risk Assessment Agent
Evaluates contract risks and provides recommendations using Crew.AI
"""

from typing import Dict, Any
from crewai import Agent, Crew, Process
from loguru import logger
import json
import re

from core.base_agent import BaseContractAgent
from core.state import (
    ContractState, AgentType, MessageType,
    ProcessingStatus, RiskAssessment
)


class RiskAgent(BaseContractAgent):
    """
    Risk Agent specializes in:
    - Scoring overall contract risk (0-10 scale)
    - Identifying critical risks by category
    - Assessing compliance issues
    - Providing actionable recommendations
    - Evaluating financial, legal, and operational risks
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.RISK,
            model="gpt-4-turbo-preview"
        )

    def get_role(self) -> str:
        return "Senior Risk Management Specialist"

    def get_goal(self) -> str:
        return "Assess all contract risks, identify critical issues, evaluate compliance concerns, and provide clear recommendations to mitigate risks"

    def get_backstory(self) -> str:
        return """You are a veteran risk management specialist with 20+ years of experience in corporate 
        risk assessment, specializing in contract and legal risk. You have extensive experience in 
        financial services, technology, and healthcare industries. You've seen countless contracts go 
        wrong and have developed a keen eye for identifying potential problems before they materialize. 
        Your risk assessments have saved companies millions in avoided losses. You understand financial 
        risk (liability caps, indemnification limits), legal risk (jurisdiction issues, ambiguous terms), 
        operational risk (restrictive clauses, unworkable obligations), and compliance risk (regulatory 
        requirements, data protection). You provide clear, actionable recommendations that balance risk 
        mitigation with business practicality."""

    def _create_agent(self) -> Agent:
        """Create the Crew.AI risk agent"""
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
        Main processing: Assess contract risks
        """
        try:
            # Update status
            state = self.update_status(state, ProcessingStatus.RISK_ASSESSMENT)

            # Validate we have legal analysis
            if not state.get("legal_analysis"):
                raise ValueError("Legal analysis not available")

            legal_analysis = state["legal_analysis"]
            contract_id = state["contract_metadata"]["contract_id"]

            self.log_processing_step(
                state, f"Starting risk assessment for {contract_id}")

            # Create risk assessment task
            risk_task = self.create_task(
                description=f"""Conduct a comprehensive risk assessment of this contract:

CONTRACT TYPE: {legal_analysis['contract_type']}
PARTIES: {', '.join(legal_analysis['parties_involved'])}
JURISDICTION: {legal_analysis.get('jurisdiction', 'Not specified')}

CLAUSES IDENTIFIED:
{json.dumps(legal_analysis['clauses_identified'], indent=2)}

OBLIGATIONS:
{json.dumps(legal_analysis['obligations'], indent=2)}

KEY TERMS:
{json.dumps(legal_analysis['key_terms'], indent=2)}

Your risk assessment must include:

1. OVERALL RISK SCORE (0-10): Where 0=no risk, 10=extreme risk
2. RISK CATEGORIES: Score each category (0-10) and explain:
   - Financial Risk: Liability caps, payment terms, penalties
   - Legal Risk: Jurisdiction, ambiguous terms, enforceability
   - Operational Risk: Restrictive clauses, unworkable obligations
   - Compliance Risk: Regulatory requirements, data protection

3. CRITICAL RISKS: Identify 2-5 most serious risks with:
   - Category (Financial/Legal/Operational/Compliance)
   - Severity (Low/Medium/High/Critical)
   - Description
   - Potential impact

4. COMPLIANCE ISSUES: Any regulatory or legal compliance concerns

5. RECOMMENDATIONS: Specific, actionable steps to mitigate risks

Provide output in this JSON format:
{{
    "overall_risk_score": 5.5,
    "risk_categories": {{
        "financial": {{"score": 6.0, "description": "Explanation"}},
        "legal": {{"score": 4.5, "description": "Explanation"}},
        "operational": {{"score": 5.0, "description": "Explanation"}},
        "compliance": {{"score": 3.0, "description": "Explanation"}}
    }},
    "critical_risks": [
        {{
            "category": "Financial",
            "severity": "High",
            "description": "Risk description",
            "impact": "Potential impact",
            "mitigation": "How to address"
        }}
    ],
    "compliance_issues": [
        {{
            "issue": "Issue name",
            "severity": "Low|Medium|High",
            "description": "Details",
            "requirement": "What regulation/law"
        }}
    ],
    "recommendations": [
        "Specific action 1",
        "Specific action 2",
        "Specific action 3"
    ]
}}""",
                expected_output="JSON formatted risk assessment"
            )

            # Execute assessment
            risk_crew = Crew(
                agents=[self.agent],
                tasks=[risk_task],
                process=Process.sequential,
                verbose=False
            )

            self.log_processing_step(state, "Executing risk assessment task")
            result = risk_crew.kickoff()

            # Parse result
            risk_data = self._parse_crew_result(result)

            # Create RiskAssessment
            risk_assessment: RiskAssessment = {
                "overall_risk_score": risk_data.get("overall_risk_score", 5.0),
                "risk_categories": risk_data.get("risk_categories", {}),
                "critical_risks": risk_data.get("critical_risks", []),
                "recommendations": risk_data.get("recommendations", []),
                "compliance_issues": risk_data.get("compliance_issues", [])
            }

            # Add to state
            state["risk_assessment"] = risk_assessment

            # Send message
            state = self.send_message(
                state,
                to_agent=AgentType.COORDINATOR,
                message_type=MessageType.ANALYSIS_RESULT,
                content={
                    "overall_risk_score": risk_assessment["overall_risk_score"],
                    "critical_risks_count": len(risk_assessment["critical_risks"]),
                    "ready_for_synthesis": True
                }
            )

            self.log_processing_step(
                state,
                f"Risk assessment complete: Score {risk_assessment['overall_risk_score']}/10"
            )

            return state

        except Exception as e:
            state = self.add_error(state, f"Risk assessment failed: {str(e)}")
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
                return self._create_fallback_assessment()

        except Exception as e:
            logger.error(f"Failed to parse risk assessment result: {str(e)}")
            return self._create_fallback_assessment()

    def _create_fallback_assessment(self) -> Dict[str, Any]:
        """Create a basic assessment structure if parsing fails"""
        return {
            "overall_risk_score": 5.0,
            "risk_categories": {
                "financial": {"score": 5.0, "description": "Unable to assess"},
                "legal": {"score": 5.0, "description": "Unable to assess"},
                "operational": {"score": 5.0, "description": "Unable to assess"},
                "compliance": {"score": 5.0, "description": "Unable to assess"}
            },
            "critical_risks": [],
            "compliance_issues": [],
            "recommendations": ["Manual review recommended due to parsing issues"]
        }

    def validate_input(self, state: ContractState) -> bool:
        """Validate that we have legal analysis"""
        return state.get("legal_analysis") is not None
