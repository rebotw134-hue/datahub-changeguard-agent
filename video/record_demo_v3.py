from __future__ import annotations

import json
import subprocess
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from changeguard.cli import DEMO_URN
from changeguard.datahub_gateway import DataHubGateway

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "output" / "submission" / "v3-build"
SLIDES = BUILD / "slides"
LIVE_OUTPUT = ROOT / "output" / "v3-live-recording"
VIEWPORT = {"width": 1280, "height": 720}


def append_line(page: Page, text: str, css_class: str = "") -> None:
    page.locator("#output").evaluate(
        "(node, item) => {"
        "const line = document.createElement('div');"
        "line.className = item.cssClass;"
        "line.textContent = item.text;"
        "node.appendChild(line);"
        "node.scrollTop = node.scrollHeight;"
        "}",
        {"text": text, "cssClass": css_class},
    )


def render_slides(browser) -> None:
    SLIDES.mkdir(parents=True, exist_ok=True)
    page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)
    storyboard = (ROOT / "video" / "storyboard.html").as_uri()
    for index in range(1, 8):
        page.goto(f"{storyboard}?slide={index}", wait_until="load")
        page.screenshot(path=str(SLIDES / f"{index:02d}.png"))
    page.close()


def record_live_run(browser) -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    context = browser.new_context(
        viewport=VIEWPORT,
        record_video_dir=str(BUILD),
        record_video_size=VIEWPORT,
    )
    page = context.new_page()
    video = page.video
    page.set_content(
        """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <style>
            * { box-sizing: border-box; }
            html, body { width: 1280px; height: 720px; margin: 0; overflow: hidden; }
            body {
              background: #0b1118; color: #dce6ef;
              font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
              letter-spacing: 0;
            }
            header {
              height: 74px; display: flex; align-items: center;
              justify-content: space-between; padding: 0 34px;
              border-bottom: 1px solid #34404c; background: #111a24;
            }
            header strong { color: #8cbcff; font: 700 20px/1 system-ui, sans-serif; }
            header span {
              color: #8da0b2; font: 700 14px/1 system-ui, sans-serif;
              text-transform: uppercase;
            }
            main { padding: 28px 36px; }
            .label {
              margin-bottom: 14px; color: #8da0b2;
              font: 700 14px/1 system-ui, sans-serif; text-transform: uppercase;
            }
            #output {
              height: 548px; padding: 24px 26px; overflow: hidden;
              border: 1px solid #34404c; border-top: 6px solid #175cd3;
              background: #070b10; font-size: 18px; line-height: 1.52;
            }
            #output div { min-height: 28px; white-space: pre-wrap; }
            .command { color: #ffffff; }
            .context { color: #8cbcff; }
            .success { color: #78dba9; }
            .block { margin-top: 8px; color: #ff8f85; font-weight: 800; }
            .muted { color: #8da0b2; }
          </style>
        </head>
        <body>
          <header>
            <strong>DataHub ChangeGuard</strong><span>Live end-to-end execution</span>
          </header>
          <main>
            <div class="label">Verified local DataHub Core 1.6</div>
            <div id="output"></div>
          </main>
        </body>
        </html>
        """
    )

    append_line(page, "$ changeguard run \\", "command")
    page.wait_for_timeout(550)
    append_line(page, "    --proposed examples/proposed_schema.json \\", "command")
    page.wait_for_timeout(450)
    append_line(page, "    --rename-hints examples/rename_hints.json \\", "command")
    page.wait_for_timeout(450)
    append_line(page, "    --source-relation commerce.orders_v2", "command")
    page.wait_for_timeout(900)
    append_line(page, "Connecting to http://127.0.0.1:8080 ...", "muted")

    command = [
        str(ROOT / ".venv" / "bin" / "changeguard"),
        "run",
        "--proposed",
        "examples/proposed_schema.json",
        "--rename-hints",
        "examples/rename_hints.json",
        "--source-relation",
        "commerce.orders_v2",
        "--output-dir",
        str(LIVE_OUTPUT),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    payload = json.loads(completed.stdout)
    live_schema, _ = DataHubGateway("http://127.0.0.1:8080").inspect_dataset(DEMO_URN)
    result = payload["result"]
    fields = json.loads((LIVE_OUTPUT / "audit.json").read_text())["findings"]

    page.wait_for_timeout(700)
    append_line(page, f"[ACK] {result['evidence_source']}", "context")
    page.wait_for_timeout(800)
    append_line(page, f"[ACK] schema fields read: {len(live_schema.columns)}", "context")
    page.wait_for_timeout(800)
    append_line(
        page,
        f"[ACK] downstream datasets: {result['downstream_count']} (field lineage)",
        "context",
    )
    page.wait_for_timeout(800)
    append_line(page, f"[ANALYZER] findings: {len(fields)}", "success")
    page.wait_for_timeout(650)
    append_line(page, "[ARTIFACTS] audit.json, report.html, SQL, dbt contract", "success")
    page.wait_for_timeout(800)
    append_line(page, f"DECISION: {result['decision']}   RISK: {result['risk_score']}/100", "block")
    page.wait_for_timeout(2200)

    context.close()
    if video is None:
        raise RuntimeError("Playwright did not create a video artifact")
    generated = Path(video.path())
    target = BUILD / "live-run.webm"
    generated.replace(target)
    return target


def record_report(browser) -> Path:
    context = browser.new_context(
        viewport=VIEWPORT,
        record_video_dir=str(BUILD),
        record_video_size=VIEWPORT,
    )
    page = context.new_page()
    video = page.video
    page.goto((LIVE_OUTPUT / "report.html").as_uri(), wait_until="load")
    page.wait_for_timeout(900)
    for position in (260, 640, 980, 1280):
        page.evaluate("value => window.scrollTo({top: value, behavior: 'smooth'})", position)
        page.wait_for_timeout(1050)
    context.close()
    if video is None:
        raise RuntimeError("Playwright did not create a report video artifact")
    generated = Path(video.path())
    target = BUILD / "report-walkthrough.webm"
    generated.replace(target)
    return target


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        render_slides(browser)
        live_run = record_live_run(browser)
        report = record_report(browser)
        browser.close()
    print(f"Rendered slides: {SLIDES}")
    print(f"Recorded live run: {live_run}")
    print(f"Recorded report: {report}")


if __name__ == "__main__":
    main()
