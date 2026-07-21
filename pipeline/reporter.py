"""Generate a Markdown summary report tying together cleaning stats,
analysis results, and links to generated visualizations.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from pipeline.config import get_logger

logger = get_logger(__name__)


def generate_report(analysis: dict, image_paths: list, output_path: str,
                     title: str = "Data Pipeline Report") -> str:
    """Render a Markdown report from analysis results and visualization paths.

    Args:
        analysis: Dict returned by analyzer.analyze_dataset (row_count,
            column_count, summary_statistics, correlations).
        image_paths: List of file paths to generated PNG visualizations.
        output_path: Where to write the .md report.
        title: Report title heading.

    Returns:
        The output_path the report was written to.
    """
    lines = [
        f"# {title}",
        "",
        f"_Generated: {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "## Dataset Overview",
        f"- Rows: {analysis.get('row_count', 'N/A')}",
        f"- Columns: {analysis.get('column_count', 'N/A')}",
        "",
        "## Summary Statistics",
    ]

    summary = analysis.get("summary_statistics")
    if isinstance(summary, pd.DataFrame) and not summary.empty:
        lines.append(summary.to_markdown())
    else:
        lines.append("_No numeric columns available for summary statistics._")

    lines += ["", "## Correlation Matrix"]
    corr = analysis.get("correlations")
    if isinstance(corr, pd.DataFrame) and not corr.empty:
        lines.append(corr.to_markdown())
    else:
        lines.append("_Not enough numeric columns to compute correlations._")

    lines += ["", "## Visualizations"]
    if image_paths:
        for path in image_paths:
            name = Path(path).stem.replace("_", " ").title()
            lines.append(f"- **{name}**: `{path}`")
    else:
        lines.append("_No visualizations were generated._")

    report_text = "\n\n".join(lines)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report_text, encoding="utf-8")

    logger.info("Report written to %s", output_path)
    return str(output_path)
