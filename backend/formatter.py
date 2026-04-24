def format_summary(rows: list[dict]):
    if not rows:
        return "No data found"

    return f"Total rows: {len(rows)}"


def to_markdown_table(rows: list[dict]):
    if not rows:
        return "No data"

    headers = list(rows[0].keys())
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")

    return "\n".join(lines)