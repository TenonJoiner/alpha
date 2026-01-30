"""
Alpha - CLI Interface

Command-line interface for Alpha AI Assistant.
"""

import asyncio
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.status import Status

from alpha.core.engine import AlphaEngine
from alpha.utils.config import load_config
from alpha.llm.service import LLMService, Message
from alpha.tools.registry import create_default_registry
from alpha.events.bus import EventType
from alpha.skills.registry import SkillRegistry
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.installer import SkillInstaller
from alpha.skills.executor import SkillExecutor
from alpha.skills import preinstall_builtin_skills
from alpha.skills.auto_manager import AutoSkillManager

# Vector Memory imports (optional - graceful fallback if unavailable)
try:
    from alpha.vector_memory import (
        VectorStore,
        EmbeddingService,
        KnowledgeBase,
        ContextRetriever
    )
    from alpha.vector_memory.embeddings import ChromaEmbeddingFunction
    VECTOR_MEMORY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Vector Memory not available: {e}")
    VECTOR_MEMORY_AVAILABLE = False

logger = logging.getLogger(__name__)
console = Console()


class CLI:
    """
    Command-line interface for Alpha.

    Features:
    - Interactive chat
    - Command execution
    - Status display
    """

    def __init__(self, engine: AlphaEngine, llm_service: LLMService, tool_registry, skill_executor: SkillExecutor = None, auto_skill_manager: AutoSkillManager = None, config=None):
        self.engine = engine
        self.llm_service = llm_service
        self.tool_registry = tool_registry
        self.skill_executor = skill_executor
        self.auto_skill_manager = auto_skill_manager
        self.conversation_history: list[Message] = []
        self.config = config

        # Initialize Vector Memory (optional, with graceful fallback)
        self.vector_memory_enabled = False
        self.vector_store = None
        self.embedding_service = None
        self.knowledge_base = None
        self.context_retriever = None

        if VECTOR_MEMORY_AVAILABLE and config and hasattr(config, 'vector_memory'):
            self._initialize_vector_memory(config.vector_memory)


        # System prompt
        self.system_prompt = """You are Alpha, a Personal Super AI Assistant.

CORE PHILOSOPHY:
- Your mission is to "not merely assist but amaze and intrigue humans at every interaction"
- Turn vague requests into completed tasks with precision and initiative
- NEVER give up on a task - always try multiple approaches until successful
- When one method fails, automatically try alternative solutions without asking the user

You have access to the following tools:
{tools}

You also have access to Agent Skills (dynamic capabilities):
{skills}

IMPORTANT INSTRUCTIONS:

1. When you need to use tools, respond in this format:

   TOOL: <tool_name>
   PARAMS: <json_or_yaml_params>

   When you need to use skills, respond in this format:

   SKILL: <skill_name>
   PARAMS: <json_or_yaml_params>

   You can use either single-line JSON or multi-line YAML for PARAMS:

   Single-line: PARAMS: {{"url": "https://example.com", "method": "GET"}}
   Multi-line:  PARAMS:
                  url: "https://example.com"
                  method: "GET"

   You can call multiple tools/skills in one response.

   CRITICAL: Tool/Skill call lines (TOOL:/SKILL: and PARAMS:) are automatically hidden from users.
   Users NEVER see these technical details - they only see your natural language messages.

2. SKILLS vs TOOLS:
   - Tools: Built-in capabilities (shell, file, search, http, datetime, calculator)
   - Skills: Dynamic capabilities that can be auto-discovered and installed
   - If a skill is not installed, Alpha will try to auto-discover and install it

3. When you receive tool/skill results (marked as "Tool execution results:"),
   DO NOT call more tools. Instead, provide a clear, natural language answer
   to the user based on the results.

4. NEVER GIVE UP PRINCIPLE:
   When a tool fails, YOU MUST automatically try alternative approaches. NEVER simply tell the user
   "I cannot do this" or "service is unavailable" without exhausting all options.

   MANDATORY MULTI-APPROACH STRATEGY:

   a) For Stock Market / Real-time Financial Data:
      Approach 1: Try Search tool first
      Approach 2: If Search fails → Use HTTP with https://hq.sinajs.cn/list=sh000001,sz399001,sz399006
      Approach 3: If HTTP fails → Try alternative API: https://qt.gtimg.cn/q=sh000001,sz399001
      Approach 4: If all APIs fail → Use HTTP to scrape from https://finance.sina.com.cn
      ONLY give up after trying ALL approaches

   b) For Weather:
      Approach 1: Try Search tool first
      Approach 2: If Search fails → Use HTTP with https://wttr.in/{{city}}?format=j1&lang=zh-cn
      Approach 3: If wttr.in fails → Try http://www.weather.com.cn/data/cityinfo/{{city_code}}.html
      Approach 4: If all fail → Try scraping from weather websites

   c) For News / Current Events:
      Approach 1: Try Search tool
      Approach 2: If Search fails → Use HTTP to fetch RSS feeds
      Approach 3: If RSS fails → Try scraping news websites directly

   d) For General Information:
      Approach 1: Try Search tool
      Approach 2: If Search fails → Try HTTP to query knowledge APIs
      Approach 3: If APIs fail → Use reasoning and existing knowledge
      NEVER just say "search is unavailable" - always provide the best answer you can

   EXECUTION RULE: After each failed attempt, immediately inform the user "Approach X failed, trying Approach Y..."
   This shows persistence and builds confidence.

5. TOOL USAGE STRATEGIES:
   - Always start with the most direct approach
   - If it fails, automatically move to alternative methods
   - Combine multiple tools if needed (e.g., HTTP + DateTime for time-sensitive data)
   - Show determination: "Let me try another way..." "I'll use a different method..."

6. Be concise, proactive, and solution-oriented. Your goal is to COMPLETE the task, not just explain why it failed."""

    async def start(self):
        """Start interactive CLI."""
        console.print(Panel.fit(
            "[bold blue]Alpha AI Assistant[/bold blue]\n"
            "Type 'help' for commands, 'quit' to exit",
            border_style="blue"
        ))

        # Display available tools
        tools = self.tool_registry.list_tools()
        tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])

        # Display available skills
        skills_desc = "No skills installed yet. Skills can be auto-discovered and installed on-demand."
        if self.skill_executor:
            skills = self.skill_executor.list_installed_skills()
            if skills:
                skills_desc = "\n".join([f"- {s['name']} (v{s['version']}): {s['description']}" for s in skills])

        # Initialize system message
        system_msg = self.system_prompt.format(tools=tools_desc, skills=skills_desc)
        self.conversation_history.append(Message(role="system", content=system_msg))

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['quit', 'exit']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if user_input.lower() == 'help':
                    self._show_help()
                    continue

                if user_input.lower() == 'status':
                    await self._show_status()
                    continue

                if user_input.lower() == 'clear':
                    self.conversation_history = [self.conversation_history[0]]
                    console.print("[yellow]Conversation cleared[/yellow]")
                    continue

                if user_input.lower() == 'skills':
                    await self._show_skills()
                    continue

                if user_input.lower().startswith('search skill '):
                    query = user_input[13:].strip()
                    await self._search_skills(query)
                    continue

                # Process user message
                await self._process_message(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                logger.error(f"CLI error: {e}", exc_info=True)

    async def _process_message(self, user_input: str):
        """Process user message and generate response."""
        # Add user message to history
        user_msg = Message(role="user", content=user_input)
        self.conversation_history.append(user_msg)

        # Add to vector memory for future retrieval
        if self.vector_memory_enabled:
            await self._add_to_vector_memory(user_input, role="user")

        # Retrieve relevant context from previous conversations
        if self.vector_memory_enabled:
            relevant_context = await self._retrieve_relevant_context(user_input, n_results=3)
            if relevant_context:
                self._inject_context_into_conversation(relevant_context)

        # Record in memory
        await self.engine.memory_manager.add_conversation(
            role="user",
            content=user_input
        )

        # Auto-skill: Try to match and load relevant skill
        if self.auto_skill_manager:
            try:
                console.print("[dim]Analyzing query for relevant skills...[/dim]")
                skill_result = await self.auto_skill_manager.process_query(user_input)

                if skill_result:
                    skill_name = skill_result['skill_name']
                    skill_context = skill_result['context']
                    skill_score = skill_result['score']

                    # Show user what skill is being used
                    console.print(f"[cyan]🎯 Using skill:[/cyan] [bold]{skill_name}[/bold] (relevance: {skill_score:.1f}/10)")

                    # Add skill context to conversation history
                    skill_msg = Message(role="system", content=skill_context)
                    self.conversation_history.append(skill_msg)

                    logger.info(f"Auto-loaded skill: {skill_name} (score: {skill_score})")
                else:
                    logger.debug("No relevant skill found for query")

            except Exception as e:
                logger.warning(f"Auto-skill matching failed: {e}")
                # Continue without skill context

        # Tool execution loop - continue until no more tool calls
        max_iterations = 3  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Generate response (may contain tool calls)
            try:
                # Show thinking indicator for first iteration
                if iteration == 1:
                    console.print("[dim]Thinking...[/dim]")

                response_text = ""
                async for chunk in self.llm_service.stream_complete(
                    self.conversation_history
                ):
                    response_text += chunk

                # Check if response contains tool calls
                tool_calls = self._parse_tool_calls(response_text)

                if tool_calls:
                    # Extract user-facing message (remove TOOL: and PARAMS: lines)
                    user_message = self._extract_user_message(response_text)

                    # Display user-facing message if any
                    if user_message.strip() and iteration == 1:
                        console.print(f"\n[bold blue]Alpha[/bold blue]: {user_message}")

                    # Add assistant message with tool calls to history
                    assistant_msg = Message(role="assistant", content=response_text)
                    self.conversation_history.append(assistant_msg)

                    # Execute tools and get results
                    tool_results = await self._execute_tools(tool_calls)

                    # Add tool results to conversation with clear instruction
                    tool_results_text = self._format_tool_results(tool_results)
                    tool_msg = Message(
                        role="user",
                        content=f"Tool execution results:\n{tool_results_text}\n\nBased on these results, provide a clear answer to the user. DO NOT call more tools."
                    )
                    self.conversation_history.append(tool_msg)

                    # Continue to next iteration to get final response
                    continue

                else:
                    # No tool calls - this is the final response
                    if iteration == 1:
                        # First response with no tools
                        console.print(f"\n[bold blue]Alpha[/bold blue]: {response_text}")
                    else:
                        # Response after tool execution - print directly to avoid Rich library bug
                        if response_text.strip():
                            console.print(f"\n[bold blue]Alpha[/bold blue]: {response_text}")
                        else:
                            console.print(f"\n[bold blue]Alpha[/bold blue]: [yellow](No response generated)[/yellow]")

                    # Add assistant response to history
                    assistant_msg = Message(role="assistant", content=response_text)
                    self.conversation_history.append(assistant_msg)

                    # Add to vector memory
                    if self.vector_memory_enabled:
                        await self._add_to_vector_memory(response_text, role="assistant")

                    # Record in memory
                    await self.engine.memory_manager.add_conversation(
                        role="assistant",
                        content=response_text
                    )

                    # Done - exit loop
                    break

            except Exception as e:
                console.print(f"\n[bold red]Error generating response:[/bold red] {e}")
                logger.error(f"Response generation error: {e}", exc_info=True)
                break

        if iteration >= max_iterations:
            console.print(f"\n[yellow]Warning: Maximum tool iterations reached[/yellow]")

    def _initialize_vector_memory(self, vm_config):
        """
        Initialize Vector Memory system.

        Args:
            vm_config: VectorMemoryConfig instance
        """
        if not vm_config or not vm_config.enabled:
            logger.info("Vector Memory disabled in configuration")
            return

        try:
            # Initialize embedding service
            self.embedding_service = EmbeddingService(
                provider=vm_config.provider or 'local',
                model=vm_config.model
            )

            # Create embedding function for ChromaDB
            embedding_function = ChromaEmbeddingFunction(self.embedding_service)

            # Initialize vector store
            self.vector_store = VectorStore(
                persist_directory=vm_config.persist_directory,
                embedding_function=embedding_function
            )

            # Initialize knowledge base
            self.knowledge_base = KnowledgeBase(
                vector_store=self.vector_store,
                embedding_service=self.embedding_service
            )

            # Initialize context retriever
            self.context_retriever = ContextRetriever(
                vector_store=self.vector_store,
                embedding_service=self.embedding_service,
                max_context_tokens=vm_config.max_context_tokens
            )

            self.vector_memory_enabled = True
            console.print("[green]✓ Vector Memory initialized[/green]")
            logger.info("Vector Memory initialized successfully")

        except Exception as e:
            logger.warning(f"Vector Memory initialization failed: {e}")
            logger.info("Continuing without semantic search capabilities")
            self.vector_memory_enabled = False

    async def _add_to_vector_memory(self, content: str, role: str):
        """
        Add message to vector memory.

        Args:
            content: Message content
            role: Message role (user/assistant/system)
        """
        if not self.vector_memory_enabled:
            return

        try:
            self.context_retriever.add_conversation(
                role=role,
                content=content,
                metadata={'timestamp': str(asyncio.get_event_loop().time())}
            )
        except Exception as e:
            logger.error(f"Failed to add to vector memory: {e}")

    async def _retrieve_relevant_context(self, query: str, n_results: int = 3) -> str:
        """
        Retrieve relevant context for query.

        Args:
            query: Search query
            n_results: Number of results to retrieve

        Returns:
            Formatted context string or None
        """
        if not self.vector_memory_enabled:
            return None

        try:
            context = self.context_retriever.build_context(
                query=query,
                n_conversations=n_results,
                n_knowledge=2
            )
            return context if context.strip() else None
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return None

    def _inject_context_into_conversation(self, context: str):
        """
        Inject retrieved context into conversation history.

        Args:
            context: Context to inject
        """
        if not context or not context.strip():
            return

        context_msg = Message(
            role="system",
            content=f"Relevant context from previous conversations:\n{context}"
        )
        # Insert before last user message (if exists)
        if self.conversation_history:
            self.conversation_history.insert(-1, context_msg)
        else:
            self.conversation_history.append(context_msg)

    def _parse_tool_calls(self, response: str) -> list:
        """Parse tool and skill calls from response."""
        import json
        import yaml

        calls = []
        lines = response.split('\n')
        current_call = None
        current_type = None  # 'tool' or 'skill'
        current_params = None
        params_lines = []
        in_params_block = False

        for i, line in enumerate(lines):
            if line.startswith("TOOL:"):
                # Save previous call if exists
                if current_call and current_params and current_type:
                    calls.append({"type": current_type, "name": current_call, "params": current_params})

                current_call = line.replace("TOOL:", "").strip()
                current_type = "tool"
                current_params = None
                params_lines = []
                in_params_block = False

            elif line.startswith("SKILL:"):
                # Save previous call if exists
                if current_call and current_params and current_type:
                    calls.append({"type": current_type, "name": current_call, "params": current_params})

                current_call = line.replace("SKILL:", "").strip()
                current_type = "skill"
                current_params = None
                params_lines = []
                in_params_block = False

            elif line.startswith("PARAMS:"):
                in_params_block = True
                params_str = line.replace("PARAMS:", "").strip()

                # Try to parse inline JSON
                if params_str:
                    try:
                        current_params = json.loads(params_str)
                        in_params_block = False
                    except json.JSONDecodeError:
                        # Not valid JSON, start collecting multi-line params
                        params_lines = [params_str] if params_str else []
                else:
                    # Empty PARAMS: line, expect multi-line YAML format
                    params_lines = []

            elif in_params_block:
                # Check if line is indented (part of params block)
                if line and (line.startswith('  ') or line.startswith('\t')):
                    params_lines.append(line)
                else:
                    # End of params block, parse collected lines
                    if params_lines:
                        params_text = '\n'.join(params_lines)
                        try:
                            # Try YAML first (more flexible)
                            current_params = yaml.safe_load(params_text)
                        except:
                            try:
                                # Try JSON
                                current_params = json.loads(params_text)
                            except:
                                logger.warning(f"Failed to parse params: {params_text}")
                                current_params = None
                    in_params_block = False
                    params_lines = []

        # Handle last call
        if current_call and current_type:
            if in_params_block and params_lines:
                # Parse remaining params
                params_text = '\n'.join(params_lines)
                try:
                    current_params = yaml.safe_load(params_text)
                except:
                    try:
                        current_params = json.loads(params_text)
                    except:
                        logger.warning(f"Failed to parse params: {params_text}")
                        current_params = None

            if current_params:
                calls.append({"type": current_type, "name": current_call, "params": current_params})

        return calls

    def _extract_user_message(self, response: str) -> str:
        """Extract user-facing message by removing tool and skill call lines."""
        lines = response.split('\n')
        user_lines = []
        in_params_block = False

        for line in lines:
            if line.startswith("TOOL:") or line.startswith("SKILL:"):
                # Skip TOOL:/SKILL: line
                continue
            elif line.startswith("PARAMS:"):
                # Skip PARAMS: line and start params block
                in_params_block = True
                continue
            elif in_params_block:
                # Check if line is indented (part of params block)
                if line and (line.startswith('  ') or line.startswith('\t')):
                    # Skip indented params lines
                    continue
                else:
                    # End of params block
                    in_params_block = False
                    # Don't skip this line, it's user content

            # Add non-tool/skill-call lines
            user_lines.append(line)

        return '\n'.join(user_lines).strip()

    async def _execute_tools(self, tool_calls: list) -> list:
        """Execute multiple tool/skill calls."""
        results = []

        for call in tool_calls:
            call_type = call.get("type", "tool")  # Default to tool for backward compatibility
            call_name = call.get("name") or call.get("tool")  # Support both formats
            params = call["params"]

            if call_type == "skill":
                # Execute skill
                logger.info(f"Executing skill: {call_name} with params: {params}")

                if not self.skill_executor:
                    results.append({
                        "type": "skill",
                        "name": call_name,
                        "success": False,
                        "output": None,
                        "error": "Skill executor not available"
                    })
                    continue

                with console.status(f"[cyan]Executing skill: {call_name}...[/cyan]"):
                    result = await self.skill_executor.execute(call_name, **params)

                results.append({
                    "type": "skill",
                    "name": call_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                })

                # Publish event
                await self.engine.event_bus.publish_event(
                    EventType.TOOL_EXECUTED,  # Reuse TOOL_EXECUTED event for now
                    {
                        "type": "skill",
                        "skill": call_name,
                        "params": params,
                        "success": result.success
                    }
                )

            else:
                # Execute tool
                logger.info(f"Executing tool: {call_name} with params: {params}")

                with console.status(f"[cyan]Executing tool: {call_name}...[/cyan]"):
                    result = await self.tool_registry.execute_tool(call_name, **params)

                results.append({
                    "type": "tool",
                    "name": call_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                })

                # Publish event
                await self.engine.event_bus.publish_event(
                    EventType.TOOL_EXECUTED,
                    {
                        "type": "tool",
                        "tool": call_name,
                        "params": params,
                        "success": result.success
                    }
                )

        return results

    def _format_tool_results(self, results: list) -> str:
        """Format tool/skill results for LLM."""
        formatted = []

        for result in results:
            result_type = result.get("type", "tool")
            result_name = result.get("name") or result.get("tool")  # Support both formats

            if result["success"]:
                if result_type == "skill":
                    formatted.append(f"Skill '{result_name}' succeeded:")
                else:
                    formatted.append(f"Tool '{result_name}' succeeded:")
                formatted.append(f"{result['output']}")
            else:
                if result_type == "skill":
                    formatted.append(f"Skill '{result_name}' failed:")
                else:
                    formatted.append(f"Tool '{result_name}' failed:")
                formatted.append(f"Error: {result['error']}")

        return '\n\n'.join(formatted)

    async def _handle_tool_calls(self, response: str):
        """Parse and execute tool calls from response."""
        # This method is now deprecated, kept for backwards compatibility
        pass

    def _show_help(self):
        """Show help message."""
        help_text = """
# Commands

- **help**: Show this help message
- **status**: Show system status
- **skills**: List installed skills
- **search skill <query>**: Search for available skills
- **clear**: Clear conversation history
- **quit/exit**: Exit Alpha

# Usage

Just type your question or request, and Alpha will help you.
Alpha has access to:
- **Tools**: Built-in capabilities (shell, file, search, http, datetime, calculator)
- **Skills**: Dynamic capabilities that can be auto-discovered and installed on-demand
        """
        console.print(Markdown(help_text))

    async def _show_skills(self):
        """Show installed skills."""
        # Get builtin skills from SkillRegistry
        builtin_skills = []
        if self.skill_executor:
            builtin_skills = self.skill_executor.list_installed_skills()

        # Get auto-skill system skills
        auto_skills = []
        if self.auto_skill_manager:
            auto_skills = self.auto_skill_manager.list_installed_skills()

        # Build output
        skills_sections = []

        # Builtin skills section
        if builtin_skills:
            builtin_list = "\n".join([
                f"- **{s['name']}** (v{s['version']}) - {s['description']}\n  Category: {s['category']}, Author: {s['author']}"
                for s in builtin_skills
            ])
            skills_sections.append(f"""## Builtin Skills (Python-based)

{builtin_list}
""")

        # Auto-skill system skills section
        if auto_skills:
            auto_list = "\n".join([
                f"- **{s['name']}** - {s['description']}"
                for s in auto_skills
            ])
            skills_sections.append(f"""## Downloaded Skills (SKILL.md format, from skills.sh)

Total: {len(auto_skills)} skills

{auto_list}

These skills are automatically loaded when relevant to your queries.
""")

        # Final output
        if not skills_sections:
            skills_text = """
# Installed Skills

No skills installed yet.

Skills can be auto-discovered and installed on-demand when you use them.
Use `search skill <query>` to find available skills.
            """
        else:
            skills_text = f"""
# Installed Skills

{"".join(skills_sections)}

**Tip**: Skills are automatically selected based on your queries. You don't need to manually invoke them.
            """

        console.print(Markdown(skills_text))

    async def _search_skills(self, query: str):
        """Search for available skills."""
        if not self.skill_executor:
            console.print("[yellow]Skill system not available[/yellow]")
            return

        console.print(f"[blue]Searching for skills: {query}...[/blue]")

        try:
            results = await self.skill_executor.discover_skills(query)

            if not results:
                console.print(f"[yellow]No skills found matching '{query}'[/yellow]")
                return

            results_list = "\n".join([
                f"- **{s.name}** (v{s.version}) - {s.description}\n  Category: {s.category}, Author: {s.author}"
                for s in results
            ])

            results_text = f"""
# Available Skills

{results_list}

These skills can be automatically installed when you use them.
            """

            console.print(Markdown(results_text))

        except Exception as e:
            console.print(f"[bold red]Error searching skills:[/bold red] {e}")
            logger.error(f"Skill search error: {e}", exc_info=True)

    async def _show_status(self):
        """Show system status."""
        health = await self.engine.health_check()

        status_text = f"""
# System Status

- **Status**: {health['status']}
- **Uptime**: {health['uptime']}
- **Tasks**: {health['tasks']}
- **Memory**: {health['memory']}
        """
        console.print(Markdown(status_text))


async def run_cli():
    """Run CLI interface."""
    # Setup logging
    Path('logs').mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/alpha.log')
        ]
    )

    try:
        # Load configuration
        config = load_config('config.yaml')

        # Create engine
        engine = AlphaEngine(config)
        await engine.startup()

        # Create LLM service
        llm_service = LLMService.from_config(config.llm)

        # Create tool registry
        tool_registry = create_default_registry()

        # Create skill system
        skill_config = config.dict().get('skills', {}) if hasattr(config, 'dict') else {}
        skill_registry = SkillRegistry()
        skill_marketplace = SkillMarketplace(config=skill_config)
        skill_installer = SkillInstaller()

        # Preinstall builtin skills
        console.print("[blue]Loading builtin skills...[/blue]")
        installed_count = await preinstall_builtin_skills(skill_registry, skill_installer)
        if installed_count > 0:
            console.print(f"[green]✓[/green] Loaded {installed_count} builtin skills")

        # Load external skill sources
        console.print("[blue]Connecting to skill sources...[/blue]")
        if skill_config.get('sources'):
            console.print(f"[dim]Found {len(skill_config['sources'])} skill sources[/dim]")

        skill_executor = SkillExecutor(
            registry=skill_registry,
            marketplace=skill_marketplace,
            installer=skill_installer,
            auto_install=skill_config.get('auto_install', True)
        )

        # Create auto-skill manager
        auto_skill_config = skill_config.get('auto_skill', {})
        auto_skill_enabled = auto_skill_config.get('enabled', True)

        auto_skill_manager = None
        if auto_skill_enabled:
            console.print("[blue]Initializing auto-skill system...[/blue]")
            auto_skill_manager = AutoSkillManager(
                auto_install=auto_skill_config.get('auto_install', True),
                auto_load=auto_skill_config.get('auto_load', True)
            )
            # Initialize (load skills cache)
            await auto_skill_manager.initialize()
            console.print("[green]✓[/green] Auto-skill system ready")

        # Create and start CLI (with config for Vector Memory)
        cli = CLI(engine, llm_service, tool_registry, skill_executor, auto_skill_manager, config)

        # Start engine in background
        engine_task = asyncio.create_task(engine.run())

        # Run CLI
        await cli.start()

        # Shutdown
        await engine.shutdown()
        await engine_task

    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_cli())
