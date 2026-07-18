from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from changeguard.analyzer import analyze_change
from changeguard.datahub_gateway import DataHubGateway
from changeguard.files import read_json, write_json
from changeguard.generators import write_artifacts
from changeguard.models import DatasetContext, DatasetSchema

DEMO_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,commerce.orders,PROD)"


def _rename_hints(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    value = read_json(path)
    raw = value.get("renames", value)
    if not isinstance(raw, dict):
        raise ValueError("Rename hints must be a JSON object or contain a 'renames' object")
    return {str(old): str(new) for old, new in raw.items()}


def _gateway(args: argparse.Namespace) -> DataHubGateway:
    return DataHubGateway(server=args.datahub_url, token=args.token)


def _run_offline(args: argparse.Namespace) -> int:
    current = DatasetSchema.from_dict(read_json(args.current))
    proposed = DatasetSchema.from_dict(read_json(args.proposed))
    context = DatasetContext.from_dict(read_json(args.context))
    result = analyze_change(current, proposed, context, _rename_hints(args.rename_hints))
    paths = write_artifacts(
        args.output_dir,
        current,
        proposed,
        context,
        result,
        args.source_relation,
    )
    print(
        json.dumps(
            {"result": result.to_dict(), "artifacts": {k: str(v) for k, v in paths.items()}},
            indent=2,
        )
    )
    return 0


def _seed(args: argparse.Namespace) -> int:
    seeded = _gateway(args).seed_demo()
    print(json.dumps(seeded, indent=2, sort_keys=True))
    return 0


def _run_live(args: argparse.Namespace) -> int:
    gateway = _gateway(args)
    current, context = gateway.inspect_dataset(args.dataset_urn, max_hops=args.max_hops)
    proposed = DatasetSchema.from_dict(read_json(args.proposed))
    result = analyze_change(current, proposed, context, _rename_hints(args.rename_hints))
    paths = write_artifacts(
        args.output_dir,
        current,
        proposed,
        context,
        result,
        args.source_relation,
    )
    payload: dict[str, object] = {
        "result": result.to_dict(),
        "artifacts": {key: str(path) for key, path in paths.items()},
    }
    if args.writeback:
        if not args.confirm_writeback:
            raise PermissionError("Pass --confirm-writeback together with --writeback")
        writeback = gateway.writeback(result, confirm=True)
        payload["writeback"] = writeback.to_dict()
        write_json(Path(args.output_dir) / "writeback.json", payload["writeback"])
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _verify(args: argparse.Namespace) -> int:
    result = _gateway(args).verify_writeback(args.dataset_urn)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["review_tag_present"] and result["active_changeguard_incidents"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="changeguard",
        description="Review proposed schema changes using DataHub context.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    offline = subparsers.add_parser("analyze", help="Run a deterministic fixture-based review")
    offline.add_argument("--current", required=True)
    offline.add_argument("--proposed", required=True)
    offline.add_argument("--context", required=True)
    offline.add_argument("--rename-hints")
    offline.add_argument("--source-relation", required=True)
    offline.add_argument("--output-dir", default="output/example")
    offline.set_defaults(handler=_run_offline)

    def add_datahub_options(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--datahub-url",
            default=os.getenv("DATAHUB_GMS_URL", "http://127.0.0.1:8080"),
        )
        command.add_argument("--token", default=os.getenv("DATAHUB_TOKEN"))

    seed = subparsers.add_parser("seed-demo", help="Upsert an isolated demo lineage graph")
    add_datahub_options(seed)
    seed.set_defaults(handler=_seed)

    live = subparsers.add_parser("run", help="Read context from DataHub and review a proposal")
    add_datahub_options(live)
    live.add_argument("--dataset-urn", default=DEMO_URN)
    live.add_argument("--proposed", required=True)
    live.add_argument("--rename-hints")
    live.add_argument("--source-relation", required=True)
    live.add_argument("--output-dir", default="output/live")
    live.add_argument("--max-hops", type=int, choices=(1, 2), default=2)
    live.add_argument("--writeback", action="store_true")
    live.add_argument("--confirm-writeback", action="store_true")
    live.set_defaults(handler=_run_live)

    verify = subparsers.add_parser("verify-writeback", help="Read tag and incident evidence back")
    add_datahub_options(verify)
    verify.add_argument("--dataset-urn", default=DEMO_URN)
    verify.set_defaults(handler=_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (ValueError, PermissionError, RuntimeError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
