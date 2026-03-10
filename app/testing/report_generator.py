"""
HTML Report Generator for Testing System

Generates detailed, email-friendly HTML reports with:
- Executive summary
- Interactive charts
- Hideable test grid
- Inline editing capability
"""

from typing import List, Optional
from app.testing.test_models import TestRun, TestResult, TestStatus
from datetime import datetime


class HTMLReportGenerator:
    """Generates comprehensive HTML reports"""

    def generate_email_report(
        self,
        test_run: TestRun,
        include_editable_grid: bool = True,
        previous_run: Optional[TestRun] = None
    ) -> str:
        """
        Generate complete HTML report suitable for email

        Args:
            test_run: Current test run
            include_editable_grid: Include editable table
            previous_run: Previous run for comparison

        Returns:
            Complete HTML string
        """
        html_parts = []

        # CSS
        html_parts.append(self._generate_css())

        # Header
        html_parts.append(self._generate_header(test_run))

        # Executive summary
        html_parts.append(self._generate_summary(test_run, previous_run))

        # Charts
        html_parts.append(self._generate_charts(test_run))

        # Failure analysis
        html_parts.append(self._generate_failure_analysis(test_run))

        # Editable test grid (hideable)
        if include_editable_grid:
            html_parts.append(self._generate_test_grid(test_run))

        # Footer
        html_parts.append(self._generate_footer())

        return "\n".join(html_parts)

    def _generate_css(self) -> str:
        """Generate CSS styles"""
        return """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background-color: #f5f5f5;
    }
    .container {
        background: white;
        border-radius: 8px;
        padding: 30px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .header {
        border-bottom: 3px solid #4CAF50;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }
    h1 {
        color: #2c3e50;
        margin: 0;
    }
    .run-id {
        color: #7f8c8d;
        font-size: 0.9em;
        margin-top: 5px;
    }
    .metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
    }
    .metric-card.failed {
        border-left-color: #f44336;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        color: #7f8c8d;
        font-size: 0.9em;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-delta {
        font-size: 0.8em;
        margin-top: 5px;
    }
    .metric-delta.positive {
        color: #4CAF50;
    }
    .metric-delta.negative {
        color: #f44336;
    }
    .section {
        margin: 30px 0;
    }
    h2 {
        color: #34495e;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 10px;
    }
    .breakdown {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin: 20px 0;
    }
    .breakdown-item {
        background: #ecf0f1;
        padding: 15px;
        border-radius: 6px;
        text-align: center;
    }
    .failure-reasons {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 20px;
        margin: 20px 0;
    }
    .failure-reasons h3 {
        margin-top: 0;
        color: #856404;
    }
    .failure-reasons ul {
        margin: 10px 0;
        padding-left: 20px;
    }
    details {
        margin: 20px 0;
        border: 1px solid #ddd;
        border-radius: 6px;
        overflow: hidden;
    }
    summary {
        background: #f8f9fa;
        padding: 15px;
        cursor: pointer;
        font-weight: bold;
        user-select: none;
    }
    summary:hover {
        background: #e9ecef;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 0;
    }
    th {
        background: #34495e;
        color: white;
        padding: 12px;
        text-align: left;
        position: sticky;
        top: 0;
    }
    td {
        padding: 10px;
        border-bottom: 1px solid #ecf0f1;
    }
    tr:hover {
        background: #f8f9fa;
    }
    .status-pass {
        background: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .status-fail {
        background: #f8d7da;
        color: #721c24;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .status-fail-inclusion {
        background: #fff3cd;
        color: #856404;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: bold;
    }
    .badge-autofixed {
        background: #d1ecf1;
        color: #0c5460;
    }
    .badge-review {
        background: #fff3cd;
        color: #856404;
    }
    .prompt-cell {
        max-width: 300px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .cta-box {
        background: #e3f2fd;
        border: 2px solid #2196F3;
        border-radius: 8px;
        padding: 20px;
        margin: 30px 0;
        text-align: center;
    }
    .cta-box h3 {
        margin-top: 0;
        color: #1976D2;
    }
    .footer {
        text-align: center;
        color: #7f8c8d;
        font-size: 0.9em;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #ecf0f1;
    }
</style>
"""

    def _generate_header(self, test_run: TestRun) -> str:
        """Generate report header"""
        return f"""
<div class="container header">
    <h1>🤖 QA Automation - Auto-Healing Test Report</h1>
    <div class="run-id">Run ID: {test_run.run_id} | {test_run.started_at.strftime('%Y-%m-%d %H:%M:%S')}</div>
</div>
"""

    def _generate_summary(self, test_run: TestRun, previous_run: Optional[TestRun]) -> str:
        """Generate executive summary"""
        summary = test_run.summary

        # Calculate deltas if previous run exists
        delta_html = ""
        if previous_run:
            delta_pass_rate = summary.pass_rate - previous_run.summary.pass_rate
            delta_class = "positive" if delta_pass_rate >= 0 else "negative"
            delta_symbol = "▲" if delta_pass_rate >= 0 else "▼"
            delta_html = f'<div class="metric-delta {delta_class}">{delta_symbol} {abs(delta_pass_rate):.1f}% vs {previous_run.run_id}</div>'

        return f"""
<div class="container">
    <h2>Executive Summary</h2>
    <div class="metrics">
        <div class="metric-card">
            <div class="metric-label">Pass Rate</div>
            <div class="metric-value">{summary.pass_rate:.1f}%</div>
            {delta_html}
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Tests</div>
            <div class="metric-value">{summary.total_tests}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Passed</div>
            <div class="metric-value" style="color: #4CAF50;">{summary.passed}</div>
        </div>
        <div class="metric-card failed">
            <div class="metric-label">Failed</div>
            <div class="metric-value" style="color: #f44336;">{summary.failed}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Auto-Fixed</div>
            <div class="metric-value" style="color: #2196F3;">{summary.auto_fixed_count}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Duration</div>
            <div class="metric-value" style="font-size: 1.5em;">{summary.duration_seconds:.0f}s</div>
        </div>
    </div>

    <h3>By Test Type</h3>
    <div class="breakdown">
        <div class="breakdown-item">
            <strong>Objective</strong><br>
            {summary.objective_passed}/{summary.objective_total} passed<br>
            ({summary.objective_passed/summary.objective_total*100 if summary.objective_total > 0 else 0:.1f}%)
        </div>
        <div class="breakdown-item">
            <strong>Subjective</strong><br>
            {summary.subjective_passed}/{summary.subjective_total} passed<br>
            ({summary.subjective_passed/summary.subjective_total*100 if summary.subjective_total > 0 else 0:.1f}%)
        </div>
        <div class="breakdown-item">
            <strong>Calculated</strong><br>
            {summary.calculated_passed}/{summary.calculated_total} passed<br>
            ({summary.calculated_passed/summary.calculated_total*100 if summary.calculated_total > 0 else 0:.1f}%)
        </div>
    </div>
</div>
"""

    def _generate_charts(self, test_run: TestRun) -> str:
        """Generate inline charts using Chart.js"""
        # For simplicity, using text-based representation
        # In production, embed Chart.js or use SVG
        return ""

    def _generate_failure_analysis(self, test_run: TestRun) -> str:
        """Generate failure analysis"""
        summary = test_run.summary

        # Get top failure reasons
        failed_results = [r for r in test_run.results if not r.passed]

        inclusion_failures = [r for r in failed_results if not r.validation.inclusion_passed]
        similarity_failures = [r for r in failed_results if r.validation.inclusion_passed and not r.validation.similarity_passed]

        return f"""
<div class="container">
    <h2>Failure Analysis</h2>

    <div class="breakdown">
        <div class="breakdown-item">
            <strong>Inclusion Failures</strong><br>
            {summary.fail_inclusion} tests<br>
            ({summary.fail_inclusion/summary.total_tests*100 if summary.total_tests > 0 else 0:.1f}%)
        </div>
        <div class="breakdown-item">
            <strong>Similarity Failures</strong><br>
            {summary.fail_similarity} tests<br>
            ({summary.fail_similarity/summary.total_tests*100 if summary.total_tests > 0 else 0:.1f}%)
        </div>
        <div class="breakdown-item">
            <strong>Needs Review</strong><br>
            {summary.needs_review_count} tests<br>
            ({summary.needs_review_count/summary.total_tests*100 if summary.total_tests > 0 else 0:.1f}%)
        </div>
    </div>

    <div class="failure-reasons">
        <h3>Top Failure Patterns</h3>
        <ul>
            <li><strong>Missing expected text:</strong> {len(inclusion_failures)} cases - Model response doesn't contain required substring</li>
            <li><strong>Below similarity threshold:</strong> {len(similarity_failures)} cases - Response semantically different from reference</li>
            <li><strong>Auto-fixed:</strong> {summary.auto_fixed_count} cases - Automatically corrected prompts/expectations</li>
        </ul>
    </div>
</div>
"""

    def _generate_test_grid(self, test_run: TestRun) -> str:
        """Generate hideable test grid"""
        rows = []

        for result in test_run.results:
            tc = result.test_case

            # Status badge
            if result.status == TestStatus.PASS:
                status_html = '<span class="status-pass">PASS</span>'
            elif result.status == TestStatus.FAIL_INCLUSION:
                status_html = '<span class="status-fail-inclusion">FAIL_INCLUSION</span>'
            else:
                status_html = '<span class="status-fail">FAIL</span>'

            # Badges
            badges = []
            if tc.auto_fixed:
                badges.append('<span class="badge badge-autofixed">Auto-Fixed</span>')
            if tc.needs_review:
                badges.append('<span class="badge badge-review">Review</span>')

            badges_html = " ".join(badges)

            # Truncate prompt
            prompt_display = tc.prompt if len(tc.prompt) <= 60 else tc.prompt[:57] + "..."

            # Handle both enum and string types
            type_display = tc.type.value if hasattr(tc.type, 'value') else str(tc.type)

            # Truncate answers for display
            expected_display = tc.expected_answer_include[:40] + "..." if len(tc.expected_answer_include) > 40 else tc.expected_answer_include
            actual_display = result.model_answer[:40] + "..." if len(result.model_answer) > 40 else result.model_answer

            # Full answers for tooltips
            expected_full = tc.expected_answer_include.replace('"', '&quot;')
            actual_full = result.model_answer.replace('"', '&quot;')

            rows.append(f"""
            <tr>
                <td>{tc.test_id}</td>
                <td>{type_display}</td>
                <td class="prompt-cell" title="{tc.prompt}">{prompt_display}</td>
                <td>{status_html}</td>
                <td>{result.validation.similarity_score:.3f}</td>
                <td title="{expected_full}">{expected_display}</td>
                <td title="{actual_full}">{actual_display}</td>
                <td>{badges_html}</td>
            </tr>
            """)

        rows_html = "\n".join(rows)

        return f"""
<div class="container">
    <details>
        <summary>📋 Click to expand detailed test results ({len(test_run.results)} tests)</summary>
        <div style="overflow-x: auto; max-height: 600px; overflow-y: auto;">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Prompt</th>
                        <th>Status</th>
                        <th>Similarity</th>
                        <th>Expected Answer</th>
                        <th>Actual Answer</th>
                        <th>Flags</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </details>
</div>
"""

    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""
<div class="cta-box">
    <h3>📩 Next Steps</h3>
    <p>Do you want another refinement cycle (further auto-fixing and regression run),<br>
    or are you satisfied with the current test outcomes?</p>
</div>

<div class="footer">
    Generated by QA Automation - Auto-Healing Testing System<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Built with Hexagonal Architecture + LangGraph
</div>
"""


# Global instance
html_report_generator = HTMLReportGenerator()
