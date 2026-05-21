from __future__ import annotations

import json
from calendar import monthrange
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.favorite_service import all_favorites_use_case
from app.services.inquiry_service import all_inquiries_use_case
from app.services.search_service import list_search_logs_use_case


def _as_naive_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _month_window(
    year: int | None = None, month: int | None = None
) -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    selected_year = year or now.year
    selected_month = month or now.month
    if selected_month < 1 or selected_month > 12:
        raise ValueError("month must be between 1 and 12")
    start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        end = datetime(selected_year + 1, 1, 1)
    else:
        end = datetime(selected_year, selected_month + 1, 1)
    return start, end


def _previous_month_window(start: datetime) -> tuple[datetime, datetime]:
    if start.month == 1:
        return datetime(start.year - 1, 12, 1), start
    return datetime(start.year, start.month - 1, 1), start


def _in_window(value: datetime | None, start: datetime, end: datetime) -> bool:
    normalized = _as_naive_utc(value)
    return normalized is not None and start <= normalized < end


def _parse_search_filters(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _bucket_counts(
    counter: Counter[str], *, limit: int = 10
) -> list[dict[str, int | str]]:
    return [
        {"label": label, "count": count} for label, count in counter.most_common(limit)
    ]


def build_monthly_supervisor_report(
    db: Session,
    *,
    year: int | None = None,
    month: int | None = None,
) -> dict[str, Any]:
    start, end = _month_window(year, month)
    previous_start, previous_end = _previous_month_window(start)

    inquiries = all_inquiries_use_case(db)
    favorites = all_favorites_use_case(db)
    search_logs = list_search_logs_use_case(db)

    current_inquiries = [
        item
        for item in inquiries
        if _in_window(getattr(item, "created_at", None), start, end)
    ]
    current_favorites = [
        item
        for item in favorites
        if _in_window(getattr(item, "created_at", None), start, end)
    ]
    current_search_logs = [
        item
        for item in search_logs
        if _in_window(getattr(item, "created_at", None), start, end)
    ]

    previous_inquiries = [
        item
        for item in inquiries
        if _in_window(getattr(item, "created_at", None), previous_start, previous_end)
    ]
    previous_favorites = [
        item
        for item in favorites
        if _in_window(getattr(item, "created_at", None), previous_start, previous_end)
    ]
    previous_search_logs = [
        item
        for item in search_logs
        if _in_window(getattr(item, "created_at", None), previous_start, previous_end)
    ]

    search_counter = Counter(
        str(item.query).strip()
        for item in current_search_logs
        if str(getattr(item, "query", "")).strip()
    )
    location_counter = Counter()
    for log in current_search_logs:
        filters = _parse_search_filters(getattr(log, "filters", None))
        location = str(filters.get("location") or "").strip()
        if location:
            location_counter[location] += 1

    property_type_counter = Counter(
        str(getattr(getattr(item, "listing", None), "property_type", "")).strip()
        for item in current_favorites
        if str(getattr(getattr(item, "listing", None), "property_type", "")).strip()
    )
    saved_listing_counter = Counter(
        str(getattr(getattr(item, "listing", None), "title", "")).strip()
        for item in current_favorites
        if str(getattr(getattr(item, "listing", None), "title", "")).strip()
    )

    days_in_month = monthrange(start.year, start.month)[1]
    daily_trends = []
    for day in range(1, days_in_month + 1):
        day_start = datetime(start.year, start.month, day)
        day_end = (
            end if day == days_in_month else datetime(start.year, start.month, day + 1)
        )
        daily_trends.append(
            {
                "day": day_start.strftime("%Y-%m-%d"),
                "inquiries": sum(
                    1
                    for item in current_inquiries
                    if _in_window(getattr(item, "created_at", None), day_start, day_end)
                ),
                "saved_properties": sum(
                    1
                    for item in current_favorites
                    if _in_window(getattr(item, "created_at", None), day_start, day_end)
                ),
                "searches": sum(
                    1
                    for item in current_search_logs
                    if _in_window(getattr(item, "created_at", None), day_start, day_end)
                ),
            }
        )

    return {
        "year": start.year,
        "month": start.month,
        "period_label": start.strftime("%B %Y"),
        "inquiries_count": len(current_inquiries),
        "saved_properties_count": len(current_favorites),
        "search_count": len(current_search_logs),
        "previous_inquiries_count": len(previous_inquiries),
        "previous_saved_properties_count": len(previous_favorites),
        "previous_search_count": len(previous_search_logs),
        "inquiries_delta": len(current_inquiries) - len(previous_inquiries),
        "saved_properties_delta": len(current_favorites) - len(previous_favorites),
        "search_delta": len(current_search_logs) - len(previous_search_logs),
        "top_searches": [
            {"query": query, "count": count}
            for query, count in search_counter.most_common(10)
        ],
        "top_locations": _bucket_counts(location_counter, limit=8),
        "most_saved_property_types": _bucket_counts(property_type_counter, limit=8),
        "most_saved_listings": _bucket_counts(saved_listing_counter, limit=8),
        "daily_trends": daily_trends,
    }
