# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0

import importlib.metadata
import hashlib
import json
import logging
import os
import re
import warnings
from pathlib import Path
from importlib.resources import files

from rich.console import Console
from rich.markup import escape
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from .exporters import export_csv, export_html, export_sarif

# 可选：使用 MCP Skill 生成 HTML
try:
    from metis.mcp.skills.html_generator import HTMLGeneratorSkill
    MCP_HTML_AVAILABLE = True
except ImportError:
    MCP_HTML_AVAILABLE = False

try:
    METIS_VERSION = importlib.metadata.version("metis")
except importlib.metadata.PackageNotFoundError:
    METIS_VERSION = "unknown"


console = Console()
logger = logging.getLogger("metis")
REPORT_TEMPLATE = (
    files("metis.cli").joinpath("report_template.html").read_text(encoding="utf-8")
)

try:
    from metis.vector_store.pgvector_store import PGVectorStoreImpl

    PG_SUPPORTED = True
except ImportError:
    PG_SUPPORTED = False


def configure_logger(logger, args):
    if logger.hasHandlers():
        logger.handlers.clear()

    default_level = logging.ERROR
    requested_level = getattr(args, "log_level", None)
    if isinstance(requested_level, str):
        level = logging._nameToLevel.get(requested_level.upper(), default_level)
    else:
        level = default_level

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if getattr(args, "log_file", None):
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.setLevel(level)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    logging.captureWarnings(True)
    warnings.resetwarnings()
    if level <= logging.WARNING:
        warnings.filterwarnings("default")
    else:
        warnings.filterwarnings("ignore")

    for name in (
        "httpx",
        "httpcore",
        "openai",
        "openai._base_client",
        "azure",
        "urllib3",
    ):
        noisy = logging.getLogger(name)
        noisy.setLevel(level)
        noisy.propagate = False
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.setLevel(level)
    warnings_logger.propagate = True


def print_console(message, quiet=False, **kwargs):
    if not quiet:
        console.print(message, **kwargs)


def with_spinner(task_description, fn, *args, quiet=False, **kwargs):
    """
    Run a function optionally displaying a spinner.
    When quiet=True (e.g., non-interactive without --verbose), suppress any spinner.
    """
    if quiet:
        return fn(*args, **kwargs)

    with Progress(
        SpinnerColumn(), TextColumn("[bold cyan]{task.description}"), console=console
    ) as progress:
        task = progress.add_task(task_description, total=None)
        result = fn(*args, **kwargs)
        progress.update(task, completed=1)
        progress.stop()
    return result


def with_timer(task_description, fn, *args, quiet=False, **kwargs):
    """
    Run a function while showing an elapsed-time timer.
    Shown only when quiet=False (e.g., verbose mode). In quiet=True, runs silently.
    """
    if quiet:
        return fn(*args, **kwargs)

    with Progress(
        TextColumn("[bold cyan]{task.description}"),
        TextColumn("[bright_black]elapsed"),
        TimeElapsedColumn(),
        transient=True,
        console=console,
        redirect_stdout=True,
        redirect_stderr=True,
    ) as progress:
        task = progress.add_task(task_description, total=1)
        result = fn(*args, **kwargs)
        try:
            progress.update(task, completed=1)
        except Exception:
            pass
    return result


def collect_reviews(engine):
    return {"reviews": [r for r in engine.review_code() if r]}


def iterate_with_progress(total, iterable):
    results = []
    if total <= 0:
        return results
    with Progress(
        SpinnerColumn(style="cyan"),
        BarColumn(bar_width=None, complete_style="green", finished_style="green"),
        TaskProgressColumn(),
        TextColumn("[bright_black]elapsed"),
        TimeElapsedColumn(),
        TextColumn("[bright_black]eta"),
        TimeRemainingColumn(),
        transient=True,
        console=console,
        redirect_stdout=True,
        redirect_stderr=True,
    ) as progress:
        task = progress.add_task("", total=total)
        for item in iterable:
            if item is not None:
                results.append(item)
            progress.advance(task, 1)
        try:
            progress.update(task, completed=progress.tasks[task].total)
        except Exception:
            pass
    return results


def count_index_items(engine):
    """
    Count total items to index (code + docs files).
    Used to size the progress bar for verbose indexing.
    """

    docs_exts = engine.plugin_config.get("docs", {})
    code_count = len(engine.get_code_files())

    doc_count = 0
    base_path = os.path.abspath(engine.codebase_path)
    for _, _, _files in os.walk(base_path):
        for f in _files:
            if os.path.splitext(f)[1].lower() in docs_exts:
                doc_count += 1

    return code_count + doc_count


def save_output(output_files, data, quiet=False):
    if not output_files:
        return

    if isinstance(output_files, (str, Path)):
        files = [output_files]
    else:
        files = list(output_files)
    json_payload = data
    sarif_payload = None

    def _write_payload(path, payload, label):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        print_console(
            f"[blue]{label} saved to {escape(str(path))}[/blue]",
            quiet,
        )

    for file_entry in files:
        output_path = Path(file_entry)
        suffix = output_path.suffix.lower()

        if suffix == ".html":
            try:
                # 优先使用 MCP Skill 生成 HTML（如果可用）
                if MCP_HTML_AVAILABLE:
                    html_skill = HTMLGeneratorSkill()
                    result = html_skill.execute(
                        report_data=data,
                        output_path=str(output_path),
                    )
                    if result.get("success"):
                        html_path = Path(result["html_path"])
                        print_console(
                            f"[blue]HTML report saved to {escape(str(html_path))}[/blue] (via MCP Skill)",
                            quiet,
                        )
                    else:
                        # 回退到传统方法
                        logger.warning(f"MCP Skill failed, falling back to traditional method: {result.get('error')}")
                        html_path = export_html(
                            data, output_path, REPORT_TEMPLATE, METIS_VERSION
                        )
                        print_console(
                            f"[blue]HTML report saved to {escape(str(html_path))}[/blue]",
                            quiet,
                        )
                else:
                    # 使用传统方法
                    html_path = export_html(
                        data, output_path, REPORT_TEMPLATE, METIS_VERSION
                    )
                    print_console(
                        f"[blue]HTML report saved to {escape(str(html_path))}[/blue]",
                        quiet,
                    )
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to generate HTML report: %s", exc)
                print_console("[red]Failed to generate HTML report.[/red]", quiet)
            continue

        if suffix == ".sarif":
            try:
                sarif_path, sarif_payload = export_sarif(
                    data, output_path, sarif_payload
                )
                print_console(
                    f"[blue]SARIF report saved to {escape(str(sarif_path))}[/blue]",
                    quiet,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to generate SARIF report: %s", exc)
                print_console(
                    f"[red]Failed to generate SARIF report at {escape(str(output_path))}[/red]",
                    quiet,
                )
            continue

        if suffix == ".csv":
            try:
                csv_path = export_csv(data, output_path)
                print_console(
                    f"[blue]CSV report saved to {escape(str(csv_path))}[/blue]",
                    quiet,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to generate CSV report: %s", exc)
                print_console(
                    f"[red]Failed to generate CSV report at {escape(str(output_path))}[/red]",
                    quiet,
                )
            continue

        # default to JSON
        _write_payload(output_path, json_payload, "Results")


def check_file_exists(file_path, quiet=False):
    if not Path(file_path).is_file():
        print_console(f"[red]File not found:[/red] {escape(file_path)}", quiet)
        return False
    return True


def sort_and_filter_reviews(
    reviews: list[dict], min_confidence: float = 0.0, severity_filter: list = None
) -> list[dict]:
    """
    Sort reviews by severity and confidence, and filter by minimum confidence and severity.

    Args:
        reviews: List of review dictionaries
        min_confidence: Minimum confidence threshold (0.0-1.0)
        severity_filter: List of severity levels to include (e.g., ["High", "Critical"])

    Returns:
        Sorted and filtered list of reviews
    """
    if not reviews:
        return reviews

    severity_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Unknown": 0}

    def sort_key(review):
        severity = review.get("severity", "Unknown")
        confidence = float(review.get("confidence", 0.0))
        return (
            -severity_order.get(severity, 0),  # 严重程度降序
            -confidence,  # 置信度降序
        )

    # Filter by confidence and severity
    filtered = []
    for r in reviews:
        confidence = float(r.get("confidence", 0.0))
        severity = r.get("severity", "Unknown")

        if confidence < min_confidence:
            continue

        if severity_filter and severity not in severity_filter:
            continue

        filtered.append(r)

    # Sort by severity and confidence
    return sorted(filtered, key=sort_key)


def pretty_print_reviews(
    results, quiet=False, min_confidence=0.0, severity_filter=None
):
    if not results or not results.get("reviews"):
        print_console("[bold green]No security issues found![/bold green]", quiet)
        return

    for file_review in results.get("reviews", []):
        file = file_review.get("file", "UNKNOWN FILE")
        reviews = file_review.get("reviews", [])

        # Sort and filter reviews
        if reviews:
            reviews = sort_and_filter_reviews(reviews, min_confidence, severity_filter)

        if reviews:
            print_console(f"\n[bold blue]File: {escape(file)}[/bold blue]", quiet)
            for idx, r in enumerate(reviews, 1):
                print_console(
                    f" [yellow]Identified issue {idx}:[/yellow] [bold]{escape(r.get('issue','-'))}[/bold]",
                    quiet,
                )
                if r.get("code_snippet"):
                    print_console(
                        f"    [cyan]Snippet:[/cyan] [dim]{r['code_snippet']}",
                        quiet,
                    )
                if r.get("line_number"):
                    print_console(
                        f"    [cyan]Line number:[/cyan] {r['line_number']}",
                        quiet,
                    )
                if r.get("cwe"):
                    cwe_text = str(r["cwe"])
                    match = re.search(r"(\d+)", cwe_text)
                    if match:
                        cwe_url = f"https://cwe.mitre.org/data/definitions/{match.group(1)}.html"
                        print_console(
                            f"    [red]CWE:[/red] [link={cwe_url}]{escape(cwe_text)}[/link]",
                            quiet,
                        )
                    else:
                        print_console(
                            f"    [red]CWE:[/red] {escape(cwe_text)}",
                            quiet,
                        )
                if severity := r.get("severity"):
                    severity_color = {
                        "Low": "green",
                        "Medium": "yellow",
                        "High": "red",
                        "Critical": "magenta",
                    }.get(severity, "bright_black")
                    print_console(
                        f"    [bright_black]Severity:[/bright_black] [bold {severity_color}]{escape(severity)}[/bold {severity_color}]",
                        quiet,
                    )
                if reasoning := r.get("reasoning"):
                    print_console(f"    [white]Why:[/white] {escape(reasoning)}", quiet)
                if r.get("mitigation"):
                    print_console(
                        f"    [green]Mitigation:[/green] {escape(r['mitigation'])}",
                        quiet,
                    )
                if confidence := r.get("confidence"):
                    print_console(
                        f"    [magenta]Confidence:[/magenta] {escape(str(confidence))}",
                        quiet,
                    )
                if any(r.get(field) for field in ("confidence", "severity", "cwe")):
                    print_console("", quiet)
        else:
            print_console(f"[green]No issues in {escape(file)}[/green]", quiet)


def build_flow_graph(results: dict) -> dict:
    if not isinstance(results, dict):
        return {"nodes": [], "edges": [], "attackChains": []}

    severity_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Unknown": 0}
    nodes: dict[str, dict] = {}
    edges: dict[tuple[str, str], dict] = {}
    attack_chains: list[dict] = []

    for file_entry in results.get("reviews", []) or []:
        if not isinstance(file_entry, dict):
            continue
        source_file = file_entry.get("file") or file_entry.get("file_path") or "Unknown"
        if not isinstance(source_file, str) or not source_file.strip():
            source_file = "Unknown"
        source_file = source_file.strip()

        issues = file_entry.get("reviews", []) or []
        issue_count = len(issues) if isinstance(issues, list) else 0
        max_sev = "Unknown"
        if isinstance(issues, list):
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                sev = issue.get("severity") or "Unknown"
                if not isinstance(sev, str):
                    sev = str(sev)
                sev = sev.strip() or "Unknown"
                if severity_rank.get(sev, 0) > severity_rank.get(max_sev, 0):
                    max_sev = sev

        node = nodes.setdefault(
            source_file,
            {
                "id": source_file,
                "label": source_file,
                "issueCount": 0,
                "maxSeverity": "Unknown",
            },
        )
        node["issueCount"] = int(node.get("issueCount", 0)) + issue_count
        if severity_rank.get(max_sev, 0) > severity_rank.get(
            node.get("maxSeverity", "Unknown"), 0
        ):
            node["maxSeverity"] = max_sev

        links = file_entry.get("context_links", []) or []
        if isinstance(links, list):
            for link in links:
                if not isinstance(link, dict):
                    continue
                target = link.get("file")
                if not isinstance(target, str) or not target.strip():
                    continue
                target = target.strip()
                if target == source_file:
                    continue
                kind = link.get("kind") or "unknown"
                key = (source_file, target)
                edge = edges.setdefault(
                    key,
                    {"source": source_file, "target": target, "weight": 0, "kinds": {}},
                )
                edge["weight"] = int(edge.get("weight", 0)) + 1
                kinds = edge.setdefault("kinds", {})
                kinds[kind] = int(kinds.get(kind, 0)) + 1

                nodes.setdefault(
                    target,
                    {
                        "id": target,
                        "label": target,
                        "issueCount": 0,
                        "maxSeverity": "Unknown",
                    },
                )

        if isinstance(issues, list):
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                issue_text = str(issue.get("issue") or "").strip()
                line = issue.get("line_number")
                line_text = str(line).strip() if line not in (None, "") else ""
                severity = issue.get("severity") or "Unknown"
                if not isinstance(severity, str):
                    severity = str(severity)
                severity = severity.strip() or "Unknown"
                snippet = issue.get("code_snippet")
                snippet_text = str(snippet or "").strip()

                chain_key = f"{source_file}:{line_text}:{issue_text}"
                chain_id = hashlib.sha256(chain_key.encode("utf-8")).hexdigest()[:16]

                steps = [
                    {
                        "kind": "vulnerability",
                        "file": source_file,
                        "line": line_text,
                        "issue": issue_text,
                        "snippet": snippet_text,
                    }
                ]
                if isinstance(links, list):
                    for link in links:
                        if not isinstance(link, dict):
                            continue
                        target = link.get("file")
                        if not isinstance(target, str) or not target.strip():
                            continue
                        steps.append(
                            {
                                "kind": "context",
                                "via": str(link.get("kind") or "unknown"),
                                "file": target.strip(),
                                "score": link.get("score"),
                                "excerpt": str(link.get("excerpt") or ""),
                            }
                        )

                attack_chains.append(
                    {
                        "id": chain_id,
                        "file": source_file,
                        "severity": severity,
                        "issue": issue_text,
                        "line": line_text,
                        "steps": steps,
                    }
                )

    return {
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "attackChains": attack_chains,
    }


def attach_flow_graph(results: dict) -> dict:
    if not isinstance(results, dict):
        return results
    results["flow_graph"] = build_flow_graph(results)
    return results


def build_pg_backend(args, runtime, embed_model_code, embed_model_docs, quiet=False):
    if not PG_SUPPORTED:
        print_console(
            "[bold red]Postgres backend requested but not installed. Please install with:[/bold red]",
            quiet,
        )
        print_console("  uv pip install '.[postgres]'", quiet, markup=False)
        exit(1)

    connection_string = (
        f"postgresql://{runtime['pg_username']}:{runtime['pg_password']}"
        f"@{runtime['pg_host']}:{int(runtime['pg_port'])}/{runtime['pg_db_name']}"
    )
    return PGVectorStoreImpl(
        connection_string=connection_string,
        project_schema=args.project_schema,
        embed_model_code=embed_model_code,
        embed_model_docs=embed_model_docs,
        embed_dim=runtime["embed_dim"],
        hnsw_kwargs=runtime.get("hnsw_kwargs", {}),
    )


def build_chroma_backend(args, runtime, embed_model_code, embed_model_docs):
    from metis.vector_store.chroma_store import ChromaStore

    return ChromaStore(
        persist_dir=args.chroma_dir,
        embed_model_code=embed_model_code,
        embed_model_docs=embed_model_docs,
        query_config=runtime.get("query", {}),
    )
