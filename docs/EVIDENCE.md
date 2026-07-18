# Evidence

Observed on 2026-07-14 against this checkout. No token values are recorded here.

## External submission state

Observed on 2026-07-18:

- Public GitHub repository created at `https://github.com/rebotw134-hue/datahub-changeguard-agent`; initial code push was still pending when this note was written.
- Devpost account created and non-legal registration fields completed for the DataHub hackathon. Entrant eligibility and official-rule acceptance remain intentionally unconfirmed.
- The original 1:44 fallback demo is unlisted at `https://youtu.be/k6SB7u50caY`.
- The 1:47 V2 demo was uploaded, passed YouTube's copyright check, and was saved as unlisted at `https://youtu.be/deXV5ECYfCE`.
- The 1:51 V3 demo was built and verified locally but was not uploaded or made public when this note was written.

## Automated checks

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
```

- Pytest: `15 passed in 0.03s`.
- Ruff: `All checks passed!`.

## Offline generation

```bash
.venv/bin/changeguard analyze \
  --current examples/current_schema.json \
  --proposed examples/proposed_schema.json \
  --context examples/context.json \
  --rename-hints examples/rename_hints.json \
  --source-relation commerce.orders_v2 \
  --output-dir output/example
```

Observed decision: `BLOCK`, risk `100/100`, with three findings: `COLUMN_RENAME`, `TYPE_CHANGED`, and `NULLABILITY_RELAXED`.

## Live DataHub verification

The existing local DataHub Core 1.6 Quickstart was started within its configured 7.75 GiB Docker allocation. GMS health and frontend checks both returned HTTP `200`. The unrelated `astra_system-postgres-1` container remained healthy.

```bash
.venv/bin/changeguard seed-demo
.venv/bin/changeguard run \
  --proposed examples/proposed_schema.json \
  --rename-hints examples/rename_hints.json \
  --source-relation commerce.orders_v2 \
  --output-dir output/live
.venv/bin/changeguard verify-writeback
```

Observed live evidence:

- Source: `urn:li:dataset:(urn:li:dataPlatform:postgres,commerce.orders,PROD)`.
- Downstream `finance.daily_revenue`: field impacts `order_id`, `order_total`.
- Downstream `growth.customer_ltv`: field impacts `created_at`, `customer_id`, `order_total`.
- Decision: `BLOCK`, risk `100/100`, downstream count `2`.
- Review tag read back: `urn:li:tag:changeguard-review-required`.
- Active incident read back: `urn:li:incident:1c19cf78-e981-416f-a02a-be30555be88b`.
- Audit fingerprint: `0fd27255e1ca`.
- The first confirmed writeback created the incident; a repeated identical audit returned `created_incident: false` and reused the same incident URN.

Direct checks against this local GMS image returned HTTP `404` for `GET /mcp` and `POST /mcp`.

### Agent Context Kit live read

Observed on 2026-07-18 with the existing DataHub Core 1.6 containers and bounded two-hop
lineage reads:

```bash
.venv/bin/changeguard run \
  --proposed examples/proposed_schema.json \
  --rename-hints examples/rename_hints.json \
  --source-relation commerce.orders_v2 \
  --output-dir output/agent-context-example
```

- Official package: `datahub-agent-context==1.6.0.14`.
- Tool functions used by the live runtime: `get_entities`, `list_schema_fields`, and `get_lineage`.
- Evidence source: `datahub-agent-context:1.6.0.14:http://127.0.0.1:8080`.
- Result: `BLOCK`, risk `100/100`, two downstream assets, and the same field-level impacts as the prior SDK verification.
- The standalone HTTP `/mcp` endpoint is not required for this path; Agent Context Kit tools execute directly against the authenticated `DataHubClient`.

## Browser checks

The generated live report was loaded in Chromium with Playwright at `1440x1000` and `390x844` viewports. Both full-page screenshots were inspected. Findings use a table on desktop and stacked evidence rows on mobile; no overlap, truncation, blank render, console error, or console warning was observed.

- `output/playwright/report-desktop.png`
- `output/playwright/report-mobile.png`
- `output/playwright/datahub-dataset.png`
- `output/playwright/datahub-incident.png`

## Demo video checks

`output/submission/datahub-changeguard-demo.mp4` was built from seven inspected 1280x720 scenes with local English narration.

Observed media properties and checks:

- Duration: `00:01:43.39`.
- Size: `2,037,502` bytes.
- Video: H.264 High, 1280x720, approximately 24 fps.
- Audio: AAC-LC, 22050 Hz, mono.
- Full decode completed with zero FFmpeg errors.
- Black-frame detection at `pic_th=0.98`, `pix_th=0.02`, and `d=0.25` reported no events.
- Silence detection at `-45 dB` for `2` seconds reported no events.
- Audio volume: mean `-15.7 dB`, maximum `-1.4 dB`.
- Frames sampled at 5, 18, 34, 49, 65, 79, and 94 seconds showed all seven intended scenes.

### V2 background build

Observed on 2026-07-18 after running `bash video/build_demo_v2.sh` without opening a desktop
video editor:

- Artifact: `output/submission/datahub-changeguard-demo-v2.mp4`.
- Duration: `00:01:46.73`; size: `5,841,132` bytes.
- Video: H.264 High, 1920x1080, 30 fps.
- Audio: AAC-LC, 48000 Hz, mono; mean `-15.7 dB`, maximum `-1.5 dB`.
- Full decode completed with zero FFmpeg errors.
- Black-frame detection at `pic_th=0.98`, `pix_th=0.02`, and `d=0.25` reported no events.
- Silence detection at `-45 dB` for `2` seconds reported no events.
- The inspected eight-frame contact sheet showed all seven scenes, readable single-line
  bilingual captions, and no blank render.
- Frames from the same scene at 1 and 5 seconds produced SSIM `0.872532`, confirming that the
  background motion pass changed the rendered frames instead of repeating a static frame.

### V3 live-run build

Observed on 2026-07-18 after running `bash video/build_demo_v3.sh` with DataHub Core 1.6
healthy in the background:

- Artifact: `output/submission/datahub-changeguard-demo-v3.mp4`.
- Duration: `00:01:51.23`; size: `7,107,248` bytes.
- Video: H.264 High, 1920x1080, 30 fps.
- Audio: AAC-LC, 48000 Hz, mono; mean `-15.8 dB`, maximum `-1.5 dB`.
- Full decode completed with zero FFmpeg errors, and black-frame detection reported no events.
- Scene four records an actual `changeguard run` against local DataHub and displays the
  observed Agent Context Kit source, five schema fields, two field-lineage downstreams,
  three findings, generated artifacts, and `BLOCK 100/100`.
- The following dynamic segment scrolls through the report generated by that same run.
- The inspected contact sheet and sampled frames at 48, 58, and 106 seconds showed readable
  terminal output, report evidence, architecture, and bilingual captions with no overlap.
- The 1280x720 V3 title frame was exported as the publishing thumbnail.

## SHA-256

```text
778568a8381d23128490e1b5c7d440ed9a84a9b71cf69e2f7ca9c17a4dde348c  output/example/audit.json
4d2f62eb5889a01c40680bca89004a5d683cab7148935fd892615a235cfe709d  output/example/report.html
32a68047317e3cd3209388e07627877b872805267e2587922930ea1342d67af5  output/live/audit.json
856bfa6def22f95e98d09bc349ae224218df8b12562a493e84bcd2611ababb96  output/live/report.html
d5649725fc2135eccd9b1015f834b4e89d7f9b372bb1d72c90e72b778abd7810  output/live/writeback.json
6db099b56f8a6b881c36e811489a6039e3eb7c990f47a495729e1c0a148dccc0  output/playwright/report-desktop.png
910e4ed2612d2a7447ca28e6967241416108ca5fa5df452675896d0968135629  output/playwright/report-mobile.png
b180adeb2c64a22acc2e874d6643d3e41dc589417ae7ab14a252570665314e04  output/playwright/datahub-dataset.png
fb9cf74e7cd6ed916af5fd890d7be13aadd827286c843ee7d0a45bf7cf027d7e  output/playwright/datahub-incident.png
ec0fc3ef98461dc7c07ce0370f91a131fad6bdd7e895366584e47a594e4f4300  output/submission/datahub-changeguard-demo.mp4
340153f572026bdca8c7631c11fe51e8e079cfba916fed355bab9ef374277de0  output/submission/storyboard-contact-sheet.png
e9eb404655c8c8d423edc9e19bf23d6e5c92d18d295e1467606db6b0595d517b  output/submission/datahub-changeguard-demo-v2.mp4
5d0dee866f02f24d64bc145ea401a7f03f9268ab8006c4daf0a94f980425a22d  output/submission/datahub-changeguard-demo-v2-contact-sheet.png
1a36332e44ea047926be78bf14ad66329f2d7e4c9d5b6dbd8851daecc8b6d0b1  output/agent-context-example/audit.json
8b2efdcf03c8226b08ba2686b40fe2a3225992bbdbc219da462e823d1d2b7bf4  output/agent-context-example/compatibility_view.sql
2c9572676471de9c311253d4a837fe72f0e0b7b9cbf3680ea9e20075662ab1ce  output/agent-context-example/datahub_context.json
86ca3f1bb6beffe4b26e72403a1ae3d829c23f2de969baf1b5d61929e01ebb36  output/agent-context-example/dbt_schema.yml
856bfa6def22f95e98d09bc349ae224218df8b12562a493e84bcd2611ababb96  output/agent-context-example/report.html
f042b9e937a9abaeaba489890f8942fc4f652df88afc65d8e36760d5224b25b7  output/agent-context-example/report.md
dee159fb395bfdd28440d5e02081815dac0c609602c1c2ef8b59452eb548a730  output/submission/datahub-changeguard-demo-v3.mp4
dd7bdbc74582804b26b17d1f678fe93a954ad89bd190c8d7b589e092e5ac7d98  output/submission/datahub-changeguard-demo-v3-contact-sheet.png
0444aa11bc4731b8145be8398b3d6919e4bfbc10b9c5237bfd03168dd9c1195d  output/submission/datahub-changeguard-demo-v3-thumbnail.png
```
