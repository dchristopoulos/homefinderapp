from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import require_permission
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.report import MonthlySupervisorReportRead
from app.services.report_service import build_monthly_supervisor_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly", response_model=MonthlySupervisorReportRead)
def monthly_supervisor_report(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    _supervisor: User = Depends(require_permission("view_reports")),
):
    try:
        return build_monthly_supervisor_report(db, year=year, month=month)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
