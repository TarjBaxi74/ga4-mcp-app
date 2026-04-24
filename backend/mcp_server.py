from config import settings
from ga4_client import client


def run_tool(name: str, inputs: dict):
    if name == "run_report":
        return client.run_report(
            property_id=settings.GA4_PROPERTY_ID,
            metrics=inputs["metrics"],
            dimensions=inputs["dimensions"],
            start_date=inputs["start_date"],
            end_date=inputs["end_date"],
            limit=inputs.get("limit", 10),
            order_by=inputs.get("order_by"),
            metric_filter=inputs.get("metric_filter"),
            dimension_filter=inputs.get("dimension_filter"),
        )

    if name == "get_metadata":
        return {
            "metrics": [
                "activeUsers", "newUsers", "totalUsers", "sessions",
                "bounceRate", "engagementRate", "screenPageViews",
                "totalRevenue", "ecommercePurchases", "eventCount",
            ],
            "dimensions": [
                "date", "country", "city", "pagePath", "deviceCategory",
                "sessionSource", "sessionMedium", "sessionDefaultChannelGroup",
                "sessionCampaignName", "eventName", "itemName",
            ],
        }

    raise ValueError(f"Unknown tool: {name}")