import time
import uuid
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_EXECUTED = "AUTO_EXECUTED"


class ActionTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    action_type: str  # e.g. "code_execution", "external_api", "database_write", "summarization"
    description: str
    estimated_cost_usd: float
    is_high_risk: bool
    payload: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = Field(default_factory=time.time)
    resolution_time: Optional[float] = None
    resolved_by: Optional[str] = None
    result_output: Optional[str] = None


class AuditTrailRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: f"audit-{uuid.uuid4().hex[:8]}")
    task_id: str
    actor: str
    action_taken: str  # SUBMITTED, APPROVED, REJECTED, EXECUTED
    timestamp: float = Field(default_factory=time.time)
    state_snapshot: Dict[str, Any]


class HITLWorkflowEngine:
    """Orchestrates research agent workflows with Human-in-the-Loop approval checkpoints."""

    def __init__(self, cost_threshold_usd: float = 0.20):
        self.cost_threshold = cost_threshold_usd
        self.pending_tasks: Dict[str, ActionTask] = {}
        self.completed_tasks: Dict[str, ActionTask] = {}
        self.audit_log: List[AuditTrailRecord] = []

    def submit_action(self, action_type: str, description: str, estimated_cost_usd: float, payload: Dict[str, Any], is_high_risk: bool = False) -> ActionTask:
        """Evaluates action safety and either auto-executes or pauses for human approval."""
        task = ActionTask(
            action_type=action_type,
            description=description,
            estimated_cost_usd=estimated_cost_usd,
            is_high_risk=is_high_risk,
            payload=payload
        )

        # Check if Human Approval is Required
        requires_approval = (estimated_cost_usd >= self.cost_threshold) or is_high_risk or (action_type in ["code_execution", "database_write", "deploy"])

        if requires_approval:
            task.status = ApprovalStatus.PENDING
            self.pending_tasks[task.task_id] = task
            self._log_audit(task.task_id, actor="AGENT", action_taken="PAUSED_FOR_HUMAN_APPROVAL", state=task.model_dump())
        else:
            task.status = ApprovalStatus.AUTO_EXECUTED
            task.result_output = f"Auto-executed low-risk task '{description}' successfully."
            task.resolution_time = time.time()
            task.resolved_by = "SYSTEM_AUTO_POLICY"
            self.completed_tasks[task.task_id] = task
            self._log_audit(task.task_id, actor="SYSTEM", action_taken="AUTO_EXECUTED", state=task.model_dump())

        return task

    def resolve_task(self, task_id: str, approve: bool, reviewer_id: str, reviewer_note: Optional[str] = None) -> ActionTask:
        """Human reviewer approves or rejects a pending execution task."""
        if task_id not in self.pending_tasks:
            raise KeyError(f"Task ID {task_id} not found in pending queue.")

        task = self.pending_tasks.pop(task_id)
        task.resolution_time = time.time()
        task.resolved_by = reviewer_id

        if approve:
            task.status = ApprovalStatus.APPROVED
            task.result_output = f"Approved by {reviewer_id}. Executed payload: {task.payload}. Note: {reviewer_note or 'N/A'}"
            self._log_audit(task_id, actor=reviewer_id, action_taken="HUMAN_APPROVED_AND_EXECUTED", state=task.model_dump())
        else:
            task.status = ApprovalStatus.REJECTED
            task.result_output = f"Task aborted by {reviewer_id}. Reason: {reviewer_note or 'Disapproved by human operator'}"
            self._log_audit(task_id, actor=reviewer_id, action_taken="HUMAN_REJECTED", state=task.model_dump())

        self.completed_tasks[task.task_id] = task
        return task

    def get_pending_queue(self) -> List[ActionTask]:
        return list(self.pending_tasks.values())

    def get_audit_trail(self) -> List[AuditTrailRecord]:
        return self.audit_log

    def _log_audit(self, task_id: str, actor: str, action_taken: str, state: Dict[str, Any]):
        record = AuditTrailRecord(
            task_id=task_id,
            actor=actor,
            action_taken=action_taken,
            state_snapshot=state
        )
        self.audit_log.append(record)
