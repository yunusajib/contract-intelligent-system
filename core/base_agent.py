"""
Base Agent Configuration for Crew.AI
Defines agent roles, goals, and backstories
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from crewai import Agent, Task
from loguru import logger
import os

from core.state import (
    ContractState, AgentType, MessageType,
    create_agent_message, ProcessingStatus
)


class BaseContractAgent(ABC):
    """
    Abstract base class for all agents in the system
    Uses Crew.AI framework for agent management
    """

    def __init__(
        self,
        agent_type: AgentType,
        model: str = "gpt-4-turbo-preview"
    ):
        self.agent_type = agent_type
        self.model = model

        # Verify API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Create Crew.AI agent
        self.agent = self._create_agent()

        logger.info(
            f"Initialized {self.agent_type.value} agent with model {model}")

    @abstractmethod
    def _create_agent(self) -> Agent:
        """
        Create and configure the Crew.AI agent
        Must be implemented by each specialized agent

        Returns:
            Configured Crew.AI Agent
        """
        pass

    @abstractmethod
    def get_role(self) -> str:
        """Return the agent's role description"""
        pass

    @abstractmethod
    def get_goal(self) -> str:
        """Return the agent's primary goal"""
        pass

    @abstractmethod
    def get_backstory(self) -> str:
        """Return the agent's backstory/context"""
        pass

    @abstractmethod
    async def process(self, state: ContractState) -> ContractState:
        """
        Main processing method - must be implemented by each agent

        Args:
            state: Current contract state

        Returns:
            Updated contract state
        """
        pass

    def create_task(
        self,
        description: str,
        expected_output: str,
        context: Optional[List[Task]] = None
    ) -> Task:
        """
        Create a Crew.AI task for this agent

        Args:
            description: What the agent needs to do
            expected_output: What output format is expected
            context: Optional list of previous tasks for context

        Returns:
            Configured Task object
        """
        return Task(
            description=description,
            agent=self.agent,
            expected_output=expected_output,
            context=context or []
        )

    def log_processing_step(
        self,
        state: ContractState,
        message: str
    ) -> ContractState:
        """Add a log entry to the processing logs"""
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] [{self.agent_type.value}] {message}"

        state["processing_logs"].append(log_entry)
        logger.info(log_entry)

        return state

    def add_error(
        self,
        state: ContractState,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> ContractState:
        """Record an error in the state"""
        from datetime import datetime
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_type.value,
            "message": error_message,
            "details": error_details or {}
        }

        state["errors"].append(error_entry)
        logger.error(f"{self.agent_type.value} error: {error_message}")

        return state

    def send_message(
        self,
        state: ContractState,
        to_agent: Optional[AgentType],
        message_type: MessageType,
        content: Dict[str, Any]
    ) -> ContractState:
        """Send a message to another agent"""
        message = create_agent_message(
            from_agent=self.agent_type,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )

        state["messages"].append(message)

        logger.debug(
            f"Message sent: {self.agent_type.value} -> "
            f"{to_agent.value if to_agent else 'BROADCAST'} ({message_type.value})"
        )

        return state

    def update_status(
        self,
        state: ContractState,
        new_status: ProcessingStatus
    ) -> ContractState:
        """Update the processing status"""
        old_status = state["status"]
        state["status"] = new_status

        logger.info(
            f"Status updated: {old_status.value} -> {new_status.value} "
            f"by {self.agent_type.value}"
        )

        return state

    def validate_input(self, state: ContractState) -> bool:
        """
        Validate that the agent has the required input to process
        Can be overridden by specific agents
        """
        return True

    async def handle_processing(self, state: ContractState) -> ContractState:
        """
        Wrapper around process() that adds error handling and logging
        """
        try:
            # Mark current agent
            state["current_agent"] = self.agent_type

            # Log start
            self.log_processing_step(state, f"Starting processing")

            # Validate input
            if not self.validate_input(state):
                raise ValueError(
                    f"{self.agent_type.value} - Invalid input state")

            # Execute main processing
            state = await self.process(state)

            # Log completion
            self.log_processing_step(state, f"Completed processing")

            return state

        except Exception as e:
            # Record error
            state = self.add_error(
                state,
                f"Processing failed: {str(e)}",
                {"exception_type": type(e).__name__}
            )

            # Update status to failed
            state = self.update_status(state, ProcessingStatus.FAILED)

            raise
