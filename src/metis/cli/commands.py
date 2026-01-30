# SPDX-FileCopyrightText: Copyright 2025 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: Apache-2.0


import importlib
from rich.console import Console
from rich.markup import escape

from metis.utils import read_file_content, safe_decode_unicode
from .utils import (
    check_file_exists,
    with_spinner,
    with_timer,
    collect_reviews,
    iterate_with_progress,
    count_index_items,
    pretty_print_reviews,
    save_output,
    print_console,
    sort_and_filter_reviews,
    attach_flow_graph,
)

console = Console()


def show_help():
    from metis.i18n import t
    console.print(
        f"""
[bold blue]Metis CLI[/bold blue]

{t('help_commands')}:

- [cyan]index[/cyan]
- [cyan]review_patch mypatch.diff[/cyan]
- [cyan]review_file path_to_file/myfile.c[/cyan]
- [cyan]review_code[/cyan]
- [cyan]update patch.diff[/cyan]
- [cyan]ask "{t('ask_example')}"[/cyan]
- [cyan]report[/cyan]              ({t('help_report')})
- [magenta]exit[/magenta]   ({t('help_exit')})
- [magenta]help[/magenta]   ({t('help_show')})

{t('help_options')}:
    --backend chroma|postgres  {t('help_backend')}
    --output-file PATH         {t('help_output_file')}
    --custom-prompt PATH       {t('help_custom_prompt')}
    --project-schema SCHEMA    {t('help_project_schema')}
    --chroma-dir DIR           {t('help_chroma_dir')}
    --verbose                  {t('help_verbose')}
    --version                  {t('help_version')}
"""
    )


def show_version():
    version = importlib.metadata.version("metis")
    console.print("Metis [green]" + version + "[/green]")


def run_review(engine, patch_file, args):
    from metis.i18n import t
    if not check_file_exists(patch_file):
        return
    results = with_spinner(
        t("reviewing_patch"),
        engine.review_patch,
        patch_file=patch_file,
        quiet=args.quiet,
    )
    pretty_print_reviews(
        results,
        args.quiet,
        min_confidence=getattr(args, "min_confidence", 0.0),
        severity_filter=getattr(args, "severity_filter", None),
    )
    attach_flow_graph(results)
    save_output(args.output_file, results, args.quiet)


def run_file_review(engine, file_path, args):
    from metis.i18n import t
    if not check_file_exists(file_path):
        return
    raw_result = with_spinner(
        t("reviewing_file", file_path=file_path),
        engine.review_file,
        file_path=file_path,
        quiet=args.quiet,
    )

    if raw_result and isinstance(raw_result.get("reviews"), list):
        results = {"reviews": [raw_result]}
    else:
        results = {"reviews": []}

    pretty_print_reviews(
        results,
        args.quiet,
        min_confidence=getattr(args, "min_confidence", 0.0),
        severity_filter=getattr(args, "severity_filter", None),
    )
    attach_flow_graph(results)
    save_output(args.output_file, results, args.quiet)


def run_review_code(engine, args):
    from metis.i18n import t
    if args.verbose:
        print_console(f"[cyan]{t('reviewing_codebase')}[/cyan]", args.quiet)
        total = len(engine.get_code_files())
        file_reviews = iterate_with_progress(total, engine.review_code())
        results = {"reviews": file_reviews}
    else:
        results = with_spinner(
            t("reviewing_codebase"), collect_reviews, engine, quiet=args.quiet
        )
    pretty_print_reviews(
        results,
        args.quiet,
        min_confidence=getattr(args, "min_confidence", 0.0),
        severity_filter=getattr(args, "severity_filter", None),
    )
    attach_flow_graph(results)
    save_output(args.output_file, results, args.quiet)


def run_index(engine, verbose=False, quiet=False):
    from metis.i18n import t
    if verbose:
        print_console(f"[cyan]{t('indexing_codebase')}[/cyan]", quiet)
        total = count_index_items(engine)
        if total > 0:
            iterate_with_progress(total, engine.index_prepare_nodes_iter())
            with_timer(
                t("embedding_indexes"), engine.index_finalize_embeddings, quiet=quiet
            )
            print_console(f"[green]{t('indexing_completed')}[/green]", quiet)
            return

    with_spinner(t("indexing_codebase"), engine.index_codebase, quiet=quiet)
    print_console(f"[green]{t('indexing_completed')}[/green]", quiet)


def run_update(engine, patch_file, args):
    from metis.i18n import t
    if not check_file_exists(patch_file):
        return
    file_diff = read_file_content(patch_file)
    with_spinner(t("updating_index"), engine.update_index, file_diff, quiet=args.quiet)
    print_console(f"[green]{t('index_update_completed')}[/green]", args.quiet)


def run_ask(engine, question):
    from metis.i18n import t
    answer = with_spinner(t("thinking"), engine.ask_question, question)
    print_console(f"[bold magenta]{t('metis_answer')}[/bold magenta]\n")
    if isinstance(answer, dict):
        if "code" in answer:
            print_console(
                f"[bold yellow]{t('code_context')}[/bold yellow] {escape(safe_decode_unicode(answer['code']))} \n"
            )
        if "docs" in answer:
            print_console(
                f"[bold blue]{t('documentation_context')}[/bold blue] {escape(safe_decode_unicode(answer['docs']))}"
            )
    else:
        print_console(escape(str(answer)))


def run_report(engine, args):
    """
    Generate a report from previous review results or run a new review.
    If output_file is specified, generate report in that format.
    If no output_file, prompt user for format.
    """
    from pathlib import Path
    from datetime import datetime

    # Determine output format and file
    if args.output_file:
        output_files = args.output_file
    else:
        # Default to HTML report with timestamp
        Path("reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = [f"reports/metis_report_{timestamp}.html"]
        from metis.i18n import t
        print_console(
            f"[cyan]{t('no_output_file_specified', path=output_files[0])}[/cyan]",
            args.quiet,
        )
    # Run review if needed (this will generate results)
    if args.verbose:
        from metis.i18n import t
        print_console(f"[cyan]{t('generating_report')}[/cyan]", args.quiet)
        total = len(engine.get_code_files())
        file_reviews = iterate_with_progress(total, engine.review_code())
        results = {"reviews": file_reviews}
    else:
        from metis.i18n import t
        results = with_spinner(
            t("generating_report"), collect_reviews, engine, quiet=args.quiet
        )

    # Apply filtering and sorting
    filtered_results = {"reviews": []}
    for file_review in results.get("reviews", []):
        reviews = file_review.get("reviews", [])
        if reviews:
            filtered_reviews = sort_and_filter_reviews(
                reviews,
                min_confidence=getattr(args, "min_confidence", 0.0),
                severity_filter=getattr(args, "severity_filter", None),
            )
            if filtered_reviews:
                filtered_results["reviews"].append(
                    {**file_review, "reviews": filtered_reviews}
                )
        else:
            filtered_results["reviews"].append(file_review)

    # Save reports
    attach_flow_graph(filtered_results)
    save_output(output_files, filtered_results, args.quiet)

    # Print summary
    total_issues = sum(
        len(fr.get("reviews", [])) for fr in filtered_results.get("reviews", [])
    )
    from metis.i18n import t
    print_console(
        f"[green]{t('report_generated', count=total_issues)}[/green]",
        args.quiet,
    )
