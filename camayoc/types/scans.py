from __future__ import annotations

from enum import Enum
from typing import Optional

from attrs import frozen

from .settings import ScanOptions


class ScanSimplifiedStatusEnum(Enum):
    CREATED = "created"
    COMPLETED = "completed"
    FAILED = "failed"


@frozen
class FinishedScan:
    scan_id: int
    scan_job_id: int
    status: ScanSimplifiedStatusEnum
    definition: ScanOptions
    report_id: Optional[int] = None
    details_report: Optional[dict] = None
    deployments_report: Optional[dict] = None
    error: Optional[Exception] = None
