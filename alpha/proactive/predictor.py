"""
Alpha - Need Predictor

Anticipate user needs based on context and history.
Features:
- Predict next likely user request
- Context analysis
- Confidence scoring
- Integration with pattern learner
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

from alpha.proactive.pattern_learner import Pattern, PatternLearner

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """Represents a need prediction."""
    prediction_id: str
    predicted_need: str
    confidence: float
    reasoning: str
    context: Dict[str, Any]
    predicted_at: datetime
    pattern_ids: List[str]
    suggested_action: Optional[str] = None


class Predictor:
    """
    Predict user needs based on context and learned patterns.

    Features:
    - Analyze current context
    - Predict next likely requests
    - Time-based predictions
    - Activity sequence analysis
    - Confidence scoring
    """

    def __init__(
        self,
        pattern_learner: PatternLearner,
        min_confidence: float = 0.5
    ):
        """
        Initialize predictor.

        Args:
            pattern_learner: PatternLearner instance
            min_confidence: Minimum confidence for predictions
        """
        self.pattern_learner = pattern_learner
        self.min_confidence = min_confidence
        self.predictions_history: List[Prediction] = []
        self.recent_requests: List[Dict[str, Any]] = []

    async def predict_next_need(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Prediction]:
        """
        Predict user's next likely needs.

        Args:
            context: Current context (time, recent activity, etc.)

        Returns:
            List of predictions ordered by confidence
        """
        predictions = []

        # Build context if not provided
        if context is None:
            context = await self._build_context()

        # Get relevant patterns
        patterns = await self.pattern_learner.get_patterns(
            min_confidence=self.min_confidence
        )

        if not patterns:
            logger.info("No patterns available for prediction")
            return predictions

        # Time-based predictions
        temporal_predictions = await self._predict_from_temporal_patterns(
            patterns, context
        )
        predictions.extend(temporal_predictions)

        # Sequence-based predictions
        sequence_predictions = await self._predict_from_sequences(
            patterns, context
        )
        predictions.extend(sequence_predictions)

        # Context-based predictions
        context_predictions = await self._predict_from_context(
            patterns, context
        )
        predictions.extend(context_predictions)

        # Remove duplicates and sort by confidence
        predictions = self._deduplicate_predictions(predictions)
        predictions.sort(key=lambda p: p.confidence, reverse=True)

        # Store predictions
        self.predictions_history.extend(predictions)

        return predictions[:5]  # Return top 5

    async def _build_context(self) -> Dict[str, Any]:
        """Build current context for predictions."""
        now = datetime.now()

        context = {
            'current_time': now,
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'day_of_month': now.day,
            'recent_requests': self.recent_requests[-10:],  # Last 10 requests
            'time_since_last_request': None
        }

        # Calculate time since last request
        if self.recent_requests:
            last_request_time = self.recent_requests[-1].get('timestamp')
            if last_request_time:
                delta = now - last_request_time
                context['time_since_last_request'] = delta.total_seconds()

        return context

    async def _predict_from_temporal_patterns(
        self,
        patterns: List[Pattern],
        context: Dict[str, Any]
    ) -> List[Prediction]:
        """Predict based on temporal patterns."""
        predictions = []

        current_hour = context['hour']
        current_day = context['day_of_week']

        temporal_patterns = [
            p for p in patterns
            if p.pattern_type == 'temporal'
        ]

        for pattern in temporal_patterns:
            metadata = pattern.metadata
            confidence = pattern.confidence

            # Check if pattern matches current time
            if metadata.get('type') == 'hour_of_day':
                hour = metadata.get('hour')
                # Predict if we're within 1 hour
                if abs(hour - current_hour) <= 1:
                    # Higher confidence if exact match
                    if hour == current_hour:
                        confidence *= 1.2
                    else:
                        confidence *= 0.9

                    import uuid
                    prediction = Prediction(
                        prediction_id=str(uuid.uuid4()),
                        predicted_need=f"User typically active at this time ({hour:02d}:00)",
                        confidence=min(confidence, 1.0),
                        reasoning=f"Based on {pattern.frequency} observations at hour {hour}",
                        context=context,
                        predicted_at=datetime.now(),
                        pattern_ids=[pattern.pattern_id],
                        suggested_action="Prepare for typical requests at this hour"
                    )
                    predictions.append(prediction)

            elif metadata.get('type') == 'day_of_week':
                day = metadata.get('day_of_week')
                if day == current_day:
                    import uuid
                    prediction = Prediction(
                        prediction_id=str(uuid.uuid4()),
                        predicted_need=f"User typically active on this day",
                        confidence=confidence,
                        reasoning=f"Based on {pattern.frequency} observations on this weekday",
                        context=context,
                        predicted_at=datetime.now(),
                        pattern_ids=[pattern.pattern_id],
                        suggested_action="Prepare for typical weekly requests"
                    )
                    predictions.append(prediction)

        return predictions

    async def _predict_from_sequences(
        self,
        patterns: List[Pattern],
        context: Dict[str, Any]
    ) -> List[Prediction]:
        """Predict based on request sequences."""
        predictions = []

        recent_requests = context.get('recent_requests', [])
        if len(recent_requests) < 2:
            return predictions

        # Analyze recent request sequence
        last_request = recent_requests[-1].get('normalized', '')

        # Look for patterns that follow this request
        recurring_patterns = [
            p for p in patterns
            if p.pattern_type == 'recurring_request'
        ]

        for pattern in recurring_patterns:
            normalized = pattern.metadata.get('normalized_text', '')

            # Simple sequence matching
            # In a production system, this would use more sophisticated sequence analysis
            if normalized and normalized != last_request:
                # Calculate confidence based on pattern frequency and time gap
                base_confidence = pattern.confidence * 0.7  # Lower for sequence predictions

                import uuid
                prediction = Prediction(
                    prediction_id=str(uuid.uuid4()),
                    predicted_need=normalized,
                    confidence=base_confidence,
                    reasoning=f"Based on request patterns (observed {pattern.frequency} times)",
                    context=context,
                    predicted_at=datetime.now(),
                    pattern_ids=[pattern.pattern_id],
                    suggested_action=f"User might ask: {pattern.examples[0] if pattern.examples else normalized}"
                )
                predictions.append(prediction)

        return predictions

    async def _predict_from_context(
        self,
        patterns: List[Pattern],
        context: Dict[str, Any]
    ) -> List[Prediction]:
        """Predict based on current context."""
        predictions = []

        time_since_last = context.get('time_since_last_request')

        # If user has been inactive for a while, predict return patterns
        if time_since_last and time_since_last > 3600:  # 1 hour
            # Look for patterns about how user returns after breaks
            recurring_patterns = [
                p for p in patterns
                if p.pattern_type == 'recurring_request' and p.confidence > 0.7
            ]

            # Predict most common requests
            for pattern in recurring_patterns[:3]:  # Top 3
                import uuid
                prediction = Prediction(
                    prediction_id=str(uuid.uuid4()),
                    predicted_need=pattern.metadata.get('normalized_text', 'Unknown'),
                    confidence=pattern.confidence * 0.6,  # Lower confidence after inactivity
                    reasoning=f"User returning after inactivity, common request (seen {pattern.frequency} times)",
                    context=context,
                    predicted_at=datetime.now(),
                    pattern_ids=[pattern.pattern_id],
                    suggested_action=pattern.examples[0] if pattern.examples else None
                )
                predictions.append(prediction)

        return predictions

    def _deduplicate_predictions(
        self,
        predictions: List[Prediction]
    ) -> List[Prediction]:
        """Remove duplicate predictions, keeping highest confidence."""
        seen = {}
        unique = []

        for prediction in predictions:
            key = prediction.predicted_need

            if key not in seen or prediction.confidence > seen[key].confidence:
                seen[key] = prediction

        unique = list(seen.values())
        return unique

    async def record_request(
        self,
        request_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a user request for future predictions.

        Args:
            request_text: The user's request
            metadata: Additional metadata
        """
        # Normalize request
        normalized = self._normalize_text(request_text)

        request_data = {
            'text': request_text,
            'normalized': normalized,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }

        self.recent_requests.append(request_data)

        # Keep only recent history (last 100 requests)
        if len(self.recent_requests) > 100:
            self.recent_requests = self.recent_requests[-100:]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        # Simple normalization
        import string
        text = text.lower().strip()
        text = text.translate(str.maketrans('', '', string.punctuation))

        # Extract keywords
        words = text.split()
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'can', 'could',
                     'please', 'would', 'will', 'i', 'me', 'my', 'you', 'your'}
        keywords = [w for w in words if w not in stop_words]

        return ' '.join(keywords[:5])

    async def evaluate_prediction(
        self,
        prediction_id: str,
        was_correct: bool
    ):
        """
        Evaluate whether a prediction was correct.

        Args:
            prediction_id: Prediction ID
            was_correct: Whether prediction was correct

        This can be used to improve future predictions.
        """
        for prediction in self.predictions_history:
            if prediction.prediction_id == prediction_id:
                logger.info(
                    f"Prediction {prediction_id} evaluation: "
                    f"{'correct' if was_correct else 'incorrect'}"
                )

                # TODO: Update pattern learner confidence based on prediction accuracy
                # This would implement reinforcement learning

                break

    async def get_prediction_accuracy(self) -> Dict[str, Any]:
        """
        Get prediction accuracy statistics.

        Returns:
            Accuracy statistics
        """
        # This would require tracking prediction evaluations
        # For now, return placeholder
        return {
            "total_predictions": len(self.predictions_history),
            "evaluated": 0,
            "correct": 0,
            "accuracy": 0.0
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get predictor statistics."""
        total = len(self.predictions_history)

        if total == 0:
            return {
                "total_predictions": 0,
                "avg_confidence": 0.0,
                "recent_requests": len(self.recent_requests)
            }

        avg_confidence = sum(p.confidence for p in self.predictions_history) / total

        return {
            "total_predictions": total,
            "avg_confidence": avg_confidence,
            "recent_requests": len(self.recent_requests),
            "latest_prediction": self.predictions_history[-1].predicted_at.isoformat()
        }
