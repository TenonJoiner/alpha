"""
Chat Handler - Server-side chat logic

Handles chat messages independently of UI (CLI/Web).
Extracted from CLI to enable client-server architecture.
"""

import logging
import asyncio
from typing import Optional, AsyncIterator, Dict, Any

from alpha.core.engine import AlphaEngine
from alpha.llm.service import LLMService, Message
from alpha.tools.registry import ToolRegistry
from alpha.skills.executor import SkillExecutor
from alpha.skills.auto_manager import AutoSkillManager
from alpha.skills.query_classifier import QueryClassifier
from alpha.events.bus import EventType

logger = logging.getLogger(__name__)


class ChatHandler:
    """
    Server-side chat message handler.

    Processes user messages and generates responses without UI dependencies.
    Supports streaming responses for real-time output.
    """

    def __init__(
        self,
        engine: AlphaEngine,
        llm_service: LLMService,
        tool_registry: ToolRegistry,
        skill_executor: Optional[SkillExecutor] = None,
        auto_skill_manager: Optional[AutoSkillManager] = None
    ):
        self.engine = engine
        self.llm_service = llm_service
        self.tool_registry = tool_registry
        self.skill_executor = skill_executor
        self.auto_skill_manager = auto_skill_manager

        # Session management (can be extended for multi-user)
        self.conversation_history: list[Message] = []
        self.query_classifier = QueryClassifier()

        # System prompt
        self.system_prompt = """You are Alpha, a Personal Super AI Assistant.

CORE PHILOSOPHY:
- Autonomous and proactive
- Never give up - find solutions creatively
- Efficient and cost-conscious
- Seamless intelligence - make complex tasks feel simple

CAPABILITIES:
- Execute shell commands, manage files, search web
- Schedule tasks, manage workflows
- Learn from interactions and improve continuously
- Generate and execute code when needed

COMMUNICATION:
- Concise and clear
- Ask for clarification when needed
- Provide actionable solutions
"""

    async def process_message(
        self,
        user_input: str,
        stream: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process user message and yield response chunks.

        Args:
            user_input: User's message
            stream: Whether to stream response (True) or return complete (False)

        Yields:
            Dict with type and content:
            - {"type": "status", "content": "Thinking..."}
            - {"type": "text", "content": "response chunk"}
            - {"type": "tool", "name": "shell", "status": "executing"}
            - {"type": "tool_result", "name": "shell", "output": "..."}
            - {"type": "error", "content": "error message"}
            - {"type": "done"}
        """
        try:
            # Add user message to history
            user_msg = Message(role="user", content=user_input)
            self.conversation_history.append(user_msg)

            # Record in memory
            await self.engine.memory_manager.add_conversation(
                role="user",
                content=user_input
            )

            # Query classification: check if skills needed
            should_match_skills = False
            if self.auto_skill_manager:
                query_info = self.query_classifier.classify(user_input)
                should_match_skills = query_info['needs_skill_matching']

                logger.info(f"Query classified as: {query_info['type']} "
                           f"(confidence: {query_info['confidence']:.2f}, "
                           f"needs_skills: {should_match_skills})")

            # Auto-skill matching
            if should_match_skills and self.auto_skill_manager:
                try:
                    yield {"type": "status", "content": "Analyzing task for relevant skills..."}

                    skill_result = await self.auto_skill_manager.process_query(user_input)

                    if skill_result:
                        skill_name = skill_result['skill_name']
                        skill_context = skill_result['context']
                        skill_score = skill_result['score']

                        yield {
                            "type": "skill_loaded",
                            "name": skill_name,
                            "score": skill_score
                        }

                        # Add skill context to conversation
                        skill_msg = Message(role="system", content=skill_context)
                        self.conversation_history.append(skill_msg)

                        logger.info(f"Auto-loaded skill: {skill_name} (score: {skill_score})")

                except Exception as e:
                    logger.warning(f"Auto-skill matching failed: {e}")

            # Generate response
            yield {"type": "status", "content": "Thinking..."}

            response_text = ""
            async for chunk in self.llm_service.stream_complete(
                self.conversation_history
            ):
                response_text += chunk
                if stream:
                    yield {"type": "text", "content": chunk}

            # Add assistant response to history
            assistant_msg = Message(role="assistant", content=response_text)
            self.conversation_history.append(assistant_msg)

            # Record in memory
            await self.engine.memory_manager.add_conversation(
                role="assistant",
                content=response_text
            )

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Error: {str(e)}"
            }
            yield {"type": "done"}

    async def get_conversation_history(self) -> list[Dict[str, str]]:
        """
        Get conversation history.

        Returns:
            List of messages with role and content
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ]

    async def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get chat session statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "messages_count": len(self.conversation_history),
            "user_messages": sum(1 for m in self.conversation_history if m.role == "user"),
            "assistant_messages": sum(1 for m in self.conversation_history if m.role == "assistant")
        }
