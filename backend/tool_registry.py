TOOLS = [
    {
        "name": "run_report",
        "description": "Run a GA4 report using metrics, dimensions, and date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": [
                "metrics",
                "dimensions",
                "start_date",
                "end_date",
            ],
        },
    },
    {
        "name": "get_metadata",
        "description": "Return supported GA4 metrics and dimensions.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]