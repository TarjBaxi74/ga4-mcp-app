import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric,
    Dimension,
    OrderBy,
    FilterExpression,
    FilterExpressionList,
    Filter,
    NumericValue,
)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# -----------------------------
# CONFIG
# -----------------------------
TOKEN_FILE = "credentials/token.json"
CLIENT_SECRET_FILE = "credentials/oauth-client.json"
SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
]

# -----------------------------
# OAuth (Cloud Run safe version)
# -----------------------------
def get_oauth_credentials():
    """
    ⚠️ Cloud Run SAFE VERSION

    - No local browser
    - No token.json dependency
    - OAuth will be handled via frontend redirect flow later

    This prevents container crash at startup.
    """
    return None


# -----------------------------
# FILTER MAPS (UNCHANGED)
# -----------------------------
STR_OP_MAP = {
    "EXACT": Filter.StringFilter.MatchType.EXACT,
    "CONTAINS": Filter.StringFilter.MatchType.CONTAINS,
    "BEGINS_WITH": Filter.StringFilter.MatchType.BEGINS_WITH,
    "ENDS_WITH": Filter.StringFilter.MatchType.ENDS_WITH,
    "REGEXP": Filter.StringFilter.MatchType.FULL_REGEXP,
}

NUM_OP_MAP = {
    "GREATER_THAN": Filter.NumericFilter.Operation.GREATER_THAN,
    "LESS_THAN": Filter.NumericFilter.Operation.LESS_THAN,
    "GREATER_THAN_OR_EQUAL": Filter.NumericFilter.Operation.GREATER_THAN_OR_EQUAL,
    "LESS_THAN_OR_EQUAL": Filter.NumericFilter.Operation.LESS_THAN_OR_EQUAL,
    "EQUAL": Filter.NumericFilter.Operation.EQUAL,
}


# -----------------------------
# FILTER BUILDERS (UNCHANGED)
# -----------------------------
def _build_single_dim_filter(f: dict) -> FilterExpression:
    return FilterExpression(
        filter=Filter(
            field_name=f["field"],
            string_filter=Filter.StringFilter(
                match_type=STR_OP_MAP[f["operation"]],
                value=f["value"],
            ),
        )
    )


def _build_dim_filter(dimension_filter) -> FilterExpression | None:
    if dimension_filter is None:
        return None

    if isinstance(dimension_filter, dict) and "and" in dimension_filter:
        conditions = dimension_filter["and"]
        if len(conditions) == 1:
            return _build_single_dim_filter(conditions[0])
        return FilterExpression(
            and_group=FilterExpressionList(
                expressions=[_build_single_dim_filter(c) for c in conditions]
            )
        )

    if isinstance(dimension_filter, list):
        if len(dimension_filter) == 1:
            return _build_single_dim_filter(dimension_filter[0])
        return FilterExpression(
            and_group=FilterExpressionList(
                expressions=[_build_single_dim_filter(c) for c in dimension_filter]
            )
        )

    if isinstance(dimension_filter, dict) and "field" in dimension_filter:
        return _build_single_dim_filter(dimension_filter)

    return None


def _build_metric_filter(metric_filter: dict) -> FilterExpression | None:
    if not metric_filter:
        return None
    return FilterExpression(
        filter=Filter(
            field_name=metric_filter["field"],
            numeric_filter=Filter.NumericFilter(
                operation=NUM_OP_MAP[metric_filter["operation"]],
                value=NumericValue(double_value=float(metric_filter["value"])),
            ),
        )
    )


# -----------------------------
# GA4 CLIENT (SAFE INIT)
# -----------------------------
class GA4Client:
    def __init__(self, creds=None):
        """
        creds = None → safe startup (Cloud Run)
        creds provided → full GA4 access
        """
        if creds:
            self.client = BetaAnalyticsDataClient(credentials=creds)
        else:
            # fallback to default (prevents crash)
            self.client = BetaAnalyticsDataClient()

    def run_report(
        self,
        property_id: str,
        metrics: list[str],
        dimensions: list[str],
        start_date: str,
        end_date: str,
        limit: int = 10,
        order_by: dict = None,
        metric_filter: dict = None,
        dimension_filter=None,
    ):
        order_bys = []
        if order_by:
            order_bys = [OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name=order_by["metric"]),
                desc=(order_by["direction"] == "DESCENDING"),
            )]

        request = RunReportRequest(
            property=property_id,
            metrics=[Metric(name=m) for m in metrics],
            dimensions=[Dimension(name=d) for d in dimensions],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            limit=limit,
            order_bys=order_bys,
            metric_filter=_build_metric_filter(metric_filter),
            dimension_filter=_build_dim_filter(dimension_filter),
        )

        response = self.client.run_report(request)

        rows = []
        for row in response.rows:
            record = {}
            for i, dim in enumerate(dimensions):
                record[dim] = row.dimension_values[i].value
            for i, metric in enumerate(metrics):
                record[metric] = row.metric_values[i].value
            rows.append(record)

        return rows


# -----------------------------
# LAZY CLIENT (IMPORTANT)
# -----------------------------
def get_client(creds=None):
    return GA4Client(creds)