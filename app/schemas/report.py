from pydantic import BaseModel


class TopSearchRead(BaseModel):
    query: str
    count: int


class ReportBucketRead(BaseModel):
    label: str
    count: int


class DailySupervisorTrendRead(BaseModel):
    day: str
    inquiries: int
    saved_properties: int
    searches: int


class MonthlySupervisorReportRead(BaseModel):
    year: int
    month: int
    period_label: str
    inquiries_count: int
    saved_properties_count: int
    search_count: int
    previous_inquiries_count: int
    previous_saved_properties_count: int
    previous_search_count: int
    inquiries_delta: int
    saved_properties_delta: int
    search_delta: int
    top_searches: list[TopSearchRead]
    top_locations: list[ReportBucketRead]
    most_saved_property_types: list[ReportBucketRead]
    most_saved_listings: list[ReportBucketRead]
    daily_trends: list[DailySupervisorTrendRead]
