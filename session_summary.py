"""
session_summary.py

Tracks reps, correct vs incorrect, and average posture score for a session.
"""
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class SessionSummary:
    total_reps: int = 0
    correct_reps: int = 0
    incorrect_reps: int = 0
    posture_scores: List[float] = field(default_factory=list)

    def push_rep(self, correct: bool, score: float):
        self.total_reps += 1
        if correct:
            self.correct_reps += 1
        else:
            self.incorrect_reps += 1
        self.posture_scores.append(score)

    def average_score(self) -> float:
        if not self.posture_scores:
            return 0.0
        return sum(self.posture_scores) / len(self.posture_scores)

    def as_dict(self) -> Dict:
        return {
            'total_reps': self.total_reps,
            'correct_reps': self.correct_reps,
            'incorrect_reps': self.incorrect_reps,
            'avg_posture_score': round(self.average_score(), 2)
        }