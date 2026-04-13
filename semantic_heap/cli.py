"""Command-line interface for Semantic Heap Memory."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .exceptions import SemanticHeapError
from .memory import SemanticHeapMemory


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(prog="semantic-heap")
    parser.add_argument("--db", default="semantic_heap.db", help="Path to SQLite database")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    save = sub.add_parser("save")
    save.add_argument("--domain", required=True)
    save.add_argument("--idea", required=True)
    save.add_argument("--json", action="store_true")

    retrieve = sub.add_parser("retrieve")
    retrieve.add_argument("--idea", required=True)
    retrieve.add_argument("--time", default="now")
    retrieve.add_argument("--limit", type=int, default=10)
    retrieve.add_argument("--json", action="store_true")

    inspect = sub.add_parser("inspect")
    inspect.add_argument("--id", required=True, type=int)
    inspect.add_argument("--json", action="store_true")

    decay = sub.add_parser("decay")
    decay.add_argument("--json", action="store_true")

    vacuum = sub.add_parser("vacuum")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    memory = SemanticHeapMemory(args.db)
    try:
        if args.command == "init":
            print(f"Initialized semantic heap database: {args.db}")
            return 0
        if args.command == "save":
            result = memory.save(args.domain, args.idea)
            if args.json:
                print(json.dumps(asdict(result), indent=2))
            else:
                print(f"Saved idea #{result.idea_id}: {result.normalized_idea}")
            return 0
        if args.command == "retrieve":
            result = memory.retrieve(args.idea, temporal_relevance=args.time, limit=args.limit)
            if args.json:
                print(json.dumps(asdict(result), indent=2))
            else:
                for match in result.matches:
                    print(f"[{match.match_score:.3f}] #{match.idea_id} {match.idea} :: {', '.join(match.semantic_paths)}")
            return 0
        if args.command == "inspect":
            info = memory.inspect_idea(args.id)
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print(info)
            return 0
        if args.command == "decay":
            changed = memory.decay()
            if args.json:
                print(json.dumps({"updated": changed}))
            else:
                print(f"Updated ideas: {changed}")
            return 0
        if args.command == "vacuum":
            memory.vacuum()
            print("Vacuum complete")
            return 0
    except SemanticHeapError as exc:
        print(f"error: {exc}")
        return 2
    finally:
        memory.close()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
