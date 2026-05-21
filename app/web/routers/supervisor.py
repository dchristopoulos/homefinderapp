from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.authz_service import has_permission
from app.services.report_service import build_monthly_supervisor_report
from app.services.user_service import get_user_profile
from app.web.deps import (
    clear_session,
    get_session_user_id,
    is_valid_active_session,
    template_response,
)

router = APIRouter()


@router.get("/supervisor", response_class=HTMLResponse)
def supervisor_dashboard(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
):
    current_user_id = get_session_user_id(request)
    if current_user_id is None:
        return RedirectResponse(url="/login", status_code=303)

    user = get_user_profile(db, current_user_id)
    if user is None or not is_valid_active_session(request, user):
        clear_session(request)
        return RedirectResponse(url="/login", status_code=303)

    request.session["user_role"] = str(user.role)
    if not has_permission(
        user.role, "view_reports", user.permission_grants, user.permission_revokes
    ):
        return RedirectResponse(url="/dashboard", status_code=303)

    try:
        report = build_monthly_supervisor_report(db, year=year, month=month)
    except ValueError:
        return RedirectResponse(url="/supervisor", status_code=303)

    trend_peak = max(
        [
            max((item["inquiries"] for item in report["daily_trends"]), default=0),
            max(
                (item["saved_properties"] for item in report["daily_trends"]), default=0
            ),
            max((item["searches"] for item in report["daily_trends"]), default=0),
        ]
    )
    trend_bars = [
        {
            **item,
            "label": item["day"][-2:],
            "inquiry_height": 12
            if trend_peak == 0
            else 12 + int((int(item["inquiries"]) / trend_peak) * 68),
            "saved_height": 12
            if trend_peak == 0
            else 12 + int((int(item["saved_properties"]) / trend_peak) * 68),
            "search_height": 12
            if trend_peak == 0
            else 12 + int((int(item["searches"]) / trend_peak) * 68),
        }
        for item in report["daily_trends"]
    ]

    return template_response(
        request,
        "supervisor.html",
        {
            "user": user,
            "report": report,
            "trend_bars": trend_bars,
        },
    )
