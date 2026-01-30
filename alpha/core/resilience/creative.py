"""
Creative Solver Component

Uses LLM-powered creative problem solving when standard approaches fail.
Implements problem decomposition, workaround generation, code generation, and multi-step planning.
"""

import logging
import asyncio
import json
import re
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class SolutionType(Enum):
    """Types of creative solutions"""
    DECOMPOSITION = "decomposition"      # Break problem into sub-tasks
    WORKAROUND = "workaround"            # Alternative approach
    CODE_GENERATION = "code_generation"  # Generate custom code
    MULTI_STEP = "multi_step"            # Complex multi-step plan
    HYBRID = "hybrid"                    # Combination of approaches


@dataclass
class SubTask:
    """
    Represents a sub-task in problem decomposition.

    Attributes:
        task_id: Unique identifier
        description: What needs to be done
        dependencies: Task IDs this depends on
        estimated_complexity: 1-10 complexity score
        approach: Suggested approach to solve
        context: Additional context information
    """
    task_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_complexity: int = 5
    approach: str = ""
    context: Dict = field(default_factory=dict)


@dataclass
class WorkaroundSolution:
    """
    Alternative workaround solution.

    Attributes:
        name: Solution name
        description: What the solution does
        implementation: Step-by-step implementation
        pros: Advantages of this approach
        cons: Disadvantages and limitations
        confidence: 0.0-1.0 confidence score
        code: Generated code (if applicable)
    """
    name: str
    description: str
    implementation: List[str]
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    confidence: float = 0.5
    code: Optional[str] = None


@dataclass
class MultiStepPlan:
    """
    Multi-step execution plan.

    Attributes:
        plan_id: Unique identifier
        goal: Overall goal to achieve
        steps: Ordered list of steps
        expected_outcome: What success looks like
        fallback_options: Backup plans if steps fail
        estimated_time: Estimated execution time
    """
    plan_id: str
    goal: str
    steps: List[Dict[str, Any]]
    expected_outcome: str
    fallback_options: List[str] = field(default_factory=list)
    estimated_time: float = 0.0


@dataclass
class CreativeSolution:
    """
    Complete creative solution result.

    Attributes:
        solution_type: Type of solution generated
        confidence: Overall confidence score
        description: High-level description
        sub_tasks: Decomposed sub-tasks (if applicable)
        workarounds: Alternative workarounds
        code: Generated code (if applicable)
        plan: Multi-step plan (if applicable)
        reasoning: LLM reasoning for the solution
        metadata: Additional metadata
    """
    solution_type: SolutionType
    confidence: float
    description: str
    sub_tasks: List[SubTask] = field(default_factory=list)
    workarounds: List[WorkaroundSolution] = field(default_factory=list)
    code: Optional[str] = None
    plan: Optional[MultiStepPlan] = None
    reasoning: str = ""
    metadata: Dict = field(default_factory=dict)


class CreativeSolver:
    """
    LLM-powered creative problem solver.

    Features:
    - Problem decomposition (break complex problems into manageable sub-tasks)
    - Workaround generation (find alternative paths when standard approaches fail)
    - Code generation (create custom Python scripts)
    - Multi-step planning (orchestrate complex solution sequences)
    - Integration with LLM for creative reasoning

    Usage:
        solver = CreativeSolver(llm_service)
        solution = await solver.solve(
            problem="Cannot access API directly",
            context={"error": "403 Forbidden", "attempts": 5},
            constraints={"no_external_deps": True}
        )
    """

    def __init__(
        self,
        llm_service: Optional[Any] = None,
        provider: str = "deepseek",
        max_retries: int = 3
    ):
        """
        Initialize creative solver.

        Args:
            llm_service: Alpha LLM service instance
            provider: LLM provider to use (deepseek, openai, anthropic)
            max_retries: Maximum retries for LLM calls
        """
        self.llm_service = llm_service
        self.provider = provider
        self.max_retries = max_retries
        self.solution_history: List[CreativeSolution] = []

    async def solve(
        self,
        problem: str,
        context: Optional[Dict] = None,
        constraints: Optional[Dict] = None,
        preferred_type: Optional[SolutionType] = None
    ) -> CreativeSolution:
        """
        Generate creative solution for a problem.

        Args:
            problem: Description of the problem to solve
            context: Additional context (errors, attempts, etc.)
            constraints: Solution constraints (time, dependencies, etc.)
            preferred_type: Preferred solution type (auto-detect if None)

        Returns:
            CreativeSolution with recommended approach
        """
        logger.info(f"Creative solving: {problem[:100]}")

        context = context or {}
        constraints = constraints or {}

        # Determine solution type
        if preferred_type is None:
            preferred_type = self._analyze_problem_type(problem, context)

        logger.debug(f"Solution type: {preferred_type.value}")

        # Generate solution based on type
        if preferred_type == SolutionType.DECOMPOSITION:
            solution = await self._decompose_problem(problem, context, constraints)
        elif preferred_type == SolutionType.WORKAROUND:
            solution = await self._generate_workarounds(problem, context, constraints)
        elif preferred_type == SolutionType.CODE_GENERATION:
            solution = await self._generate_code(problem, context, constraints)
        elif preferred_type == SolutionType.MULTI_STEP:
            solution = await self._create_multi_step_plan(problem, context, constraints)
        else:
            # Hybrid approach - try multiple strategies
            solution = await self._hybrid_solve(problem, context, constraints)

        # Record solution
        self.solution_history.append(solution)

        logger.info(
            f"Creative solution generated: {solution.solution_type.value} "
            f"(confidence: {solution.confidence:.2f})"
        )

        return solution

    def _analyze_problem_type(self, problem: str, context: Dict) -> SolutionType:
        """
        Analyze problem to determine best solution type.

        Args:
            problem: Problem description
            context: Context information

        Returns:
            Recommended SolutionType
        """
        problem_lower = problem.lower()

        # Check for code generation indicators
        if any(kw in problem_lower for kw in [
            'write code', 'generate script', 'implement function',
            'create python', 'write a script'
        ]):
            return SolutionType.CODE_GENERATION

        # Check for decomposition indicators
        if any(kw in problem_lower for kw in [
            'complex', 'multiple steps', 'large task', 'break down',
            'decompose', 'divide', 'parts'
        ]):
            return SolutionType.DECOMPOSITION

        # Check for workaround indicators
        if any(kw in problem_lower for kw in [
            'blocked', 'cannot', 'forbidden', 'alternative',
            'workaround', 'bypass', 'different way'
        ]):
            return SolutionType.WORKAROUND

        # Check for multi-step planning indicators
        if any(kw in problem_lower for kw in [
            'plan', 'sequence', 'orchestrate', 'coordinate',
            'multi-step', 'workflow'
        ]):
            return SolutionType.MULTI_STEP

        # Check context for repeated failures
        if context.get('attempts', 0) >= 3:
            return SolutionType.WORKAROUND

        # Default to hybrid approach
        return SolutionType.HYBRID

    async def _decompose_problem(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> CreativeSolution:
        """
        Decompose complex problem into sub-tasks.

        Args:
            problem: Problem to decompose
            context: Problem context
            constraints: Constraints to consider

        Returns:
            CreativeSolution with sub-tasks
        """
        prompt = self._build_decomposition_prompt(problem, context, constraints)

        # Get LLM response
        llm_response = await self._call_llm(prompt)

        # Parse response into sub-tasks
        sub_tasks = self._parse_sub_tasks(llm_response)

        return CreativeSolution(
            solution_type=SolutionType.DECOMPOSITION,
            confidence=0.8,
            description=f"Decomposed into {len(sub_tasks)} manageable sub-tasks",
            sub_tasks=sub_tasks,
            reasoning=llm_response,
            metadata={'original_problem': problem}
        )

    async def _generate_workarounds(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> CreativeSolution:
        """
        Generate alternative workaround solutions.

        Args:
            problem: Problem requiring workaround
            context: Problem context
            constraints: Constraints to consider

        Returns:
            CreativeSolution with workarounds
        """
        prompt = self._build_workaround_prompt(problem, context, constraints)

        # Get LLM response
        llm_response = await self._call_llm(prompt)

        # Parse workarounds
        workarounds = self._parse_workarounds(llm_response)

        # Calculate confidence based on number of viable options
        confidence = min(0.9, 0.5 + (len(workarounds) * 0.1))

        return CreativeSolution(
            solution_type=SolutionType.WORKAROUND,
            confidence=confidence,
            description=f"Generated {len(workarounds)} alternative approaches",
            workarounds=workarounds,
            reasoning=llm_response,
            metadata={'original_problem': problem}
        )

    async def _generate_code(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> CreativeSolution:
        """
        Generate custom Python code to solve problem.

        Args:
            problem: Problem requiring code solution
            context: Problem context
            constraints: Code constraints (dependencies, etc.)

        Returns:
            CreativeSolution with generated code
        """
        prompt = self._build_code_generation_prompt(problem, context, constraints)

        # Get LLM response
        llm_response = await self._call_llm(prompt, temperature=0.3)

        # Extract code from response
        code = self._extract_code(llm_response)

        return CreativeSolution(
            solution_type=SolutionType.CODE_GENERATION,
            confidence=0.75,
            description="Generated custom Python code solution",
            code=code,
            reasoning=llm_response,
            metadata={'original_problem': problem}
        )

    async def _create_multi_step_plan(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> CreativeSolution:
        """
        Create multi-step execution plan.

        Args:
            problem: Problem requiring plan
            context: Problem context
            constraints: Planning constraints

        Returns:
            CreativeSolution with execution plan
        """
        prompt = self._build_planning_prompt(problem, context, constraints)

        # Get LLM response
        llm_response = await self._call_llm(prompt)

        # Parse plan
        plan = self._parse_plan(llm_response, problem)

        return CreativeSolution(
            solution_type=SolutionType.MULTI_STEP,
            confidence=0.7,
            description=f"Created {len(plan.steps)}-step execution plan",
            plan=plan,
            reasoning=llm_response,
            metadata={'original_problem': problem}
        )

    async def _hybrid_solve(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> CreativeSolution:
        """
        Hybrid approach combining multiple strategies.

        Args:
            problem: Problem to solve
            context: Problem context
            constraints: Solution constraints

        Returns:
            CreativeSolution with hybrid approach
        """
        # Generate both workarounds and decomposition
        workaround_task = self._generate_workarounds(problem, context, constraints)
        decomposition_task = self._decompose_problem(problem, context, constraints)

        # Execute in parallel
        workaround_result, decomposition_result = await asyncio.gather(
            workaround_task,
            decomposition_task,
            return_exceptions=True
        )

        # Combine results
        workarounds = []
        sub_tasks = []

        if isinstance(workaround_result, CreativeSolution):
            workarounds = workaround_result.workarounds

        if isinstance(decomposition_result, CreativeSolution):
            sub_tasks = decomposition_result.sub_tasks

        return CreativeSolution(
            solution_type=SolutionType.HYBRID,
            confidence=0.8,
            description=f"Hybrid solution: {len(workarounds)} workarounds + {len(sub_tasks)} sub-tasks",
            workarounds=workarounds,
            sub_tasks=sub_tasks,
            reasoning="Combined multiple creative approaches",
            metadata={'original_problem': problem}
        )

    def _build_decomposition_prompt(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> str:
        """Build prompt for problem decomposition"""
        return f"""You are a problem decomposition expert. Break down this complex problem into manageable sub-tasks.

Problem: {problem}

Context:
{json.dumps(context, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Please provide a decomposition in the following JSON format:
{{
  "sub_tasks": [
    {{
      "task_id": "unique_id",
      "description": "what needs to be done",
      "dependencies": ["other_task_ids"],
      "estimated_complexity": 5,
      "approach": "suggested approach"
    }}
  ]
}}

Focus on:
1. Breaking into independent or minimally dependent tasks
2. Each task should be achievable in isolation
3. Order tasks by dependencies
4. Estimate complexity (1=trivial, 10=very complex)"""

    def _build_workaround_prompt(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> str:
        """Build prompt for workaround generation"""
        return f"""You are a creative problem solver specializing in finding alternative solutions.

Problem: {problem}

Context:
{json.dumps(context, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Generate 2-4 creative workarounds in the following JSON format:
{{
  "workarounds": [
    {{
      "name": "solution_name",
      "description": "what this solution does",
      "implementation": ["step 1", "step 2", "step 3"],
      "pros": ["advantage 1", "advantage 2"],
      "cons": ["limitation 1", "limitation 2"],
      "confidence": 0.8
    }}
  ]
}}

For each workaround:
1. Think outside the box - avoid repeating failed approaches
2. Consider unconventional but practical solutions
3. Provide concrete implementation steps
4. Be honest about limitations"""

    def _build_code_generation_prompt(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> str:
        """Build prompt for code generation"""
        deps = constraints.get('allowed_dependencies', ['standard library only'])

        return f"""You are an expert Python developer. Generate production-ready code to solve this problem.

Problem: {problem}

Context:
{json.dumps(context, indent=2)}

Allowed Dependencies: {', '.join(deps) if isinstance(deps, list) else deps}

Requirements:
1. Write clean, well-documented Python code
2. Include error handling
3. Add type hints
4. Follow Python best practices
5. Keep it simple and maintainable

Provide the code in a single Python code block with explanation:

```python
# Your code here
```

Then explain how to use it and any important considerations."""

    def _build_planning_prompt(
        self,
        problem: str,
        context: Dict,
        constraints: Dict
    ) -> str:
        """Build prompt for multi-step planning"""
        return f"""You are a strategic planner. Create a detailed multi-step execution plan.

Goal: {problem}

Context:
{json.dumps(context, indent=2)}

Constraints:
{json.dumps(constraints, indent=2)}

Provide a plan in the following JSON format:
{{
  "goal": "overall goal",
  "steps": [
    {{
      "step_number": 1,
      "action": "what to do",
      "expected_result": "what should happen",
      "verification": "how to verify success",
      "fallback": "what to do if this fails"
    }}
  ],
  "expected_outcome": "final result",
  "fallback_options": ["backup plan 1", "backup plan 2"]
}}

For each step:
1. Be specific and actionable
2. Include verification criteria
3. Provide fallback options
4. Estimate time/resources"""

    async def _call_llm(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Call LLM with retry logic.

        Args:
            prompt: Prompt to send
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response text
        """
        if not self.llm_service:
            logger.warning("No LLM service configured, returning mock response")
            return self._mock_llm_response(prompt)

        from alpha.llm.service import Message

        messages = [
            Message(role="system", content="You are a creative problem-solving assistant."),
            Message(role="user", content=prompt)
        ]

        for attempt in range(self.max_retries):
            try:
                response = await self.llm_service.complete(
                    messages=messages,
                    provider=self.provider,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.content
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt >= self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise Exception("LLM call failed after all retries")

    def _mock_llm_response(self, prompt: str) -> str:
        """Generate mock response when LLM not available"""
        if "decompose" in prompt.lower() or "sub_tasks" in prompt.lower():
            return json.dumps({
                "sub_tasks": [
                    {
                        "task_id": "task_1",
                        "description": "Analyze the problem requirements",
                        "dependencies": [],
                        "estimated_complexity": 3,
                        "approach": "Review documentation and specifications"
                    },
                    {
                        "task_id": "task_2",
                        "description": "Implement solution",
                        "dependencies": ["task_1"],
                        "estimated_complexity": 7,
                        "approach": "Write code following best practices"
                    }
                ]
            })
        elif "workaround" in prompt.lower():
            return json.dumps({
                "workarounds": [
                    {
                        "name": "Alternative API approach",
                        "description": "Use different API endpoint",
                        "implementation": ["Find alternative endpoint", "Test access", "Implement"],
                        "pros": ["May have different rate limits", "Could work around block"],
                        "cons": ["Might have limited features", "Could be deprecated"],
                        "confidence": 0.7
                    }
                ]
            })
        elif "code" in prompt.lower():
            return "```python\n# Generated code solution\ndef solve_problem():\n    pass\n```"
        else:
            return json.dumps({
                "goal": "Solve the problem",
                "steps": [{"step_number": 1, "action": "Execute solution"}],
                "expected_outcome": "Problem resolved"
            })

    def _parse_sub_tasks(self, llm_response: str) -> List[SubTask]:
        """Parse sub-tasks from LLM response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(llm_response)

            sub_tasks = []
            for task_data in data.get('sub_tasks', []):
                sub_tasks.append(SubTask(
                    task_id=task_data.get('task_id', f"task_{len(sub_tasks)}"),
                    description=task_data.get('description', ''),
                    dependencies=task_data.get('dependencies', []),
                    estimated_complexity=task_data.get('estimated_complexity', 5),
                    approach=task_data.get('approach', '')
                ))

            return sub_tasks
        except Exception as e:
            logger.warning(f"Failed to parse sub-tasks: {e}")
            # Return single generic task as fallback
            return [SubTask(
                task_id="task_1",
                description="Complete the task using available methods",
                estimated_complexity=5
            )]

    def _parse_workarounds(self, llm_response: str) -> List[WorkaroundSolution]:
        """Parse workarounds from LLM response"""
        try:
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(llm_response)

            workarounds = []
            for wa_data in data.get('workarounds', []):
                workarounds.append(WorkaroundSolution(
                    name=wa_data.get('name', f'workaround_{len(workarounds)}'),
                    description=wa_data.get('description', ''),
                    implementation=wa_data.get('implementation', []),
                    pros=wa_data.get('pros', []),
                    cons=wa_data.get('cons', []),
                    confidence=wa_data.get('confidence', 0.5)
                ))

            return workarounds
        except Exception as e:
            logger.warning(f"Failed to parse workarounds: {e}")
            return []

    def _extract_code(self, llm_response: str) -> str:
        """Extract Python code from LLM response"""
        # Look for code blocks
        code_blocks = re.findall(r'```python\n(.*?)\n```', llm_response, re.DOTALL)

        if code_blocks:
            return code_blocks[0].strip()

        # Fallback: return entire response if no code block found
        return llm_response.strip()

    def _parse_plan(self, llm_response: str, problem: str) -> MultiStepPlan:
        """Parse multi-step plan from LLM response"""
        try:
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(llm_response)

            return MultiStepPlan(
                plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                goal=data.get('goal', problem),
                steps=data.get('steps', []),
                expected_outcome=data.get('expected_outcome', ''),
                fallback_options=data.get('fallback_options', [])
            )
        except Exception as e:
            logger.warning(f"Failed to parse plan: {e}")
            # Return minimal plan as fallback
            return MultiStepPlan(
                plan_id="fallback_plan",
                goal=problem,
                steps=[{"step_number": 1, "action": "Execute available solutions"}],
                expected_outcome="Problem resolved"
            )

    def get_solution_history(self) -> List[CreativeSolution]:
        """Get history of generated solutions"""
        return self.solution_history.copy()

    def clear_history(self):
        """Clear solution history"""
        self.solution_history.clear()
        logger.debug("Cleared creative solver history")
