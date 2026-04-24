from datetime import datetime


VALID_METRICS = {
    "activeUsers",
    "sessions",
    "screenPageViews",
    "bounceRate",
    "averageSessionDuration",
    "newUsers",
    "engagementRate",
}

VALID_DIMENSIONS = {
    "date",
    "country",
    "city",
    "pagePath",
    "deviceCategory",
    "sessionSource",
}

def normalize_date_range(text: str):
    text = text.lower()

    if "today" in text:
        return "today", "today"
    if "yesterday" in text:
        return "yesterday", "yesterday"
    if "this week" in text:
        return "7daysAgo", "today"
    if "last month" in text:
        return "30daysAgo", "today"

    return "7daysAgo", "today"


def validate_metrics(metrics: list[str]):
    invalid = [m for m in metrics if m not in VALID_METRICS]
    if invalid:
        raise ValueError(f"Invalid metrics: {invalid}")
    
def validate_dimensions(dimensions: list[str]):
    invalid = [d for d in dimensions if d not in VALID_DIMENSIONS]
    if invalid:
        raise ValueError(f"Invalid dimensions: {invalid}")