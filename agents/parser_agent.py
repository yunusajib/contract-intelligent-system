"""
Document Parser Agent
Extracts and structures text from contracts using Crew.AI
"""

from typing import Dict, Any
from crewai import Agent
from loguru import logger
import json
import re

from core.base_agent import BaseContractAgent
from core.state import (
    ContractState, AgentType, MessageType,
    ProcessingStatus, ParserOutput
)


class ParserAgent(BaseContractAgent):
    """
    Parser Agent specializes in:
    - Extracting text from documents
    - Identifying document structure and sections
    - Parsing metadata (pages, word count, etc.)
    - Assessing extraction quality/confidence
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.PARSER,
            model="gpt-4-turbo-preview"
        )

    def get_role(self) -> str:
        return "Expert Document Structure Analyst"

    def get_goal(self) -> str:
        return "Extract and structure contract text, identify key sections, and provide high-quality parsed output for downstream analysis"

    def get_backstory(self) -> str:
        return """You are an expert in document analysis with 10+ years of experience in legal document processing. 
        You excel at identifying document structure, extracting key sections, and understanding contract formatting.
        Your parsing accuracy is critical for the entire analysis pipeline. You can identify standard contract 
        sections like: Parties, Definitions, Scope, Obligations, Term & Termination, Liability, Indemnification, 
        Governing Law, and more. You understand both formal legal documents and informal agreements."""

    def _create_agent(self) -> Agent:
        """Create the Crew.AI parser agent"""
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
        Main processing: Parse the contract and structure the output
        """
        try:
            # Update status
            state = self.update_status(state, ProcessingStatus.PARSING)

            # In a real implementation, you would read the actual file here
            # For now, we'll simulate with the contract_id to load test data
            contract_id = state["contract_metadata"]["contract_id"]

            self.log_processing_step(
                state, f"Starting document parsing for {contract_id}")

            # Simulate document content (in production, read from file)
            raw_text = self._get_document_content(state)

            # Create parsing task
            parsing_task = self.create_task(
                description=f"""Analyze and parse the following contract document:

DOCUMENT TEXT:
{raw_text[:2000]}...  # Truncated for task description

Your task:
1. Identify all major sections in the document
2. Extract key information for each section
3. Assess the document structure and quality
4. Calculate extraction confidence (0.0 to 1.0)

Provide output in JSON format:
{{
    "structured_sections": {{
        "section_name": "section_content_summary",
        ...
    }},
    "metadata": {{
        "num_pages": estimate,
        "word_count": approximate count,
        "language": "en",
        "document_quality": "high|medium|low"
    }},
    "extraction_confidence": 0.0-1.0
}}""",
                expected_output="JSON formatted parsed document structure"
            )

            # Execute parsing
            from crewai import Crew, Process

            parsing_crew = Crew(
                agents=[self.agent],
                tasks=[parsing_task],
                process=Process.sequential,
                verbose=False
            )

            self.log_processing_step(state, "Executing parsing task")
            result = parsing_crew.kickoff()

            # Parse result
            parsed_data = self._parse_crew_result(result)

            # Create ParserOutput
            parser_output: ParserOutput = {
                "raw_text": raw_text,
                "structured_sections": parsed_data.get("structured_sections", {}),
                "metadata": parsed_data.get("metadata", {}),
                "extraction_confidence": parsed_data.get("extraction_confidence", 0.85)
            }

            # Add to state
            state["parser_output"] = parser_output

            # Send message
            state = self.send_message(
                state,
                to_agent=AgentType.LEGAL,
                message_type=MessageType.ANALYSIS_RESULT,
                content={
                    "sections_found": len(parser_output["structured_sections"]),
                    "confidence": parser_output["extraction_confidence"]
                }
            )

            self.log_processing_step(
                state,
                f"Parsing complete: {len(parser_output['structured_sections'])} sections identified"
            )

            return state

        except Exception as e:
            state = self.add_error(state, f"Parsing failed: {str(e)}")
            raise

    def _get_document_content(self, state: ContractState) -> str:
        """
        Get document content (simulated for now)
        In production, this would read from uploaded file
        """
        # Simulate contract content based on filename
        filename = state["contract_metadata"]["filename"]

        if "nda" in filename.lower():
            return """
NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement (the "Agreement") is entered into as of January 15, 2024, 
by and between TechCorp Inc., a Delaware corporation ("Disclosing Party"), and 
DataSystems LLC, a Delaware limited liability company ("Receiving Party").

WHEREAS, the parties wish to explore a potential business relationship;
WHEREAS, in connection with such discussions, Disclosing Party may disclose certain 
confidential and proprietary information to Receiving Party;

NOW, THEREFORE, in consideration of the mutual covenants and agreements set forth herein, 
the parties agree as follows:

1. DEFINITIONS
1.1 "Confidential Information" means any and all technical and non-technical information 
disclosed by Disclosing Party to Receiving Party, including but not limited to: patents, 
patent applications, trade secrets, proprietary information, designs, business plans, 
financial information, software, customer lists, and any other information marked as confidential.

1.2 "Permitted Disclosure" means disclosure required by law, regulation, or court order, 
provided that Receiving Party provides prompt written notice to Disclosing Party.

2. OBLIGATIONS
2.1 Receiving Party agrees to:
   a) Hold all Confidential Information in strict confidence
   b) Not disclose Confidential Information to any third party without prior written consent
   c) Use Confidential Information solely for evaluating the potential business relationship
   d) Protect Confidential Information with the same degree of care used for its own confidential information

2.2 Disclosing Party retains all right, title, and interest in and to the Confidential Information.

3. EXCLUSIONS
Confidential Information does not include information that:
   a) Is or becomes publicly available through no breach of this Agreement
   b) Was rightfully in Receiving Party's possession prior to disclosure
   c) Is independently developed by Receiving Party without use of Confidential Information
   d) Is rightfully obtained from a third party without breach of confidentiality

4. TERM AND TERMINATION
4.1 This Agreement shall commence on the effective date and continue for two (2) years.
4.2 Either party may terminate this Agreement with thirty (30) days written notice.
4.3 Upon termination, Receiving Party shall return or destroy all Confidential Information 
within thirty (30) days.

5. LIABILITY AND INDEMNIFICATION
5.1 Receiving Party agrees to indemnify and hold harmless Disclosing Party from any damages 
resulting from unauthorized disclosure or use of Confidential Information.
5.2 Liability under this Agreement shall be limited to Five Hundred Thousand Dollars ($500,000).

6. GENERAL PROVISIONS
6.1 This Agreement shall be governed by the laws of the State of Delaware.
6.2 This Agreement constitutes the entire agreement between the parties.
6.3 Any amendments must be in writing and signed by both parties.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

TechCorp Inc.                          DataSystems LLC
By: _____________________              By: _____________________
Name: John Smith                        Name: Jane Doe
Title: CEO                              Title: President
Date: January 15, 2024                  Date: January 15, 2024
"""
        else:
            return """
SERVICE AGREEMENT

This Service Agreement is made as of [Date] between [Company A] and [Company B].

1. SERVICES: Provider agrees to deliver the following services...
2. COMPENSATION: Client agrees to pay...
3. TERM: This agreement shall commence on...
4. TERMINATION: Either party may terminate...
"""

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

                # Fallback: create structure from text
                return self._create_fallback_structure(result_str)

        except Exception as e:
            logger.error(f"Failed to parse result: {str(e)}")
            return self._create_fallback_structure(str(result))

    def _create_fallback_structure(self, text: str) -> Dict[str, Any]:
        """Create a basic structure if JSON parsing fails"""
        return {
            "structured_sections": {
                "Full Text": text[:500]
            },
            "metadata": {
                "num_pages": 1,
                "word_count": len(text.split()),
                "language": "en",
                "document_quality": "medium"
            },
            "extraction_confidence": 0.7
        }

    def validate_input(self, state: ContractState) -> bool:
        """Validate that we have the necessary input"""
        return (
            state["contract_metadata"] is not None and
            state["contract_metadata"]["filename"] is not None
        )
