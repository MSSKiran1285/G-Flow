"""Renders an EvidenceReport (smt.engine.evidence) into a PDF, in G-Flow's own visual
identity — structurally similar to G-Stride's evidence PDFs (cover metadata, per-scenario
step tables with screenshots, an input/output traceability matrix, a raw verbatim log
appendix), but using only fields G-Flow can back with real data; nothing here is a
placeholder for a check that was never actually performed.

Rendering path: build a plain HTML string, print it to PDF via a headless Chromium-family
browser (Edge on Windows) — the same mechanism already used elsewhere in this project to
preview generated SVG/HTML, since native PDF libraries (cairosvg, weasyprint) don't have a
working system dependency on this machine.
"""

from __future__ import annotations

import base64
import html
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from smt.engine.evidence import EvidenceReport, EvidenceScenario, EvidenceStep

_BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def _find_browser() -> str:
    for candidate in _BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    found = shutil.which("msedge") or shutil.which("chrome") or shutil.which("chromium")
    if found:
        return found
    raise RuntimeError(
        "No Chromium-family browser found for PDF rendering (checked Edge/Chrome in their "
        "usual install locations, and msedge/chrome/chromium on PATH)."
    )


def _esc(value: object) -> str:
    return html.escape(str(value))


def _fmt_duration(ms: float) -> str:
    seconds = ms / 1000
    return f"{seconds:.1f} s"


def _fmt_dt(dt) -> str:
    return dt.strftime("%b %d, %Y, %I:%M:%S %p %Z").strip()


def _step_row(index: str, step: EvidenceStep) -> str:
    result_class = "pass" if step.success else "fail"
    result_text = "Passed" if step.success else "Failed"
    warn = ' <span class="warn">&#9650; &gt;30s</span>' if step.duration_ms > 30_000 else ""
    description = _esc(step.description)
    if step.captured:
        description += f"<br><span class='muted'>captured {_esc(step.captured)}</span>"
    value = _esc(step.value_entered) if step.value_entered else "&mdash;"
    return f"""
      <tr>
        <td>{_esc(index)}</td>
        <td>{description}</td>
        <td><code>{value}</code></td>
        <td class="{result_class}">{result_text}{f'<br><span class="muted">{_esc(step.error)}</span>' if step.error else ''}</td>
        <td>{_esc(_fmt_duration(step.duration_ms))}{warn}</td>
      </tr>"""


def _screenshot_figs(chapter_no: int, steps: list[EvidenceStep]) -> str:
    figs = []
    fig_no = 1
    for step in steps:
        if not step.screenshot_png:
            continue
        b64 = base64.b64encode(step.screenshot_png).decode("ascii")
        caption = step.captured or step.description
        figs.append(f"""
      <div class="fig">
        <div class="fig-caption"><strong>Fig {chapter_no}.{fig_no}</strong> &mdash; {_esc(caption)}. Captured automatically during Scenario {chapter_no}.</div>
        <img src="data:image/png;base64,{b64}" />
      </div>""")
        fig_no += 1
    if not figs:
        return ""
    return f"""
    <h3>Screenshot Evidence</h3>
    {''.join(figs)}"""


def _scenario_chapter(chapter_no: int, scenario: EvidenceScenario) -> str:
    rows = "".join(_step_row(f"{chapter_no}.{i + 1}", step) for i, step in enumerate(scenario.steps))
    banner = (
        '<div class="banner pass">&check; Scenario completed successfully</div>'
        if scenario.success
        else '<div class="banner fail">&#10007; Scenario failed</div>'
    )
    return f"""
  <section class="chapter">
    <h2>Chapter {chapter_no} &mdash; {_esc(scenario.test_case_name)}</h2>
    {f'<p class="objective">{_esc(scenario.description)}</p>' if scenario.description else ''}
    <table class="step-table">
      <thead><tr><th>#</th><th>Business Action</th><th>Value Entered</th><th>Result</th><th>Duration</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {banner}
    {_screenshot_figs(chapter_no, scenario.steps)}
  </section>"""


def _traceability_matrix(report: EvidenceReport) -> str:
    rows = []
    for key, value in report.row.items():
        rows.append(f"<tr><td>{_esc(key)}</td><td>Input</td><td><code>{_esc(value)}</code></td><td>Execution input</td></tr>")
    for key, value in report.final_buffer.items():
        rows.append(f"<tr><td>{_esc(key)}</td><td>Output</td><td><code>{_esc(value)}</code></td><td>Captured during execution</td></tr>")
    if not rows:
        return ""
    return f"""
  <section>
    <h2>Traceability &amp; Results Matrix</h2>
    <table class="step-table">
      <thead><tr><th>Field</th><th>Type</th><th>Value</th><th>Produced / Consumed In</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </section>"""


def _raw_log_appendix(report: EvidenceReport) -> str:
    sections = []
    for scenario in report.scenarios:
        rows = "".join(
            f"""<tr>
              <td>{_esc(step.description)} <span class="muted">[{_esc(step.action_mode)} {_esc(step.component_id)}]</span></td>
              <td class="{'pass' if step.success else 'fail'}">{'PASSED' if step.success else 'FAILED'}</td>
              <td>{step.duration_ms:.0f} ms</td>
              <td>{_esc(step.error)}</td>
            </tr>"""
            for step in scenario.steps
        )
        status = "PASSED" if scenario.success else "FAILED"
        sections.append(f"""
    <h3>{_esc(scenario.test_case_name)} &mdash; {status}</h3>
    <table class="step-table">
      <thead><tr><th>Action</th><th>Status</th><th>Duration</th><th>Error</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>""")
    return f"""
  <section>
    <h2>Appendix &mdash; Audit Detail (Raw Step Log, Verbatim)</h2>
    {''.join(sections)}
  </section>"""


_CSS = """
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", Arial, sans-serif; color: #1c2430; margin: 0; }
  .page { padding: 32px 40px; }
  .eyebrow { text-transform: uppercase; letter-spacing: 0.08em; font-size: 11px; color: #616e80; text-align: center; }
  h1 { font-size: 26px; text-align: center; margin: 8px 0 4px; }
  .subtitle { text-align: center; color: #334b66; margin-bottom: 20px; }
  .result-badge { display: block; width: fit-content; margin: 0 auto 24px; padding: 8px 20px; border-radius: 999px; font-weight: 700; color: #fff; }
  .result-badge.pass { background: #1f7a4d; }
  .result-badge.fail { background: #c0392b; }
  table.meta { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
  table.meta td { border: 1px solid #e2e6ec; padding: 8px 12px; font-size: 12.5px; vertical-align: top; }
  table.meta td:first-child { width: 220px; font-weight: 600; background: #f7f8fa; }
  table.meta code, .step-table code { font-family: "Consolas", monospace; font-size: 11.5px; background: #f1f2f5; padding: 1px 4px; border-radius: 3px; }
  h2 { font-size: 18px; border-bottom: 2px solid #3a4a63; padding-bottom: 6px; margin-top: 32px; }
  h3 { font-size: 14px; margin-top: 20px; }
  .objective { color: #334b66; font-style: italic; }
  table.step-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 12px; }
  table.step-table th { background: #f1f2f5; text-transform: uppercase; letter-spacing: 0.03em; font-size: 10.5px; color: #616e80; text-align: left; padding: 6px 10px; border-bottom: 1px solid #cbd5e1; }
  table.step-table td { padding: 6px 10px; border-bottom: 1px solid #e2e6ec; vertical-align: top; }
  td.pass { color: #1f7a4d; font-weight: 600; }
  td.fail { color: #c0392b; font-weight: 600; }
  .muted { color: #8a96a6; font-size: 11px; }
  .warn { color: #955400; font-weight: 700; }
  .banner { padding: 8px 14px; border-radius: 6px; font-weight: 600; margin: 8px 0 20px; }
  .banner.pass { background: #e3f3ea; color: #1f7a4d; }
  .banner.fail { background: #fbe7e4; color: #c0392b; }
  .fig { margin: 12px 0 20px; page-break-inside: avoid; }
  .fig-caption { font-size: 12px; margin-bottom: 6px; }
  .fig img { max-width: 100%; border: 1px solid #cbd5e1; border-radius: 4px; }
  .footer-brand { text-align: center; color: #8a96a6; font-size: 11px; margin-top: 16px; }
"""


def render_evidence_html(report: EvidenceReport) -> str:
    title = " &rarr; ".join(_esc(s.test_case_name) for s in report.scenarios)
    overall = report.success
    meta_rows = [
        ("Run ID", report.run_id),
        ("Execution ID", report.execution_id),
        ("Plan Hash", report.plan_hash),
        ("Data Hash", report.data_hash),
        ("Execution Mode", report.execution_mode),
        ("Started", _fmt_dt(report.started_at)),
        ("Finished", _fmt_dt(report.finished_at)),
        ("Total Duration", f"{(report.finished_at - report.started_at).total_seconds():.1f} s"),
        ("Executed By", report.executed_by),
        ("Environment", report.environment),
    ]
    meta_html = "".join(f"<tr><td>{_esc(k)}</td><td><code>{_esc(v)}</code></td></tr>" for k, v in meta_rows)

    chapters = "".join(_scenario_chapter(i + 1, s) for i, s in enumerate(report.scenarios))

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{_CSS}</style></head>
<body>
<div class="page">
  <div class="eyebrow">G-FLOW &middot; TEST AUTOMATION EVIDENCE</div>
  <h1>Business Process Automation &mdash; Test Evidence</h1>
  <div class="subtitle">{title}</div>
  <div class="result-badge {'pass' if overall else 'fail'}">{'&check; OVERALL RESULT: PASSED' if overall else '&#10007; OVERALL RESULT: FAILED'}</div>

  <table class="meta">{meta_html}</table>

  {chapters}

  {_traceability_matrix(report)}

  {_raw_log_appendix(report)}

  <div class="footer-brand">G-Flow</div>
</div>
</body></html>"""


def render_evidence_pdf(report: EvidenceReport, timeout_s: float = 30.0) -> bytes:
    html_content = render_evidence_html(report)
    tmp = tempfile.mkdtemp()
    try:
        html_path = Path(tmp) / "evidence.html"
        pdf_path = Path(tmp) / "evidence.pdf"
        html_path.write_text(html_content, encoding="utf-8")

        browser = _find_browser()
        profile_dir = Path(tmp) / "profile"
        # --user-data-dir forces a genuinely separate browser process even when the
        # user already has a normal (non-headless) Edge/Chrome window open — without
        # it, the headless invocation can silently hand off to that existing instance
        # instead of actually rendering.
        args = [
            browser, "--headless=new", "--disable-gpu", f"--user-data-dir={profile_dir}",
            "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri(),
        ]
        # The launcher process can return well before rendering actually finishes (it
        # forks a detached child that does the real work) — poll for the output file
        # rather than trusting subprocess.run's own completion as the signal.
        subprocess.run(args, capture_output=True, timeout=timeout_s)
        deadline = time.monotonic() + timeout_s
        while not pdf_path.exists() and time.monotonic() < deadline:
            time.sleep(0.5)
        if not pdf_path.exists():
            raise RuntimeError(f"PDF rendering timed out after {timeout_s}s waiting for {pdf_path}")
        # The file can exist (created) slightly before the writer process releases its
        # exclusive handle on Windows — a bare read right after `.exists()` becomes true
        # can still hit a PermissionError. Retry the read itself, not just existence.
        last_error: Exception | None = None
        for _ in range(10):
            try:
                return pdf_path.read_bytes()
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.3)
        raise RuntimeError(f"PDF was written but never became readable: {last_error}")
    finally:
        # The rendering process can still be releasing its profile lock for a moment
        # after the PDF itself is already fully written and readable — never let a
        # slow-to-die browser process turn a successful render into an error.
        shutil.rmtree(tmp, ignore_errors=True)
