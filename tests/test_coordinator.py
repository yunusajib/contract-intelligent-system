"""
Test script for Coordinator Agent with Crew.AI
Run this to verify Step 2 setup is working correctly
"""

from loguru import logger
from core.state import (
    create_initial_state,
    ProcessingStatus,
    ParserOutput,
    LegalAnalysis,
    RiskAssessment
)
from agents.coordinator_agent import CoordinatorAgent
from dotenv import load_dotenv
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()


async def test_coordinator_synthesis():
    """
    Test the coordinator's ability to synthesize a final report
    from mock agent outputs using Crew.AI
    """
    logger.info("=" * 80)
    logger.info("TESTING COORDINATOR AGENT (CREW.AI) - SYNTHESIS CAPABILITY")
    logger.info("=" * 80)

    # Create initial state
    state = create_initial_state(
        contract_id="TEST-001",
        filename="test_nda.pdf",
        file_size=125000,
        user_instructions="Focus on confidentiality terms and liability limits",
        priority_level="high"
    )

    # Mock Parser Output
    state["parser_output"] = ParserOutput(
        raw_text="Sample NDA text with confidential information clauses...",
        structured_sections={
            "Definitions": "Party A, Party B, Confidential Information...",
            "Obligations": "Each party agrees to maintain confidentiality...",
            "Term": "This agreement shall remain in effect for 2 years...",
            "Termination": "Either party may terminate with 30 days notice..."
        },
        metadata={
            "num_pages": 8,
            "word_count": 3500,
            "language": "en"
        },
        extraction_confidence=0.95
    )

    # Mock Legal Analysis
    state["legal_analysis"] = LegalAnalysis(
        key_terms=[
            {
                "term": "Confidential Information",
                "definition": "Any non-public business information",
                "importance": "high"
            },
            {
                "term": "Permitted Disclosure",
                "definition": "Disclosure required by law",
                "importance": "medium"
            }
        ],
        obligations=[
            {
                "party": "Party A",
                "description": "Maintain confidentiality of all disclosed information",
                "deadline": "Throughout agreement term"
            },
            {
                "party": "Party B",
                "description": "Return or destroy confidential materials upon termination",
                "deadline": "Within 30 days of termination"
            }
        ],
        parties_involved=["TechCorp Inc.", "DataSystems LLC"],
        contract_type="Non-Disclosure Agreement (NDA)",
        jurisdiction="Delaware",
        effective_date="2024-01-15",
        termination_date="2026-01-15",
        clauses_identified=[
            {
                "type": "Confidentiality",
                "summary": "Standard confidentiality obligations with broad definition",
                "risk_level": "low"
            },
            {
                "type": "Indemnification",
                "summary": "Limited indemnification for breach of confidentiality",
                "risk_level": "medium"
            },
            {
                "type": "Liability Cap",
                "summary": "Liability capped at $500,000",
                "risk_level": "medium"
            }
        ]
    )

    # Mock Risk Assessment
    state["risk_assessment"] = RiskAssessment(
        overall_risk_score=5.5,
        risk_categories={
            "financial": {
                "score": 6.0,
                "description": "Moderate financial exposure due to liability cap"
            },
            "legal": {
                "score": 4.5,
                "description": "Standard NDA terms with acceptable legal risk"
            },
            "operational": {
                "score": 6.5,
                "description": "Broad definition of confidential info may restrict operations"
            }
        },
        critical_risks=[
            {
                "category": "Confidentiality",
                "severity": "High",
                "description": "Definition of 'Confidential Information' is overly broad",
                "impact": "Could restrict legitimate business activities"
            },
            {
                "category": "Financial",
                "severity": "Medium",
                "description": "Liability cap may not cover potential breach damages",
                "impact": "Exposure up to $500K"
            }
        ],
        recommendations=[
            "Narrow the definition of Confidential Information to exclude publicly available data",
            "Negotiate higher liability cap or unlimited liability for willful breach",
            "Add carve-out for independent development",
            "Include clear procedures for returning confidential materials"
        ],
        compliance_issues=[
            {
                "issue": "GDPR Considerations",
                "severity": "Low",
                "description": "No specific mention of data protection regulations"
            }
        ]
    )

    # Initialize Coordinator Agent
    logger.info("Initializing Coordinator Agent with Crew.AI...")
    try:
        coordinator = CoordinatorAgent()
        logger.success("✓ Coordinator Agent initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize coordinator: {str(e)}")
        logger.info(
            "\n💡 Make sure you have set OPENAI_API_KEY in your .env file")
        return False

    # Process and synthesize
    logger.info("Starting synthesis process...")
    try:
        updated_state = await coordinator.synthesize_report(state)

        logger.success("✓ Synthesis completed successfully!")
        logger.info(f"Status: {updated_state['status'].value}")

        # Display results
        if updated_state["final_report"]:
            report = updated_state["final_report"]

            logger.info("\n" + "=" * 80)
            logger.info("FINAL REPORT SUMMARY")
            logger.info("=" * 80)

            logger.info(f"\n📊 Risk Matrix:")
            for risk_type, level in report["risk_matrix"].items():
                logger.info(f"  - {risk_type}: {level}")

            logger.info(
                f"\n🎯 Approval Recommendation: {report['approval_recommendation']}")

            logger.info(f"\n📝 Action Items ({len(report['action_items'])}):")
            for i, item in enumerate(report["action_items"], 1):
                logger.info(f"  {i}. {item}")

            logger.info(f"\n📄 Executive Summary:")
            summary = report['executive_summary'][:300]
            logger.info(
                f"  {summary}{'...' if len(report['executive_summary']) > 300 else ''}")

            logger.success(
                "\n✓ All tests passed! Coordinator Agent with Crew.AI is working correctly.")

        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {str(e)}")
        logger.exception(e)
        logger.info("\n💡 Common issues:")
        logger.info("  - Make sure OPENAI_API_KEY is set in .env")
        logger.info("  - Verify you have API credits available")
        logger.info("  - Check your internet connection")
        return False


async def test_coordinator_initialization():
    """Test basic coordinator initialization"""
    logger.info("Testing Coordinator initialization with Crew.AI...")

    try:
        coordinator = CoordinatorAgent()
        logger.success("✓ Coordinator Agent initialized successfully")
        logger.info(f"  - Agent Type: {coordinator.agent_type.value}")
        logger.info(f"  - Model: {coordinator.model}")
        logger.info(f"  - Role: {coordinator.get_role()}")
        logger.info(f"  - Framework: Crew.AI")
        return True
    except Exception as e:
        logger.error(f"✗ Initialization failed: {str(e)}")
        logger.info("\n💡 Make sure OPENAI_API_KEY is set in your .env file")
        return False


async def main():
    """Run all tests"""
    logger.info("\n🚀 Starting Coordinator Agent Tests (Crew.AI Framework)\n")

    # Test 1: Initialization
    test1_passed = await test_coordinator_initialization()

    # Test 2: Synthesis
    if test1_passed:
        logger.info("\n")
        test2_passed = await test_coordinator_synthesis()
    else:
        logger.error("Skipping synthesis test due to initialization failure")
        test2_passed = False

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(
        f"Initialization Test: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    logger.info(
        f"Synthesis Test: {'✓ PASSED' if test2_passed else '✗ FAILED'}")

    if test1_passed and test2_passed:
        logger.success(
            "\n🎉 All tests passed! Crew.AI setup complete. Ready for Step 3.")
    else:
        logger.error("\n❌ Some tests failed. Please check the errors above.")
        logger.info("\n📋 Quick Setup Checklist:")
        logger.info("  1. Create .env file with OPENAI_API_KEY=your_key")
        logger.info(
            "  2. Run: pip install crewai crewai-tools langchain-openai")
        logger.info("  3. Verify API key works: echo $OPENAI_API_KEY")


if __name__ == "__main__":
    asyncio.run(main())
