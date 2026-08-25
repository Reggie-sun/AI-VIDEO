from enum import Enum


class StateCommitStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    OUTCOME_UNKNOWN = "outcome_unknown"


class ReviewAttemptPhase(str, Enum):
    REQUESTED = "requested"
    EVIDENCE = "evidence"
    ACTIVATE = "activate"
