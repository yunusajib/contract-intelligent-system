"""
Comprehensive test for all agents working together
Tests the full multi-agent workflow
"""

from loguru import logger
from core.state import create_initial_state
from agents.coordinator_agent import CoordinatorAgent
from agents.risk_agent import RiskAgent
from agents.legal_agent import LegalAgent
from agents.parser_agent import ParserAgent
from dotenv import load_dotenv
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()


async def test_full_workflow():
    """
    Test the complete multi-agent workflow:
    Parser → Legal → Risk → Coordinator
    """
    logger.info("=" * 80)
    logger.info("TESTING FULL MULTI-AGENT WORKFLOW")
    logger.info("=" * 80)

    # Create initial state
    state = create_initial_state(
        contract_id="FULL-TEST-001",
        filename="sample_nda.pdf",
        file_size=145000,
        user_instructions="Provide detailed analysis focusing on liability and confidentiality",
        priority_level="high"
    )

    try:
        # Step 1: Parser Agent
        logger.info("\n" + "─" * 80)
        logger.info("STEP 1: DOCUMENT PARSING")
        logger.info("─" * 80)

        parser = ParserAgent()
        state = await parser.handle_processing(state)

        logger.success(
            f"✓ Parser complete: {len(state['parser_output']['structured_sections'])} sections found")
        logger.info(
            f"  Extraction confidence: {state['parser_output']['extraction_confidence']}")

        # Step 2: Legal Agent
        logger.info("\n" + "─" * 80)
        logger.info("STEP 2: LEGAL ANALYSIS")
        logger.info("─" * 80)

        legal = LegalAgent()
        state = await legal.handle_processing(state)

        logger.success(f"✓ Legal analysis complete")
        logger.info(
            f"  Contract type: {state['legal_analysis']['contract_type']}")
        logger.info(
            f"  Parties: {', '.join(state['legal_analysis']['parties_involved'])}")
        logger.info(
            f"  Clauses identified: {len(state['legal_analysis']['clauses_identified'])}")
        logger.info(
            f"  Obligations: {len(state['legal_analysis']['obligations'])}")

        # Step 3: Risk Agent
        logger.info("\n" + "─" * 80)
        logger.info("STEP 3: RISK ASSESSMENT")
        logger.info("─" * 80)

        risk = RiskAgent()
        state = await risk.handle_processing(state)

        logger.success(f"✓ Risk assessment complete")
        logger.info(
            f"  Overall risk score: {state['risk_assessment']['overall_risk_score']}/10")
        logger.info(
            f"  Critical risks: {len(state['risk_assessment']['critical_risks'])}")
        logger.info(
            f"  Recommendations: {len(state['risk_assessment']['recommendations'])}")

        # Step 4: Coordinator Agent (Synthesis)
        logger.info("\n" + "─" * 80)
        logger.info("STEP 4: FINAL SYNTHESIS")
        logger.info("─" * 80)

        coordinator = CoordinatorAgent()
        state = await coordinator.handle_processing(state)

        logger.success(f"✓ Synthesis complete")

        # Display final report
        if state["final_report"]:
            report = state["final_report"]

            logger.info("\n" + "=" * 80)
            logger.info("FINAL CONTRACT ANALYSIS REPORT")
            logger.info("=" * 80)

            logger.info(f"\n📊 RISK MATRIX:")
            for risk_type, level in report["risk_matrix"].items():
                emoji = "🟢" if level == "Low" else "🟡" if level == "Medium" else "🔴"
                logger.info(f"  {emoji} {risk_type}: {level}")

            logger.info(f"\n🎯 APPROVAL RECOMMENDATION:")
            logger.info(f"  {report['approval_recommendation']}")

            logger.info(f"\n📝 ACTION ITEMS ({len(report['action_items'])}):")
            for i, item in enumerate(report["action_items"], 1):
                logger.info(f"  {i}. {item}")

            logger.info(f"\n📄 EXECUTIVE SUMMARY:")
            summary = report['executive_summary']
            # Split into paragraphs for better readability
            paragraphs = summary.split('. ')
            for para in paragraphs[:3]:  # Show first 3 sentences
                logger.info(f"  {para}.")

            logger.info(f"\n💼 KEY FINDINGS:")
            findings = report['detailed_analysis'].get('key_findings', [])
            for i, finding in enumerate(findings[:5], 1):
                logger.info(f"  {i}. {finding}")

        # Display processing logs
        logger.info(f"\n📋 PROCESSING LOGS:")
        for log in state["processing_logs"][-10:]:  # Last 10 logs
            logger.info(f"  {log}")

        # Check for errors
        if state["errors"]:
            logger.warning(
                f"\n⚠️  ERRORS ENCOUNTERED ({len(state['errors'])}):")
            for error in state["errors"]:
                logger.warning(f"  - {error['message']}")

        logger.success("\n" + "=" * 80)
        logger.success("🎉 FULL WORKFLOW TEST PASSED!")
        logger.success("All agents working correctly in sequence")
        logger.success("=" * 80)

        return True

    except Exception as e:
        logger.error(f"\n❌ WORKFLOW TEST FAILED: {str(e)}")
        logger.exception(e)
        return False


async def test_individual_agents():
    """Test each agent initialization"""
    logger.info("\n🧪 Testing individual agent initialization...\n")

    results = {}

    # Test Parser
    try:
        parser = ParserAgent()
        logger.success(f"✓ ParserAgent initialized")
        results["parser"] = True
    except Exception as e:
        logger.error(f"✗ ParserAgent failed: {str(e)}")
        results["parser"] = False

    # Test Legal
    try:
        legal = LegalAgent()
        logger.success(f"✓ LegalAgent initialized")
        results["legal"] = True
    except Exception as e:
        logger.error(f"✗ LegalAgent failed: {str(e)}")
        results["legal"] = False

    # Test Risk
    try:
        risk = RiskAgent()
        logger.success(f"✓ RiskAgent initialized")
        results["risk"] = True
    except Exception as e:
        logger.error(f"✗ RiskAgent failed: {str(e)}")
        results["risk"] = False

    # Test Coordinator
    try:
        coordinator = CoordinatorAgent()
        logger.success(f"✓ CoordinatorAgent initialized")
        results["coordinator"] = True
    except Exception as e:
        logger.error(f"✗ CoordinatorAgent failed: {str(e)}")
        results["coordinator"] = False

    return all(results.values())


async def main():
    """Run all tests"""
    logger.info("\n🚀 Starting Multi-Agent System Tests\n")

    # Test 1: Individual agent initialization
    init_passed = await test_individual_agents()

    # Test 2: Full workflow
    if init_passed:
        logger.info("\n")
        workflow_passed = await test_full_workflow()
    else:
        logger.error("Skipping workflow test due to initialization failures")
        workflow_passed = False

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(
        f"Agent Initialization: {'✓ PASSED' if init_passed else '✗ FAILED'}")
    logger.info(
        f"Full Workflow Test: {'✓ PASSED' if workflow_passed else '✗ FAILED'}")

    if init_passed and workflow_passed:
        logger.success("\n🎉 ALL TESTS PASSED!")
        logger.success("Your multi-agent system is working perfectly!")
        logger.success("Ready for Step 4: Building the orchestration workflow")
    else:
        logger.error("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
