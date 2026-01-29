"""
Alpha - Cron Expression Parser

Parses and evaluates cron expressions for task scheduling.

Supported format: minute hour day month weekday
- minute: 0-59
- hour: 0-23
- day: 1-31
- month: 1-12
- weekday: 0-6 (0 = Sunday)

Special characters:
- *: any value
- */N: every N units
- N-M: range from N to M
- N,M,O: specific values
"""

import re
from datetime import datetime, timedelta
from typing import List, Set, Optional
import calendar


class CronParseError(Exception):
    """Raised when cron expression cannot be parsed."""
    pass


class CronSchedule:
    """
    Cron schedule representation and evaluation.

    Examples:
        # Every day at 9:00 AM
        cron = CronSchedule("0 9 * * *")

        # Every 15 minutes
        cron = CronSchedule("*/15 * * * *")

        # Every Monday at 8:30 AM
        cron = CronSchedule("30 8 * * 1")
    """

    def __init__(self, expression: str):
        """
        Initialize cron schedule from expression.

        Args:
            expression: Cron expression string

        Raises:
            CronParseError: If expression is invalid
        """
        self.expression = expression.strip()
        self.parts = self._parse(self.expression)

    def _parse(self, expression: str) -> dict:
        """
        Parse cron expression into components.

        Returns:
            Dictionary with minute, hour, day, month, weekday sets
        """
        parts = expression.split()

        if len(parts) != 5:
            raise CronParseError(
                f"Invalid cron expression: expected 5 parts, got {len(parts)}"
            )

        try:
            return {
                "minute": self._parse_field(parts[0], 0, 59),
                "hour": self._parse_field(parts[1], 0, 23),
                "day": self._parse_field(parts[2], 1, 31),
                "month": self._parse_field(parts[3], 1, 12),
                "weekday": self._parse_field(parts[4], 0, 6),
            }
        except ValueError as e:
            raise CronParseError(f"Invalid cron expression: {e}")

    def _parse_field(self, field: str, min_val: int, max_val: int) -> Set[int]:
        """
        Parse a single cron field.

        Args:
            field: Field string (e.g., "*", "*/5", "1-10", "1,3,5")
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Set of matching values
        """
        if field == "*":
            return set(range(min_val, max_val + 1))

        # Handle */N (step)
        if field.startswith("*/"):
            try:
                step = int(field[2:])
                return set(range(min_val, max_val + 1, step))
            except ValueError:
                raise ValueError(f"Invalid step value: {field}")

        # Handle N-M (range)
        if "-" in field and not field.startswith("-"):
            try:
                start, end = field.split("-")
                start, end = int(start), int(end)
                if not (min_val <= start <= max_val and min_val <= end <= max_val):
                    raise ValueError(f"Range out of bounds: {field}")
                return set(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid range: {field}")

        # Handle N,M,O (list)
        if "," in field:
            try:
                values = [int(v.strip()) for v in field.split(",")]
                for v in values:
                    if not (min_val <= v <= max_val):
                        raise ValueError(f"Value out of bounds: {v}")
                return set(values)
            except ValueError:
                raise ValueError(f"Invalid list: {field}")

        # Single value
        try:
            value = int(field)
            if not (min_val <= value <= max_val):
                raise ValueError(f"Value out of bounds: {value}")
            return {value}
        except ValueError:
            raise ValueError(f"Invalid value: {field}")

    def matches(self, dt: datetime) -> bool:
        """
        Check if datetime matches cron expression.

        Args:
            dt: Datetime to check

        Returns:
            True if datetime matches expression
        """
        return (
            dt.minute in self.parts["minute"]
            and dt.hour in self.parts["hour"]
            and dt.day in self.parts["day"]
            and dt.month in self.parts["month"]
            and dt.weekday() in self._convert_weekday(self.parts["weekday"])
        )

    def _convert_weekday(self, weekdays: Set[int]) -> Set[int]:
        """
        Convert cron weekday (0=Sunday) to Python weekday (0=Monday).

        Args:
            weekdays: Set of cron weekdays

        Returns:
            Set of Python weekdays
        """
        python_weekdays = set()
        for day in weekdays:
            if day == 0:
                python_weekdays.add(6)  # Sunday
            else:
                python_weekdays.add(day - 1)  # Monday-Saturday
        return python_weekdays

    def next_run_time(self, after: Optional[datetime] = None) -> datetime:
        """
        Calculate next run time after given datetime.

        Args:
            after: Reference datetime (default: now)

        Returns:
            Next datetime matching cron expression
        """
        if after is None:
            after = datetime.now()

        # Start from next minute
        current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Search for next matching time (max 2 years ahead)
        max_iterations = 365 * 24 * 60 * 2
        iterations = 0

        while iterations < max_iterations:
            if self.matches(current):
                return current

            # Move to next minute
            current += timedelta(minutes=1)
            iterations += 1

        raise CronParseError(
            f"Could not find next run time for expression: {self.expression}"
        )

    def previous_run_time(self, before: Optional[datetime] = None) -> datetime:
        """
        Calculate previous run time before given datetime.

        Args:
            before: Reference datetime (default: now)

        Returns:
            Previous datetime matching cron expression
        """
        if before is None:
            before = datetime.now()

        # Start from previous minute
        current = before.replace(second=0, microsecond=0) - timedelta(minutes=1)

        # Search for previous matching time (max 2 years back)
        max_iterations = 365 * 24 * 60 * 2
        iterations = 0

        while iterations < max_iterations:
            if self.matches(current):
                return current

            # Move to previous minute
            current -= timedelta(minutes=1)
            iterations += 1

        raise CronParseError(
            f"Could not find previous run time for expression: {self.expression}"
        )

    def __str__(self) -> str:
        return f"CronSchedule({self.expression})"

    def __repr__(self) -> str:
        return f"CronSchedule(expression='{self.expression}')"


class CronParser:
    """
    Utility class for parsing and validating cron expressions.
    """

    @staticmethod
    def parse(expression: str) -> CronSchedule:
        """
        Parse cron expression.

        Args:
            expression: Cron expression string

        Returns:
            CronSchedule instance

        Raises:
            CronParseError: If expression is invalid
        """
        return CronSchedule(expression)

    @staticmethod
    def validate(expression: str) -> bool:
        """
        Validate cron expression.

        Args:
            expression: Cron expression string

        Returns:
            True if valid, False otherwise
        """
        try:
            CronSchedule(expression)
            return True
        except CronParseError:
            return False

    @staticmethod
    def describe(expression: str) -> str:
        """
        Generate human-readable description of cron expression.

        Args:
            expression: Cron expression string

        Returns:
            Human-readable description
        """
        try:
            cron = CronSchedule(expression)
            parts = []

            # Minute
            if cron.parts["minute"] == set(range(60)):
                minute_desc = "every minute"
            elif len(cron.parts["minute"]) == 1:
                minute_desc = f"at minute {list(cron.parts['minute'])[0]}"
            else:
                minute_desc = f"at minutes {sorted(cron.parts['minute'])}"

            # Hour
            if cron.parts["hour"] == set(range(24)):
                hour_desc = "every hour"
            elif len(cron.parts["hour"]) == 1:
                hour_desc = f"at hour {list(cron.parts['hour'])[0]}"
            else:
                hour_desc = f"at hours {sorted(cron.parts['hour'])}"

            # Day
            if cron.parts["day"] == set(range(1, 32)):
                day_desc = "every day"
            elif len(cron.parts["day"]) == 1:
                day_desc = f"on day {list(cron.parts['day'])[0]}"
            else:
                day_desc = f"on days {sorted(cron.parts['day'])}"

            # Month
            if cron.parts["month"] == set(range(1, 13)):
                month_desc = "every month"
            elif len(cron.parts["month"]) == 1:
                month_desc = f"in month {list(cron.parts['month'])[0]}"
            else:
                month_desc = f"in months {sorted(cron.parts['month'])}"

            # Weekday
            weekday_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            if cron.parts["weekday"] == set(range(7)):
                weekday_desc = "every day of week"
            elif len(cron.parts["weekday"]) == 1:
                day = list(cron.parts["weekday"])[0]
                weekday_desc = f"on {weekday_names[day]}"
            else:
                days = [weekday_names[d] for d in sorted(cron.parts["weekday"])]
                weekday_desc = f"on {', '.join(days)}"

            return f"{minute_desc}, {hour_desc}, {day_desc}, {month_desc}, {weekday_desc}"

        except CronParseError as e:
            return f"Invalid expression: {e}"


# Common cron expressions
class CommonCronExpressions:
    """Pre-defined common cron expressions."""

    EVERY_MINUTE = "* * * * *"
    EVERY_5_MINUTES = "*/5 * * * *"
    EVERY_15_MINUTES = "*/15 * * * *"
    EVERY_30_MINUTES = "*/30 * * * *"
    EVERY_HOUR = "0 * * * *"
    EVERY_2_HOURS = "0 */2 * * *"
    EVERY_6_HOURS = "0 */6 * * *"
    EVERY_12_HOURS = "0 */12 * * *"
    DAILY_MIDNIGHT = "0 0 * * *"
    DAILY_NOON = "0 12 * * *"
    DAILY_9AM = "0 9 * * *"
    DAILY_5PM = "0 17 * * *"
    WEEKLY_MONDAY_9AM = "0 9 * * 1"
    WEEKLY_FRIDAY_5PM = "0 17 * * 5"
    MONTHLY_FIRST_DAY = "0 0 1 * *"
    MONTHLY_LAST_DAY = "0 0 28-31 * *"  # Approximate
