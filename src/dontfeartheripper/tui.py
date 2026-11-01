import curses
from concurrent.futures import Future, ThreadPoolExecutor
import os
from queue import Empty, Queue
import signal
import sys
import textwrap
from pathlib import Path

from .container import (
    classify_container,
    count_album_nodes,
    detect_containers,
    write_collection_nfo,
    write_container_metadata,
    write_container_poster,
)
from .cover import (
    analyze_covers,
    execute_download_plan,
    preview_fetch,
)
from .organizer import (
    apply_rename_plan,
    build_rename_plan,
    undo_renames,
)
from .progress import (
    CancellationToken,
    OperationCancelled,
    ProgressCallback,
    humanize_progress_message,
    report_progress,
)
from .library_search import search_library
from .library_db import invalidate_library, load_library
from .jellyfin import (
    JellyfinError,
    generate_jellyfin_collections,
)
from .quality import analyze_quality
from .repair import (
    analyze_repairs,
    apply_repairs,
    undo_repairs,
)
from .stats import build_stats


MAIN_MENU = (
    ("overview", "Overview"),
    ("library", "Library"),
    ("artwork", "Artwork"),
    ("collections", "Collections"),
    ("maintenance", "Maintenance"),
    ("quit", "Quit"),
)

MENU_GROUPS = {
    "overview": (
        ("dashboard", "Dashboard"),
    ),
    "library": (
        ("search", "Search library"),
        ("scan", "Library scan"),
        ("doctor", "Diagnostics"),
        ("stats", "Statistics"),
        ("quality", "Quality report"),
    ),
    "artwork": (
        ("covers", "Missing artwork"),
        ("covers-download", "Fetch & download covers"),
    ),
    "collections": (
        ("containers", "Containers"),
        ("jellyfin-preview", "Jellyfin collection plan"),
        ("jellyfin-apply", "Publish Jellyfin collections"),
        ("container-write", "Write container files"),
    ),
    "maintenance": (
        ("repair-preview", "Repair preview"),
        ("repair-apply", "Apply repairs"),
        ("repair-undo", "Undo repairs"),
        ("rename-preview", "Rename preview"),
        ("rename-apply", "Apply renames"),
        ("rename-undo", "Undo rename"),
    ),
}

BACK_ACTION = "back"
BACK_ENTRY = (BACK_ACTION, "Back to main menu")

CONFIRM_ACTIONS = {
    "repair-apply",
    "rename-apply",
    "container-write",
    "rename-undo",
    "repair-undo",
    "covers-download",
    "jellyfin-apply",
}


def _call_with_progress(function, *args, progress=None):
    if progress is None:
        return function(*args)
    return function(*args, progress)


def _scan_library(root, progress=None):
    return load_library(
        root,
        progress,
        refresh=True,
    )


def _load_library(root, progress=None):
    return load_library(root, progress)


def _action_lines(
    action,
    root,
    items,
    progress: ProgressCallback | None = None,
    search_query=None,
):
    report_progress(progress, f"Preparing {action.replace('-', ' ')}")
    if action == "dashboard":
        stats = build_stats(items)
        quality = analyze_quality(items)
        return [
            f"Library: {root}",
            "",
            f"Albums: {stats['albums']}    "
            f"Compilations: {stats['compilations']}    "
            f"Soundtracks: {stats['soundtracks']}",
            f"Containers: {stats['containers']}    "
            f"Rename candidates: {stats['rename_candidates']}",
            f"Quality score: {quality['quality_score']}%",
            "",
            "Choose a task from the menu.",
            "Changes are always previewed first and require confirmation.",
        ]

    if action in ("scan", "doctor"):
        if action == "scan":
            lines = [
                f"[{item.category.upper()}] {item.path}"
                for item in items
            ]
            return lines or ["No albums found."]

        lines = []
        for item in items:
            if item.container_directory:
                lines.append(f"INFO  {item.path} (container directory)")
            if item.cryptic:
                detail = (
                    f" -> {item.suggested_name}"
                    if item.suggested_name
                    else ""
                )
                lines.append(f"WARN  {item.path} (cryptic name){detail}")
            if item.rename_collision:
                lines.append(f"WARN  {item.path} (rename collision)")
        return lines or ["No diagnostics to report."]

    if action == "stats":
        stats = build_stats(items)
        return [
            f"{name.replace('_', ' ').title()}: {value}"
            for name, value in stats.items()
            if name != "schema_version"
        ]

    if action == "quality":
        report = analyze_quality(items)
        lines = [f"Quality score: {report['quality_score']}%"]
        lines.extend(
            f"{issue['severity'].upper()}  {issue['type']}: {issue['path']}"
            for issue in report["issues"]
        )
        return lines

    if action == "search":
        results = search_library(
            root,
            search_query or "",
            progress,
        )
        if not results:
            return [f'No matches found for "{search_query}".']
        return [
            f'Search results for "{search_query}"',
            f"Matches: {len(results)}",
            "",
            *results,
        ]

    if action == "covers":
        report = _call_with_progress(
            analyze_covers,
            items,
            progress=progress,
        )
        lines = [
            f"Missing covers: {len(report['missing_covers'])}",
            "",
        ]
        lines.extend(
            f"{item['artist'] or 'Unknown artist'} - "
            f"{item['album'] or Path(item['path']).name}"
            for item in report["missing_covers"]
        )
        return lines

    if action == "containers":
        containers = _call_with_progress(
            detect_containers,
            root,
            progress=progress,
        )
        if not containers:
            return ["No containers found."]
        return [
            f"{container['path']} "
            f"({classify_container(container)}, "
            f"{count_album_nodes(container['children'])} albums)"
            for container in containers
        ]

    if action in ("jellyfin-preview", "jellyfin-apply"):
        url = os.environ.get("JELLYFIN_URL")
        api_key = os.environ.get("JELLYFIN_API_KEY")
        if not url or not api_key:
            return [
                "Jellyfin is not configured.",
                "Set JELLYFIN_URL and JELLYFIN_API_KEY",
                "in the environment before starting the TUI.",
            ]
        try:
            report = generate_jellyfin_collections(
                _call_with_progress(
                    detect_containers,
                    root,
                    progress=progress,
                ),
                url,
                api_key,
                root,
                server_root=os.environ.get(
                    "JELLYFIN_LIBRARY_ROOT"
                ),
                apply=action == "jellyfin-apply",
                progress=progress,
            )
        except JellyfinError as exc:
            return [f"Jellyfin error: {exc}"]

        lines = [
            "Jellyfin collection plan"
            if action == "jellyfin-preview"
            else "Jellyfin collection results",
            "",
        ]
        for collection in report["collections"]:
            state = (
                "UPDATE"
                if collection["collection_id"]
                else "CREATE"
            )
            lines.append(
                f"{state} {collection['name']}: "
                f"{collection['matched_count']}/"
                f"{collection['album_count']} albums"
            )
            lines.extend(
                f"  NOT FOUND: {path}"
                for path in collection["missing_paths"]
            )
        if action == "jellyfin-apply":
            lines.extend(
                f"{result['status'].upper()} {result['name']}"
                + (
                    f": {result['reason']}"
                    if result.get("reason")
                    else ""
                )
                for result in report["results"]
            )
        if len(report["collections"]) == 0:
            lines.append("No album containers with multiple albums found.")
        return lines

    if action == "covers-download":
        _call_with_progress(
            preview_fetch,
            items,
            progress=progress,
        )
        report = _call_with_progress(
            execute_download_plan,
            items,
            progress=progress,
        )
        downloads = report["downloads"]
        downloaded = sum(
            1
            for item in downloads
            if item["success"] and not item["skipped"]
        )
        skipped = sum(1 for item in downloads if item["skipped"])
        failed = sum(1 for item in downloads if not item["success"])
        return [
            f"Downloaded: {downloaded}",
            f"Skipped: {skipped}",
            f"Failed: {failed}",
        ]

    if action.startswith("repair"):
        report_progress(progress, "Analyzing tag repairs")
        report = analyze_repairs(items, progress)
        repairs = report["repairs"]
        if action == "repair-preview":
            lines = [f"Planned repairs: {len(repairs)}"]
            lines.extend(
                f"{item['path']}  {item['field']}: "
                f"{item['old']!r} -> {item['new']!r}"
                for item in repairs
            )
            return lines
        if action == "repair-apply":
            if not repairs:
                return ["No repairs to apply."]
            report_progress(
                progress,
                f"Updating {len(repairs)} repair groups",
                0,
                len(repairs),
            )
            return [
                f"Updated tags: {apply_repairs(repairs, progress)}",
                "Rollback file: .dftr-last-repair.json",
            ]
        if action == "repair-undo":
            return [f"Reverted tags: {undo_repairs(progress)}"]

    if action.startswith("rename"):
        report_progress(progress, "Building rename plan")
        plan = build_rename_plan(items)
        if action == "rename-preview":
            lines = [f"Rename candidates: {len(plan)}"]
            lines.extend(
                (
                    f"SKIP  {entry['from']} ({entry['skip_reason']})"
                    if entry["skip_reason"]
                    else f"{entry['from']} -> {entry['to']}"
                )
                for entry in plan
            )
            return lines
        if action == "rename-apply":
            result = apply_rename_plan(plan, progress)
            return [
                f"Renamed directories: {result['renamed']}",
                (
                    "Rollback file: .dftr-last-rename.json"
                    if result["renamed"]
                    else "No changes made."
                ),
            ]
        if action == "rename-undo":
            result = undo_renames(progress)
            return [
                f"Reverted directories: {result['reverted']}",
                *(
                    f"SKIP  {path} ({reason})"
                    for path, reason in result["skipped"]
                ),
            ]

    if action == "container-write":
        report_progress(progress, "Finding containers")
        containers = _call_with_progress(
            detect_containers,
            root,
            progress=progress,
        )
        written = 0
        for index, container in enumerate(containers, start=1):
            report_progress(
                progress,
                f"Writing container files: {container['path'].name}",
                index - 1,
                len(containers),
            )
            write_container_metadata(container)
            write_collection_nfo(container)
            write_container_poster(container)
            written += 1
            report_progress(
                progress,
                f"Wrote container files: {container['path'].name}",
                index,
                len(containers),
            )
        return [f"Container metadata sets written: {written}"]

    return []


def _put(screen, y, x, text, width, attr=0):
    if width <= 0:
        return
    try:
        screen.addnstr(y, x, str(text), width, attr)
    except curses.error:
        pass


def _wrapped_lines(lines, width):
    return [
        part
        for line in lines
        for part in (
            textwrap.wrap(
                str(line),
                width=max(1, width),
                replace_whitespace=False,
                drop_whitespace=True,
            )
            or [""]
        )
    ]


def _scroll_limit(screen, lines):
    height, width = screen.getmaxyx()
    sidebar_width = min(25, width // 3)
    content_width = width - sidebar_width - 4
    visible_height = height - 2 - 5 - 1
    return max(
        0,
        len(_wrapped_lines(lines, content_width)) - visible_height,
    )


def _mouse_scroll_offset(screen, lines, offset, x, y, state):
    if state & getattr(curses, "BUTTON4_PRESSED", 0):
        delta = -3
    elif state & getattr(curses, "BUTTON5_PRESSED", 0):
        delta = 3
    else:
        return None

    height, width = screen.getmaxyx()
    sidebar_width = min(25, width // 3)
    content_x = sidebar_width + 2
    menu_top = 5
    footer_y = height - 2
    visible_height = footer_y - menu_top - 1
    if (
        x < content_x
        or y < menu_top
        or y >= menu_top + visible_height
    ):
        return None

    max_offset = _scroll_limit(screen, lines)
    return max(0, min(offset + delta, max_offset))


def _draw(
    screen,
    root,
    entries,
    selected,
    lines,
    offset,
    status,
    confirm_action,
    menu_title,
    content_title,
    *,
    busy=False,
    progress_current=None,
    progress_total=None,
    frame=0,
    search_query=None,
):
    screen.erase()
    height, width = screen.getmaxyx()
    if height < 12 or width < 58:
        _put(
            screen,
            0,
            0,
            "Terminal too small. Resize to at least 58x12.",
            width,
        )
        screen.refresh()
        return

    title_attr = curses.color_pair(1) | curses.A_BOLD
    selected_attr = curses.color_pair(2) | curses.A_BOLD
    _put(
        screen,
        0,
        2,
        "DFTR  /  MUSIC LIBRARY",
        width - 4,
        title_attr,
    )
    _put(screen, 1, 2, str(root), width - 4)
    _put(screen, 2, 0, "-" * (width - 1), width - 1)

    sidebar_width = min(25, width // 3)
    section_y = 3
    menu_top = 5
    footer_y = height - 2
    _put(screen, section_y, 1, menu_title, sidebar_width - 2, title_attr)
    content_x = sidebar_width + 2
    content_width = width - content_x - 2
    _put(
        screen,
        section_y,
        content_x,
        content_title,
        content_width,
        title_attr,
    )
    _put(screen, 4, 0, "-" * (width - 1), width - 1)

    menu_height = footer_y - menu_top
    menu_offset = max(
        0,
        min(
            selected - menu_height + 1,
            len(entries) - menu_height,
        ),
    )

    for row in range(menu_height):
        index = menu_offset + row
        if index >= len(entries):
            break
        _, label = entries[index]
        attr = selected_attr if index == selected else 0
        marker = ">" if index == selected else " "
        _put(
            screen,
            menu_top + row,
            1,
            f"{marker} {label}",
            sidebar_width - 2,
            attr,
        )

    separator_x = sidebar_width
    for row in range(section_y, footer_y):
        _put(screen, row, separator_x, "|", 1)

    if busy:
        bar_width = max(1, min(16, content_width - 17))
        if progress_total and progress_total > 0:
            completed = min(
                bar_width,
                round(
                    bar_width
                    * min(progress_current or 0, progress_total)
                    / progress_total
                ),
            )
            bar = "#" * completed + "-" * (bar_width - completed)
            percent = round(
                100 * min(progress_current or 0, progress_total)
                / progress_total
            )
            progress_label = (
                f"[{bar}] {percent:3d}% · "
                f"{progress_current or 0}/{progress_total}"
            )
        else:
            block_width = min(5, bar_width)
            travel = max(1, bar_width - block_width)
            position = frame % (travel * 2)
            position = position if position <= travel else travel * 2 - position
            bar = (
                "-" * position
                + "#" * block_width
                + "-" * (bar_width - position - block_width)
            )
            progress_label = f"[{bar}]"
        _put(
            screen,
            footer_y - 1,
            content_x,
            progress_label,
            content_width,
            curses.color_pair(1),
        )
    else:
        _put(screen, footer_y - 1, 0, "-" * (width - 1), width - 1)
    visible_height = footer_y - menu_top - 1
    if search_query is not None:
        _put(
            screen,
            menu_top,
            content_x,
            "Search songs, albums, artists, genres, and collections.",
            content_width,
        )
        _put(
            screen,
            menu_top + 2,
            content_x,
            "Search:",
            content_width,
            title_attr,
        )
        _put(
            screen,
            menu_top + 3,
            content_x,
            f"{search_query}_",
            content_width,
        )
        wrapped_lines = []
    else:
        wrapped_lines = _wrapped_lines(lines, content_width)
    for row, part in enumerate(
        wrapped_lines[offset : offset + visible_height]
    ):
        _put(
            screen,
            menu_top + row,
            content_x,
            part,
            content_width,
        )

    if busy:
        spinner = ("|", "/", "-", chr(92))[frame % 4]
        status = f"{spinner} {status}"
    _put(
        screen,
        footer_y,
        1,
        status[: max(0, width - 2)],
        width - 2,
        curses.color_pair(3),
    )
    if confirm_action:
        help_text = "Confirm? [y] Yes  [n] No"
    elif busy:
        help_text = "Esc/Ctrl-C: stop safely · current step will finish first"
    elif search_query is not None:
        help_text = "Type to search  Enter: search  Backspace: delete  Esc: cancel"
    elif menu_title == "MAIN MENU":
        help_text = "Up/Down: select  Enter: open  r: refresh  q: quit"
    else:
        help_text = (
            "Wheel/PgUp/PgDn: scroll · Enter: open · Esc: menu · "
            "r: refresh · q: quit"
        )
    _put(screen, height - 1, 1, help_text, width - 2)
    screen.refresh()


def _main(screen, root):
    curses.curs_set(0)
    screen.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)

    if hasattr(screen, "timeout"):
        screen.timeout(100)
    mouse_events = (
        getattr(curses, "BUTTON4_PRESSED", 0)
        | getattr(curses, "BUTTON5_PRESSED", 0)
    )
    if mouse_events:
        try:
            curses.mousemask(mouse_events)
        except curses.error:
            pass

    events: Queue = Queue()
    executor = ThreadPoolExecutor(max_workers=1)
    active_future: Future | None = None
    active_token = CancellationToken()
    job_kind = "initial-scan"
    job_message = "Scanning music library"
    progress_current = None
    progress_total = None
    frame = 0
    items = []
    selected_main = 0
    selected = 0
    offset = 0
    status = "Scanning music library"
    lines = _main_menu_lines()
    confirm_action = None
    active_group = None
    search_query = None
    job_action = None

    def start_job(operation):
        nonlocal active_future, active_token
        token = CancellationToken()

        def progress_callback(message, current=None, total=None):
            token.raise_if_cancelled()
            events.put((message, current, total))

        def run():
            token.raise_if_cancelled()
            result = operation(progress_callback)
            token.raise_if_cancelled()
            return result

        active_token = token
        active_future = executor.submit(run)

    def handle_sigint(signum, frame):
        if active_future is not None:
            active_token.cancel()

    previous_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_sigint)
    start_job(lambda progress: _load_library(root, progress))

    try:
        while True:
            if active_group is None:
                entries = MAIN_MENU
                menu_title = "MAIN MENU"
            else:
                entries = (*MENU_GROUPS[active_group], BACK_ENTRY)
                menu_title = dict(MAIN_MENU)[active_group].upper()
            busy = active_future is not None
            _draw(
                screen,
                root,
                entries,
                selected,
                lines,
                offset,
                status,
                confirm_action,
                menu_title,
                (
                    "SECTIONS"
                    if active_group is None
                    else (
                        "LIBRARY STATUS"
                        if active_group == "overview"
                        else "SECTION GUIDE"
                    )
                ),
                busy=busy,
                progress_current=progress_current,
                progress_total=progress_total,
                frame=frame,
                search_query=search_query,
            )
            frame += 1

            if busy:
                while True:
                    try:
                        (
                            job_message,
                            progress_current,
                            progress_total,
                        ) = events.get_nowait()
                    except Empty:
                        break
                    status = humanize_progress_message(job_message)

                if active_future.done():
                    try:
                        result = active_future.result()
                    except OperationCancelled as exc:
                        if job_action in {
                            "repair-apply",
                            "repair-undo",
                            "rename-apply",
                            "rename-undo",
                        }:
                            invalidate_library(root)
                        lines = [
                            "Operation stopped at a safe checkpoint.",
                            str(exc),
                        ]
                        if job_action == "repair-apply":
                            lines.append(
                                "Completed tag changes are recorded in "
                                ".dftr-last-repair.json."
                            )
                        elif job_action == "rename-apply":
                            lines.append(
                                "Completed folder changes are recorded in "
                                ".dftr-last-rename.json."
                            )
                        elif job_action == "jellyfin-apply":
                            lines.append(
                                "Jellyfin may contain completed changes; "
                                "inspect its collections before retrying."
                            )
                        status = "Action cancelled safely."
                    except Exception as exc:
                        lines = ["Task failed.", str(exc)]
                        status = "Task failed"
                    else:
                        if job_kind in ("initial-scan", "refresh-scan"):
                            items = result
                            status = f"Found {len(items)} library entries."
                            if job_kind == "initial-scan":
                                lines = _main_menu_lines()
                            elif active_group == "overview":
                                lines = _action_lines(
                                    "dashboard",
                                    root,
                                    items,
                                )
                        else:
                            lines, refreshed_items = result
                            if refreshed_items is not None:
                                items = refreshed_items
                            status = "Action completed."
                            offset = 0
                    active_future = None
                    progress_current = None
                    progress_total = None
                    continue
                key = screen.getch()
                if key in (27, 3):
                    active_token.cancel()
                    status = "Stopping safely; finishing the current step..."
                continue

            key = screen.getch()
            if search_query is not None:
                if key in (curses.KEY_ENTER, 10, 13):
                    if not search_query.strip():
                        status = "Type a search word before starting."
                        continue
                    query = search_query.strip()
                    search_query = None
                    job_kind = "action"
                    job_action = "search"
                    start_job(
                        lambda progress: _action_job(
                            "search",
                            root,
                            items,
                            progress,
                            query,
                        )
                    )
                    status = f'Searching the library for "{query}"'
                    progress_current = None
                    progress_total = None
                elif key in (27,):
                    search_query = None
                    status = "Search cancelled."
                elif key in (
                    curses.KEY_BACKSPACE,
                    8,
                    127,
                ):
                    search_query = search_query[:-1]
                elif 0 <= key <= 0x10FFFF:
                    character = chr(key)
                    if character.isprintable() and len(search_query) < 160:
                        search_query += character
                continue

            if confirm_action:
                if key in (ord("y"), ord("Y")):
                    action = confirm_action
                    confirm_action = None

                    def run_confirmed_action(progress):
                        if action in (
                            "rename-apply",
                            "rename-undo",
                            "repair-apply",
                            "repair-undo",
                        ):
                            invalidate_library(root)
                        action_lines = _action_lines(
                            action,
                            root,
                            items,
                            progress,
                        )
                        refreshed = None
                        if action in (
                            "rename-apply",
                            "rename-undo",
                            "repair-apply",
                            "repair-undo",
                        ):
                            refreshed = _scan_library(
                                root,
                                progress,
                            )
                        return action_lines, refreshed

                    job_kind = "action"
                    job_action = action
                    start_job(
                        lambda progress: run_confirmed_action(progress)
                    )
                    job_message = f"Running {action.replace('-', ' ')}"
                    status = job_message
                    progress_current = None
                    progress_total = None
                elif key in (ord("n"), ord("N"), 27):
                    confirm_action = None
                    status = "Action cancelled."
                continue

            if key in (ord("q"), ord("Q")):
                break
            if active_group is not None and key in (
                27,
                curses.KEY_BACKSPACE,
                8,
                127,
            ):
                active_group = None
                selected = selected_main
                lines = _main_menu_lines()
                offset = 0
                continue
            if key == getattr(curses, "KEY_MOUSE", None):
                try:
                    _, mouse_x, mouse_y, _, state = curses.getmouse()
                except curses.error:
                    continue
                new_offset = _mouse_scroll_offset(
                    screen,
                    lines,
                    offset,
                    mouse_x,
                    mouse_y,
                    state,
                )
                if new_offset is not None:
                    offset = new_offset
                continue
            if key in (curses.KEY_UP, ord("k")):
                selected = (selected - 1) % len(entries)
                continue
            if key in (curses.KEY_DOWN, ord("j")):
                selected = (selected + 1) % len(entries)
                continue
            if active_group is not None and key == curses.KEY_PPAGE:
                offset = max(
                    0,
                    min(offset - 8, _scroll_limit(screen, lines)),
                )
                continue
            if active_group is not None and key == curses.KEY_NPAGE:
                offset = min(offset + 8, _scroll_limit(screen, lines))
                continue
            if key in (ord("r"), ord("R")):
                job_kind = "refresh-scan"
                start_job(lambda progress: _scan_library(root, progress))
                status = "Refreshing music library"
                progress_current = None
                progress_total = None
                continue
            if key in (curses.KEY_ENTER, 10, 13):
                action, label = entries[selected]
                if active_group is not None and action == "search":
                    search_query = ""
                    status = "Search songs, albums, artists, genres, and collections."
                    continue
                if active_group is None:
                    if action == "quit":
                        break
                    selected_main = selected
                    active_group = action
                    selected = 0
                    offset = 0
                    if action == "overview":
                        job_kind = "action"
                        job_action = "dashboard"
                        start_job(
                            lambda progress: _action_job(
                                "dashboard",
                                root,
                                items,
                                progress,
                            )
                        )
                        status = "Preparing dashboard"
                    else:
                        lines = [
                            f"Choose an option from {label}.",
                            "",
                            "Use the arrow keys to browse this section.",
                        ]
                        status = f"{label} menu"
                    continue
                if action == BACK_ACTION:
                    active_group = None
                    selected = selected_main
                    lines = _main_menu_lines()
                    offset = 0
                    status = "Main menu"
                    continue
                if action in CONFIRM_ACTIONS:
                    confirm_action = action
                    status = (
                        "This action changes files, tags, or the Jellyfin server."
                    )
                    continue
                job_kind = "action"
                job_action = action
                start_job(
                    lambda progress: _action_job(
                        action,
                        root,
                        items,
                        progress,
                    )
                )
                status = f"Loading {label}"
                offset = 0
    finally:
        signal.signal(signal.SIGINT, previous_sigint_handler)
        executor.shutdown(wait=True)


def _main_menu_lines():
    return [
        "Choose a section from the main menu.",
        "",
        "Overview  Dashboard with library counts and quality score.",
        "Library  Search, browse, diagnose and review audio quality.",
        "Artwork  Find missing covers and fetch artwork.",
        "Collections  Inspect containers and publish to Jellyfin.",
        "Maintenance  Preview and apply tag or folder repairs.",
        "",
        "Changes require confirmation before they are applied.",
    ]


def _action_job(action, root, items, progress, search_query=None):
    return (
        _action_lines(action, root, items, progress, search_query),
        None,
    )


def run_tui(root: Path) -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("The TUI requires an interactive terminal.")
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    curses.wrapper(_main, root)
