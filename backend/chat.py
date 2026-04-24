from fastapi import APIRouter
from pydantic import BaseModel
from google import genai 
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from config import settings
from auth import get_session_creds
from ga4_client import GA4Client
from datetime import date, timedelta
import json

router = APIRouter()
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    property_id: str
    session_id: str

# ─────────────────────────────────────────────
#  ROUTING PROMPT
# ─────────────────────────────────────────────
ROUTING_PROMPT = """You are a GA4 Data API expert. Given a user question, return ONLY a valid JSON object — no explanation, no markdown, no backticks, no thinking text.

=== GA4 METRICS REFERENCE ===
Use the correct GA4 API metric name. Common ones (not exhaustive):

USER METRICS:
  activeUsers, newUsers, totalUsers, dauPerMau, dauPerWau, wauPerMau

SESSION METRICS:
  sessions, sessionsPerUser, engagedSessions, averageSessionDuration, engagementRate

PAGE / SCREEN METRICS:
  screenPageViews, screenPageViewsPerSession, screenPageViewsPerUser

ECOMMERCE METRICS:
  totalRevenue, purchaseRevenue, ecommercePurchases, purchaseToViewRate,
  itemsAddedToCart, itemsPurchased, itemRevenue, itemsViewed, cartToViewRate,
  addToCarts, checkouts, transactions

BOUNCE & ENGAGEMENT:
  bounceRate, userEngagementDuration

ENGAGEMENT TIME METRICS:
  userEngagementDuration          — total engagement time in seconds (sum)
  averageSessionDuration          — average session duration (NOT engagement time)

  To get "average engagement time per user":
    metrics: ["userEngagementDuration", "activeUsers"]
    → then divide userEngagementDuration / activeUsers in the summary
  
  To get "average engagement time per session":
    metrics: ["userEngagementDuration", "sessions"]

EVENT METRICS:
  eventCount, eventCountPerUser, eventsPerSession, conversions, keyEvents

ACQUISITION:
  organicGoogleSearchClicks, organicGoogleSearchImpressions, organicGoogleSearchClickThroughRate

If the user asks for a metric not in this list, use the closest valid GA4 API camelCase metric name.
Multiple metrics are allowed when the question asks for more than one thing.

=== GA4 DIMENSIONS REFERENCE ===
Common dimensions (not exhaustive):
  date, dateHour, week, month, year
  country, city, region, continent
  deviceCategory, operatingSystem, browser, mobileDeviceModel
  pagePath, pageTitle, landingPage, exitPage
  sessionSource, sessionMedium, sessionCampaignName, sessionDefaultChannelGroup,
  firstUserSource, firstUserMedium, firstUserCampaignName
  eventName, itemName, itemCategory, itemBrand, itemId
  userAgeBracket, userGender

=== DEDUPLICATION RULE ===
- "total active users", "how many users", "unique users" over a period → dimensions: []
- "active users per day / daily / trend / over time" → dimensions: ["date"]
- NEVER use date dimension when user wants a single total — it causes double-counting

=== DATE FORMATTING ===
Today's date is {today}. Compute all relative dates from this exact date.

ABSOLUTE DATES:
- "today"                          → start_date: "today",        end_date: "today"
- "yesterday"                      → start_date: "yesterday",    end_date: "yesterday"
- specific date e.g. "20th march 2026" → start_date: "2026-03-20", end_date: "2026-03-20"
- date range e.g. "march 1 to march 20" → start_date: "2026-03-01", end_date: "2026-03-20"

LAST N DAYS (exclude today, match GA4 dashboard):
- "last 7 days"                    → start_date: "7daysAgo",     end_date: "yesterday"
- "last 28 days"                   → start_date: "28daysAgo",    end_date: "yesterday"
- "last 30 days"                   → start_date: "30daysAgo",    end_date: "yesterday"
- "last 90 days"                   → start_date: "90daysAgo",    end_date: "yesterday"
- "last 365 days"                  → start_date: "365daysAgo",   end_date: "yesterday"
- "last N days"                    → start_date: "NdaysAgo",     end_date: "yesterday"

THIS PERIOD (current incomplete period, exclude today):
- "this week" → start_date: most recent Sunday on or before {today} as YYYY-MM-DD, end_date: "yesterday"
  Example: if today is 2026-04-23 (Thursday), most recent Sunday = 2026-04-19
- "this month"                     → start_date: first day of current month as YYYY-MM-DD, end_date: "today"
- "this year"                      → start_date: January 1st of current year as YYYY-MM-DD, end_date: "today"
- "this quarter"                   → use current quarter boundaries:
    Q1 (Jan-Mar): start_date: "YYYY-01-01", end_date: "YYYY-03-31" or yesterday if still in Q1
    Q2 (Apr-Jun): start_date: "YYYY-04-01", end_date: "YYYY-06-30" or yesterday if still in Q2
    Q3 (Jul-Sep): start_date: "YYYY-07-01", end_date: "YYYY-09-30" or yesterday if still in Q3
    Q4 (Oct-Dec): start_date: "YYYY-10-01", end_date: "YYYY-12-31" or yesterday if still in Q4

LAST PERIOD (fully completed previous period):
- "last week"                      → return TWO interpretations as two separate queries if ambiguous,
                                     Mon-Sun: start_date: last Monday as YYYY-MM-DD, end_date: last Sunday as YYYY-MM-DD
                                     Sun-Sat: start_date: last Sunday as YYYY-MM-DD, end_date: last Saturday as YYYY-MM-DD
                                     Default to Mon-Sun unless user specifies otherwise
- "last month"                     → start_date: first day of previous month as YYYY-MM-DD,
                                     end_date: last day of previous month as YYYY-MM-DD
- "last year"                      → start_date: January 1st of previous year as YYYY-MM-DD,
                                     end_date: December 31st of previous year as YYYY-MM-DD
- "last quarter"                   → use previous quarter boundaries:
    If current is Q1: last quarter = Q4 of previous year: "YYYY-10-01" to "YYYY-12-31"
    If current is Q2: last quarter = Q1: "YYYY-01-01" to "YYYY-03-31"
    If current is Q3: last quarter = Q2: "YYYY-04-01" to "YYYY-06-30"
    If current is Q4: last quarter = Q3: "YYYY-07-01" to "YYYY-09-30"

QUARTER TO DATE:
- "Q1" / "Q1 to date"             → start_date: "YYYY-01-01", end_date: "YYYY-03-31" or yesterday if in Q1
- "Q2" / "Q2 to date"             → start_date: "YYYY-04-01", end_date: "YYYY-06-30" or yesterday if in Q2
- "Q3" / "Q3 to date"             → start_date: "YYYY-07-01", end_date: "YYYY-09-30" or yesterday if in Q3
- "Q4" / "Q4 to date"             → start_date: "YYYY-10-01", end_date: "YYYY-12-31" or yesterday if in Q4

IMPORTANT RULES:
- NEVER use "today" as end_date unless the user explicitly asks for today's data
- Always use "yesterday" as end_date for rolling and period queries to match GA4 dashboard
- For "this week/month/year", always compute the exact YYYY-MM-DD start date
- For "last week/month/year/quarter", always compute exact YYYY-MM-DD boundaries
- Current year is 2026. Compute all dates relative to today's actual date

=== INTENT → DIMENSION MAPPING ===
- "total / overall / how many / unique"         → dimensions: []
- "trend / over time / each day / daily"        → dimensions: ["date"]
- "by country / top countries"                  → dimensions: ["country"]
- "by city / top cities"                        → dimensions: ["city"]
- "by device / mobile vs desktop"               → dimensions: ["deviceCategory"]
- "top pages / most visited / best pages"       → dimensions: ["pagePath"]
- "landing page / entry page"                   → dimensions: ["landingPage"]
- "traffic source / where users came from"      → dimensions: ["sessionSource"]
- "by channel"                                  → dimensions: ["sessionDefaultChannelGroup"]
- "by campaign"                                 → dimensions: ["sessionCampaignName"]
- "products / items sold"                       → dimensions: ["itemName"]
- "by event"                                    → dimensions: ["eventName"]
- "average engagement time" → metrics: ["userEngagementDuration", "activeUsers"]
- "avg engagement time per session" → metrics: ["userEngagementDuration", "sessions"]
- "total engagement time" → metrics: ["userEngagementDuration"]

=== LIMIT RULES ===
- "top 5" / "least 5" / "bottom 5" → limit: 5
- "top 10" / "least 10"            → limit: 10
- "top N" / "least N"              → limit: N
- unspecified top/bottom           → limit: 10
- daily trends                     → limit: 90
- single aggregate (no dimension)  → limit: 1
- country/city breakdowns          → limit: 15

=== ORDERING ===
Use the "order_by" field to control sort direction.
Schema: {{ "metric": "<metricName>", "direction": "DESCENDING" | "ASCENDING" }}

- "top / highest / most / best / greatest" → direction: "DESCENDING"
- "least / lowest / worst / bottom / minimum" → direction: "ASCENDING"
- When order_by is not relevant (no ranking implied), omit the field entirely.

Examples:
  "top 5 pages by views"           → order_by: {{"metric": "screenPageViews", "direction": "DESCENDING"}}
  "lowest bounce rate by country"  → order_by: {{"metric": "bounceRate", "direction": "ASCENDING"}}
  "least selling products"         → order_by: {{"metric": "itemsPurchased", "direction": "ASCENDING"}}

=== FILTERS ===
Use "metric_filter" for numeric conditions on metrics (AFTER aggregation).
Use "dimension_filter" for matching/excluding specific dimension values.

metric_filter schema:
{{
  "metric_filter": {{
    "field": "<metricName>",
    "operation": "GREATER_THAN" | "LESS_THAN" | "GREATER_THAN_OR_EQUAL" | "LESS_THAN_OR_EQUAL" | "EQUAL",
    "value": <number>
  }}
}}

dimension_filter schema — single condition:
{{
  "dimension_filter": {{"field": "<dimensionName>", "operation": "EXACT" | "CONTAINS" | "BEGINS_WITH" | "ENDS_WITH" | "REGEXP", "value": "<string>"}}
}}

dimension_filter schema — multiple AND conditions:
{{
  "dimension_filter": [
    {{"field": "<dimensionName1>", "operation": "EXACT", "value": "<string1>"}},
    {{"field": "<dimensionName2>", "operation": "EXACT", "value": "<string2>"}}
  ]
}}

Both metric_filter and dimension_filter can be present simultaneously.
For multiple dimension conditions, ALWAYS use the list format.

Examples:
  "countries where revenue > 500"
    → metric_filter: {{"field":"totalRevenue","operation":"GREATER_THAN","value":500}}

  "pages containing /blog"
    → dimension_filter: {{"field":"pagePath","operation":"CONTAINS","value":"/blog"}}

  "users from organic search where sessions > 50"
    → dimension_filter: {{"field":"sessionDefaultChannelGroup","operation":"EXACT","value":"Organic Search"}},
       metric_filter: {{"field":"sessions","operation":"GREATER_THAN","value":50}}

  "top 3 cities where country is India and source is direct"
    → dimension_filter: [
        {{"field":"country","operation":"EXACT","value":"India"}},
        {{"field":"sessionSource","operation":"EXACT","value":"(direct)"}}
      ]

  "active users where device is mobile and country is India"
    → dimension_filter: [
        {{"field":"deviceCategory","operation":"EXACT","value":"mobile"}},
        {{"field":"country","operation":"EXACT","value":"India"}}
      ]

=== GA4 SOURCE/MEDIUM VALUE FORMATS ===
GA4 stores traffic sources with specific formatting — always use these exact values:
  sessionSource = "(direct)"        NOT "direct"
  sessionSource = "google"          NOT "Google"
  sessionMedium = "(none)"          for direct traffic medium
  sessionMedium = "organic"         for organic search
  sessionMedium = "cpc"             for paid search
  sessionDefaultChannelGroup = "Direct"            (capital D)
  sessionDefaultChannelGroup = "Organic Search"    (exact casing)
  sessionDefaultChannelGroup = "Paid Search"       (exact casing)
  sessionDefaultChannelGroup = "Referral"          (exact casing)
  sessionDefaultChannelGroup = "Email"             (exact casing)
  sessionDefaultChannelGroup = "Social"            (exact casing)

So "direct traffic" or "source is direct" → sessionSource EXACT "(direct)"
And "organic search" → sessionDefaultChannelGroup EXACT "Organic Search"

=== OUTPUT FORMAT ===
Return ONLY this JSON — include only fields that apply, omit optional ones that aren't needed:

{{
  "metrics": ["metric1", "metric2"],
  "dimensions": ["dimension1"],
  "start_date": "...",
  "end_date": "...",
  "limit": 10,
  "order_by": {{"metric": "metricName", "direction": "DESCENDING"}},
  "metric_filter": {{"field": "metricName", "operation": "GREATER_THAN", "value": 100}},
  "dimension_filter": {{"field": "dimensionName", "operation": "EXACT", "value": "someValue"}}
}}

User question: {question}"""


# ─────────────────────────────────────────────
#  SUMMARY PROMPT
# ─────────────────────────────────────────────
SUMMARY_PROMPT = """You are a GA4 analytics assistant. Answer the user's question directly and concisely using the data provided.

User question: "{question}"

GA4 data returned:
{data}

Instructions:
- Answer the question directly in 2-3 sentences
- Highlight the single most important number or insight
- If the data contains both userEngagementDuration and activeUsers, compute average engagement time as userEngagementDuration / activeUsers and present it in seconds or minutes
- If the data contains both userEngagementDuration and sessions, compute average engagement time as userEngagementDuration / sessions
- If filters were applied (e.g. revenue > X), mention that in your answer naturally
- If data is empty or None, say no data was found for that period/filter combination
- Do not mention technical terms like metrics, dimensions, filters, or API
- Speak naturally as if explaining to a business owner"""


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_ga4_for_session(session_id: str) -> GA4Client:
    """Build a GA4Client using the user's OAuth session credentials."""
    creds = get_session_creds(session_id)
    ga4 = GA4Client.__new__(GA4Client)
    ga4.client = BetaAnalyticsDataClient(credentials=creds)
    return ga4

def get_date_context(today: date) -> dict:
    """Pre-compute all common date ranges so Gemini never has to calculate them."""
    yesterday = today - timedelta(days=1)

    # This week (Sunday as start)
    days_since_sunday = (today.weekday() + 1) % 7
    this_week_start = today - timedelta(days=days_since_sunday)

    # This month
    this_month_start = today.replace(day=1)

    # This year
    this_year_start = today.replace(month=1, day=1)

    # This quarter
    quarter = (today.month - 1) // 3
    quarter_start_month = quarter * 3 + 1
    this_quarter_start = today.replace(month=quarter_start_month, day=1)

    # Last week (Mon-Sun)
    last_week_end = today - timedelta(days=today.weekday() + 1)  # last Sunday
    last_week_start = last_week_end - timedelta(days=6)           # last Monday

    # Last month
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    # Last year
    last_year_start = today.replace(year=today.year - 1, month=1, day=1)
    last_year_end = today.replace(year=today.year - 1, month=12, day=31)

    # Last quarter
    last_quarter = quarter - 1 if quarter > 0 else 3
    last_quarter_year = today.year if quarter > 0 else today.year - 1
    last_quarter_start_month = last_quarter * 3 + 1
    last_quarter_end_month = last_quarter_start_month + 2
    import calendar
    last_quarter_end_day = calendar.monthrange(last_quarter_year, last_quarter_end_month)[1]
    last_quarter_start = date(last_quarter_year, last_quarter_start_month, 1)
    last_quarter_end = date(last_quarter_year, last_quarter_end_month, last_quarter_end_day)

    return {
        "today": today.strftime("%Y-%m-%d"),
        "yesterday": yesterday.strftime("%Y-%m-%d"),
        "this_week_start": this_week_start.strftime("%Y-%m-%d"),
        "this_month_start": this_month_start.strftime("%Y-%m-%d"),
        "this_year_start": this_year_start.strftime("%Y-%m-%d"),
        "this_quarter_start": this_quarter_start.strftime("%Y-%m-%d"),
        "last_week_start": last_week_start.strftime("%Y-%m-%d"),
        "last_week_end": last_week_end.strftime("%Y-%m-%d"),
        "last_month_start": last_month_start.strftime("%Y-%m-%d"),
        "last_month_end": last_month_end.strftime("%Y-%m-%d"),
        "last_year_start": last_year_start.strftime("%Y-%m-%d"),
        "last_year_end": last_year_end.strftime("%Y-%m-%d"),
        "last_quarter_start": last_quarter_start.strftime("%Y-%m-%d"),
        "last_quarter_end": last_quarter_end.strftime("%Y-%m-%d"),
    }


def build_params(question: str) -> dict:
    today = date.today()
    ctx = get_date_context(today)

    # Replace the vague date instructions with pre-computed exact values
    date_context_str = f"""
=== PRE-COMPUTED DATE RANGES (use these exact values, do NOT recalculate) ===
today              = {ctx['today']}
yesterday          = {ctx['yesterday']}

this week          → start_date: "{ctx['this_week_start']}",  end_date: "{ctx['today']}"
this month         → start_date: "{ctx['this_month_start']}", end_date: "{ctx['today']}"
this year          → start_date: "{ctx['this_year_start']}",  end_date: "{ctx['today']}"
this quarter       → start_date: "{ctx['this_quarter_start']}",end_date: "{ctx['today']}"

last week          → start_date: "{ctx['last_week_start']}",  end_date: "{ctx['last_week_end']}"
last month         → start_date: "{ctx['last_month_start']}", end_date: "{ctx['last_month_end']}"
last year          → start_date: "{ctx['last_year_start']}",  end_date: "{ctx['last_year_end']}"
last quarter       → start_date: "{ctx['last_quarter_start']}",end_date: "{ctx['last_quarter_end']}"

last 7 days        → start_date: "7daysAgo",   end_date: "yesterday"
last 28 days       → start_date: "28daysAgo",  end_date: "yesterday"
last 30 days       → start_date: "30daysAgo",  end_date: "yesterday"
last 90 days       → start_date: "90daysAgo",  end_date: "yesterday"
last N days        → start_date: "NdaysAgo",   end_date: "yesterday"

RULE: NEVER compute dates yourself. Always use the exact values above.
"""

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=ROUTING_PROMPT.format(question=question, today=ctx['today']) + date_context_str
    )
    raw = response.text.strip()

    # strip thinking tags (gemini 2.5 pro)
    if "<think>" in raw:
        raw = raw.split("</think>")[-1].strip()

    # strip markdown fences
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    params = json.loads(raw.strip())
    print("🔍 QUERY PARAMS:", json.dumps(params, indent=2))
    return params


def summarize(question: str, data: list) -> str:
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=SUMMARY_PROMPT.format(question=question, data=data)
    )
    return response.text.strip()


def fetch_deduplicated_total(ga4: GA4Client, property_id: str, params: dict) -> str | None:
    """For activeUsers with date dimension, fetch the true unique total separately."""
    try:
        total_data = ga4.run_report(
            property_id=property_id,
            metrics=["activeUsers"],
            dimensions=[],
            start_date=params["start_date"],
            end_date=params["end_date"],
            limit=1,
        )
        if total_data:
            return total_data[0].get("activeUsers")
    except Exception:
        pass
    return None


def build_tool_params(params: dict) -> dict:
    """Translate LLM output into the exact shape ga4.run_report expects."""
    tool_params: dict = {
        "metrics":    params["metrics"],
        "dimensions": params.get("dimensions", []),
        "start_date": params["start_date"],
        "end_date":   params["end_date"],
        "limit":      params.get("limit", 10),
    }
    if "order_by" in params:
        tool_params["order_by"] = params["order_by"]
    if "metric_filter" in params:
        tool_params["metric_filter"] = params["metric_filter"]
    if "dimension_filter" in params:
        tool_params["dimension_filter"] = params["dimension_filter"]
    return tool_params


def build_tool_label(params: dict) -> str:
    """Build a human-readable badge label showing any filters applied."""
    if "metric_filter" not in params and "dimension_filter" not in params:
        return "run_report"

    filters = []
    op_map = {
        "GREATER_THAN": ">", "LESS_THAN": "<",
        "GREATER_THAN_OR_EQUAL": ">=", "LESS_THAN_OR_EQUAL": "<=",
        "EQUAL": "=",
    }

    if mf := params.get("metric_filter"):
        filters.append(
            f"{mf['field']} {op_map.get(mf['operation'], mf['operation'])} {mf['value']}"
        )

    if df := params.get("dimension_filter"):
        if isinstance(df, list):
            filters.append(" AND ".join(
                f"{c['field']}={c['value']}" for c in df
            ))
        else:
            filters.append(f"{df['field']} {df['operation'].lower()} '{df['value']}'")

    return f"run_report · {', '.join(filters)}"


# ─────────────────────────────────────────────
#  ROUTE
# ─────────────────────────────────────────────
@router.post("")
def chat(req: ChatRequest):
    try:
        # Build GA4 client from user's OAuth session credentials
        ga4 = get_ga4_for_session(req.session_id)
        property_id = f"properties/{req.property_id}" if not req.property_id.startswith("properties/") else req.property_id

        # Step 1 — Gemini builds GA4 query params from natural language
        params = build_params(req.message)

        # Step 2 — translate to run_report shape and execute
        tool_params = build_tool_params(params)
        raw_data = ga4.run_report(
            property_id=property_id,
            metrics=tool_params["metrics"],
            dimensions=tool_params["dimensions"],
            start_date=tool_params["start_date"],
            end_date=tool_params["end_date"],
            limit=tool_params.get("limit", 10),
            order_by=tool_params.get("order_by"),
            metric_filter=tool_params.get("metric_filter"),
            dimension_filter=tool_params.get("dimension_filter"),
        )

        # Step 3 — fix activeUsers double-counting when date dimension is present
        prefix = ""
        if (
            "activeUsers" in params.get("metrics", [])
            and "date" in params.get("dimensions", [])
        ):
            total = fetch_deduplicated_total(ga4, property_id, params)
            if total:
                prefix = f"Total unique active users: **{total}**\n\n"

        # Step 4 — Gemini summarizes result in plain English
        reply = summarize(req.message, raw_data)

        return {
            "reply": prefix + reply,
            "data": raw_data,
            "tool_used": build_tool_label(params),
        }

    except json.JSONDecodeError as e:
        print("JSON PARSE ERROR:", e)
        return {
            "reply": "I couldn't parse that query. Try something like: 'top 3 cities where country is India and source is direct last 90 days', or 'sessions by country where sessions > 50 last 30 days'.",
            "data": None,
            "tool_used": None,
        }

    except Exception as e:
        import traceback
        print("CHAT ERROR:", traceback.format_exc())
        return {
            "reply": f"Error: {str(e)}",
            "data": None,
            "tool_used": None,
        }