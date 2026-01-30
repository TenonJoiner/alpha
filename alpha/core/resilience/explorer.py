"""
Alternative Explorer Component

Explores multiple solution paths to accomplish tasks when primary approaches fail.
Supports both parallel and sequential strategy execution.
"""

import logging
from typing import List, Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of alternative strategies"""
    API_PROVIDER = "api_provider"      # Different API providers
    TOOL_ALTERNATIVE = "tool"          # Different tools for same goal
    APPROACH_VARIATION = "approach"    # Different problem-solving approaches
    PARAMETER_VARIATION = "parameter"  # Different parameter combinations
    CUSTOM_CODE = "custom_code"        # Generated custom code


@dataclass
class StrategyTemplate:
    """
    Template for generating alternative strategies.

    Attributes:
        strategy_type: Type of strategy
        name_pattern: Pattern for strategy name (e.g., "provider_{}")
        description_pattern: Pattern for description
        priority_base: Base priority score
        cost_multiplier: Cost factor relative to primary
        applicable_operations: List of operation patterns this applies to
    """
    strategy_type: StrategyType
    name_pattern: str
    description_pattern: str
    priority_base: float = 1.0
    cost_multiplier: float = 1.0
    applicable_operations: List[str] = field(default_factory=list)


class AlternativeExplorer:
    """
    Explores and enumerates alternative strategies for task execution.

    Features:
    - Strategy enumeration based on task characteristics
    - Strategy ranking by success probability, cost, and speed
    - Dynamic strategy generation
    - Learning from past successes (future enhancement)

    Usage:
        explorer = AlternativeExplorer()

        # Enumerate strategies for HTTP request
        strategies = explorer.enumerate_strategies(
            operation="http_request",
            context={"url": "https://api.example.com", "method": "GET"}
        )

        # Rank strategies
        ranked = explorer.rank_strategies(strategies)
    """

    def __init__(self):
        """Initialize alternative explorer"""
        self.strategy_templates: List[StrategyTemplate] = []
        self.success_history: Dict[str, int] = {}  # strategy_name -> success_count
        self.failure_history: Dict[str, int] = {}  # strategy_name -> failure_count

        self._initialize_default_templates()

        logger.info("AlternativeExplorer initialized")

    def _initialize_default_templates(self):
        """Initialize default strategy templates"""

        # API Provider alternatives
        self.strategy_templates.append(StrategyTemplate(
            strategy_type=StrategyType.API_PROVIDER,
            name_pattern="provider_{}",
            description_pattern="Use {} API provider",
            priority_base=1.0,
            cost_multiplier=1.0,
            applicable_operations=["llm_request", "api_call"]
        ))

        # Tool alternatives for HTTP requests
        self.strategy_templates.append(StrategyTemplate(
            strategy_type=StrategyType.TOOL_ALTERNATIVE,
            name_pattern="http_tool_{}",
            description_pattern="Use {} for HTTP request",
            priority_base=0.9,
            cost_multiplier=0.5,
            applicable_operations=["http_request", "fetch_url"]
        ))

        # Approach variations for data retrieval
        self.strategy_templates.append(StrategyTemplate(
            strategy_type=StrategyType.APPROACH_VARIATION,
            name_pattern="approach_{}",
            description_pattern="Use {} approach",
            priority_base=0.8,
            cost_multiplier=0.8,
            applicable_operations=["data_retrieval", "search", "query"]
        ))

    def enumerate_strategies(
        self,
        operation: str,
        context: Optional[Dict] = None,
        primary_strategy: Optional[str] = None
    ) -> List[Dict]:
        """
        Enumerate possible alternative strategies for an operation.

        Args:
            operation: Operation identifier (e.g., "http_request", "llm_call")
            context: Additional context about the operation
            primary_strategy: Name of primary strategy that failed (to avoid)

        Returns:
            List of strategy dictionaries with metadata
        """
        context = context or {}
        strategies = []

        logger.debug(f"Enumerating strategies for operation: {operation}")

        # Find applicable templates
        applicable_templates = [
            t for t in self.strategy_templates
            if any(pattern in operation for pattern in t.applicable_operations)
        ]

        # Generate strategies from templates
        for template in applicable_templates:
            strategy_variants = self._generate_strategy_variants(
                template, operation, context
            )
            strategies.extend(strategy_variants)

        # Add operation-specific strategies
        custom_strategies = self._get_custom_strategies(operation, context)
        strategies.extend(custom_strategies)

        # Filter out primary strategy if specified
        if primary_strategy:
            strategies = [s for s in strategies if s["name"] != primary_strategy]

        logger.info(f"Enumerated {len(strategies)} alternative strategies")

        return strategies

    def _generate_strategy_variants(
        self,
        template: StrategyTemplate,
        operation: str,
        context: Dict
    ) -> List[Dict]:
        """
        Generate strategy variants from template.

        Args:
            template: Strategy template
            operation: Operation identifier
            context: Operation context

        Returns:
            List of strategy dictionaries
        """
        variants = []

        # Generate variants based on strategy type
        if template.strategy_type == StrategyType.API_PROVIDER:
            # Example: Different LLM providers
            providers = ["deepseek", "anthropic", "openai"]
            for provider in providers:
                variants.append({
                    "name": template.name_pattern.format(provider),
                    "type": template.strategy_type.value,
                    "description": template.description_pattern.format(provider.title()),
                    "priority": template.priority_base,
                    "cost_estimate": context.get("cost", 0.01) * template.cost_multiplier,
                    "metadata": {"provider": provider}
                })

        elif template.strategy_type == StrategyType.TOOL_ALTERNATIVE:
            # Example: Different HTTP tools
            tools = ["httpx", "curl", "wget", "requests"]
            for tool in tools:
                variants.append({
                    "name": template.name_pattern.format(tool),
                    "type": template.strategy_type.value,
                    "description": template.description_pattern.format(tool),
                    "priority": template.priority_base,
                    "cost_estimate": 0.0,  # No API cost for local tools
                    "metadata": {"tool": tool}
                })

        elif template.strategy_type == StrategyType.APPROACH_VARIATION:
            # Example: Different search approaches
            approaches = ["direct_api", "web_search", "cache_lookup", "fallback_data"]
            for approach in approaches:
                variants.append({
                    "name": template.name_pattern.format(approach),
                    "type": template.strategy_type.value,
                    "description": template.description_pattern.format(approach.replace("_", " ")),
                    "priority": template.priority_base,
                    "cost_estimate": context.get("cost", 0.01) * template.cost_multiplier,
                    "metadata": {"approach": approach}
                })

        return variants

    def _get_custom_strategies(self, operation: str, context: Dict) -> List[Dict]:
        """
        Get custom strategies specific to operation type.

        Args:
            operation: Operation identifier
            context: Operation context

        Returns:
            List of custom strategy dictionaries
        """
        custom = []

        # HTTP request custom strategies
        if "http" in operation or "fetch" in operation:
            custom.append({
                "name": "http_with_retry_headers",
                "type": StrategyType.PARAMETER_VARIATION.value,
                "description": "Add retry-friendly headers",
                "priority": 0.85,
                "cost_estimate": 0.0,
                "metadata": {"modification": "add_headers"}
            })

            custom.append({
                "name": "http_with_longer_timeout",
                "type": StrategyType.PARAMETER_VARIATION.value,
                "description": "Increase timeout duration",
                "priority": 0.80,
                "cost_estimate": 0.0,
                "metadata": {"modification": "increase_timeout"}
            })

        # LLM request custom strategies
        if "llm" in operation or "ai" in operation:
            custom.append({
                "name": "llm_with_simpler_prompt",
                "type": StrategyType.PARAMETER_VARIATION.value,
                "description": "Simplify prompt for better success rate",
                "priority": 0.75,
                "cost_estimate": context.get("cost", 0.01) * 0.7,
                "metadata": {"modification": "simplify_prompt"}
            })

        # File operation custom strategies
        if "file" in operation or "read" in operation or "write" in operation:
            custom.append({
                "name": "file_with_chunks",
                "type": StrategyType.APPROACH_VARIATION.value,
                "description": "Process file in chunks",
                "priority": 0.85,
                "cost_estimate": 0.0,
                "metadata": {"modification": "chunked_processing"}
            })

        return custom

    def rank_strategies(
        self,
        strategies: List[Dict],
        optimization_goal: str = "balanced"
    ) -> List[Dict]:
        """
        Rank strategies by preference based on optimization goal.

        Ranking factors:
        - Base priority
        - Historical success rate
        - Cost (if cost-optimizing)
        - Estimated speed (if speed-optimizing)

        Args:
            strategies: List of strategy dictionaries
            optimization_goal: "balanced", "cost", "speed", or "success_rate"

        Returns:
            Sorted list of strategies (highest rank first)
        """
        logger.debug(f"Ranking {len(strategies)} strategies (goal: {optimization_goal})")

        ranked = []
        for strategy in strategies:
            score = self._calculate_strategy_score(strategy, optimization_goal)
            strategy["score"] = score
            ranked.append(strategy)

        # Sort by score (descending)
        ranked.sort(key=lambda s: s["score"], reverse=True)

        logger.debug(f"Top strategy: {ranked[0]['name']} (score: {ranked[0]['score']:.2f})")

        return ranked

    def _calculate_strategy_score(
        self,
        strategy: Dict,
        optimization_goal: str
    ) -> float:
        """
        Calculate strategy score based on optimization goal.

        Args:
            strategy: Strategy dictionary
            optimization_goal: Optimization criterion

        Returns:
            Score (higher is better)
        """
        base_priority = strategy.get("priority", 1.0)
        cost = strategy.get("cost_estimate", 0.01)
        time_estimate = strategy.get("time_estimate", 10.0)

        # Calculate success rate from history
        name = strategy["name"]
        successes = self.success_history.get(name, 0)
        failures = self.failure_history.get(name, 0)
        total_attempts = successes + failures

        if total_attempts > 0:
            success_rate = successes / total_attempts
        else:
            success_rate = 0.5  # Default for unknown strategies

        # Calculate score based on goal
        if optimization_goal == "cost":
            # Minimize cost, but consider success rate
            cost_factor = 1.0 / (cost + 0.001)  # Avoid division by zero
            score = (cost_factor * 0.7) + (success_rate * 0.3)

        elif optimization_goal == "speed":
            # Minimize time, but consider success rate
            time_factor = 1.0 / (time_estimate + 0.1)
            score = (time_factor * 0.7) + (success_rate * 0.3)

        elif optimization_goal == "success_rate":
            # Maximize success rate
            score = (success_rate * 0.8) + (base_priority * 0.2)

        else:  # balanced
            # Balance all factors
            cost_factor = 1.0 / (cost + 0.001)
            time_factor = 1.0 / (time_estimate + 0.1)

            score = (
                (base_priority * 0.3) +
                (success_rate * 0.4) +
                (cost_factor * 0.15) +
                (time_factor * 0.15)
            )

        return score

    def record_success(self, strategy_name: str):
        """
        Record successful strategy execution.

        Args:
            strategy_name: Name of successful strategy
        """
        self.success_history[strategy_name] = self.success_history.get(strategy_name, 0) + 1
        logger.debug(f"Recorded success for strategy: {strategy_name}")

    def record_failure(self, strategy_name: str):
        """
        Record failed strategy execution.

        Args:
            strategy_name: Name of failed strategy
        """
        self.failure_history[strategy_name] = self.failure_history.get(strategy_name, 0) + 1
        logger.debug(f"Recorded failure for strategy: {strategy_name}")

    def get_success_rate(self, strategy_name: str) -> float:
        """
        Get success rate for a strategy.

        Args:
            strategy_name: Name of strategy

        Returns:
            Success rate (0.0 to 1.0), or 0.5 if unknown
        """
        successes = self.success_history.get(strategy_name, 0)
        failures = self.failure_history.get(strategy_name, 0)
        total = successes + failures

        if total == 0:
            return 0.5  # Unknown strategy

        return successes / total

    def get_strategy_stats(self) -> Dict:
        """
        Get statistics about strategy performance.

        Returns:
            Dictionary with strategy statistics
        """
        all_strategies = set(list(self.success_history.keys()) + list(self.failure_history.keys()))

        stats = {
            "total_strategies_tried": len(all_strategies),
            "strategies": {}
        }

        for strategy_name in all_strategies:
            successes = self.success_history.get(strategy_name, 0)
            failures = self.failure_history.get(strategy_name, 0)
            total = successes + failures
            success_rate = successes / total if total > 0 else 0.0

            stats["strategies"][strategy_name] = {
                "successes": successes,
                "failures": failures,
                "total_attempts": total,
                "success_rate": success_rate
            }

        return stats

    def clear_history(self):
        """Clear success/failure history"""
        self.success_history.clear()
        self.failure_history.clear()
        logger.debug("Cleared strategy history")
