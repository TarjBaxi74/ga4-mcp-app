from fastapi import APIRouter, Query
from ga4_client import get_client
from config import settings

router = APIRouter()


@router.get("/summary")
def get_summary():
    client = get_client()
    rows = client.run_report(
        property_id=settings.GA4_PROPERTY_ID,
        metrics=["activeUsers", "sessions"],
        dimensions=["date"],
        start_date="7daysAgo",
        end_date="today",
        limit=7,
    )

    return {"rows": rows}


@router.get("/report")
def get_report(
    metrics: str = Query(...),
    dimensions: str = Query("date"),
    start: str = Query("7daysAgo"),
    end: str = Query("today"),
):
    client = get_client()
    rows = client.run_report(
        property_id=settings.GA4_PROPERTY_ID,
        metrics=metrics.split(","),
        dimensions=dimensions.split(","),
        start_date=start,
        end_date=end,
    )

    return {"rows": rows}