"""Build an inventory across a corpus of bots (read-only)."""

from __future__ import annotations

from collections import Counter

from . import complexity, crawl, extract, model


def inventory(root: str) -> dict:
    """Per-bot summaries plus an aggregate view for a folder (or single file)."""
    files = crawl.find_bot_files(root)
    bots = []
    errors = []
    pkg_counter: Counter = Counter()
    cmd_counter: Counter = Counter()

    for f in files:
        try:
            data = model.load_bot(f["path"])
        except model.BotLoadError as exc:
            errors.append({"path": f["path"], "error": str(exc)})
            continue

        pkgs = extract.extract_packages(data)
        usage = extract.action_usage(data)
        variables = extract.extract_variables(data)
        metrics = complexity.metrics(data)

        for p in pkgs:
            pkg_counter[p["name"]] += 1
        for u in usage:
            cmd_counter[(u["package"], u["command"])] += u["count"]

        bots.append({
            "path": f["path"],
            "relpath": f["relpath"],
            "size": f["size"],
            "package_count": len(pkgs),
            "action_count": metrics["action_count"],
            "variable_count": metrics["variable_count"],
            "loops": metrics["loops"],
            "complexity_score": metrics["complexity_score"],
            "packages": [p["name"] for p in pkgs],
        })

    aggregate = {
        "bot_count": len(bots),
        "error_count": len(errors),
        "packages_by_frequency": [
            {"name": n, "bots_using": c}
            for n, c in sorted(pkg_counter.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "top_actions": [
            {"package": p, "command": c, "total_uses": n}
            for (p, c), n in sorted(cmd_counter.items(), key=lambda kv: (-kv[1], kv[0]))[:25]
        ],
    }

    return {
        "root": root,
        "aggregate": aggregate,
        "bots": sorted(bots, key=lambda b: b["path"]),
        "errors": errors,
    }
