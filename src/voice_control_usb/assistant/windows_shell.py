"""Modern native Windows shell for typed and controlled speech input."""

from __future__ import annotations

from queue import Empty, SimpleQueue
from threading import Thread
from typing import Callable

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.command_legend import (
    COMMAND_SECTIONS,
    filter_command_sections,
)
from voice_control_usb.assistant.speech_flow import (
    dispatch_transcription,
    record_speech_failure,
)
from voice_control_usb.audio.transcriber import (
    SpeechTranscriber,
    TranscriptionResult,
)


def _enable_dark_title_bar(root: object) -> None:
    """Ask modern Windows versions to draw the native title bar in dark mode."""

    import ctypes
    import sys

    if sys.platform != "win32":
        return
    try:
        root.update_idletasks()  # type: ignore[attr-defined]
        handle = ctypes.windll.user32.GetParent(root.winfo_id())  # type: ignore[attr-defined]
        enabled = ctypes.c_int(1)
        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                handle,
                attribute,
                ctypes.byref(enabled),
                ctypes.sizeof(enabled),
            )
            if result == 0:
                break
    except (AttributeError, OSError):
        # Older Windows builds can simply retain their system title-bar theme.
        return


def run_windows_shell(
    app: AssistantApp,
    transcriber: SpeechTranscriber,
    shutdown_requested: Callable[[], bool] | None = None,
) -> None:
    """Run the visible command deck and push-to-talk assistant window."""

    import tkinter as tk
    from tkinter import ttk

    colors = {
        "window": "#060A12",
        "sidebar": "#0A1020",
        "panel": "#0D1526",
        "card": "#111C30",
        "card_hover": "#17243B",
        "border": "#22304A",
        "text": "#E8F1FF",
        "muted": "#8EA3BF",
        "faint": "#5E7390",
        "cyan": "#38BDF8",
        "teal": "#22D3A7",
        "purple": "#A78BFA",
        "amber": "#F59E0B",
        "pink": "#F472B6",
        "danger": "#FB7185",
    }

    root = tk.Tk()
    root.title("Voice Control // Command Console")
    root.geometry("1520x820")
    root.minsize(1180, 680)
    root.configure(background=colors["window"])
    root.option_add("*Font", ("Segoe UI", 10))
    root.option_add("*TCombobox*Listbox.background", colors["card"])
    root.option_add("*TCombobox*Listbox.foreground", colors["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", colors["cyan"])
    root.option_add("*TCombobox*Listbox.selectForeground", colors["window"])
    _enable_dark_title_bar(root)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        "Console.TCombobox",
        fieldbackground=colors["card"],
        background=colors["card"],
        foreground=colors["text"],
        arrowcolor=colors["cyan"],
        bordercolor=colors["border"],
        lightcolor=colors["border"],
        darkcolor=colors["border"],
        padding=8,
    )
    style.map(
        "Console.TCombobox",
        fieldbackground=[("readonly", colors["card"])],
        foreground=[("readonly", colors["text"])],
        selectbackground=[("readonly", colors["card"])],
        selectforeground=[("readonly", colors["text"])],
    )

    def make_dark_scrollbar(
        parent: tk.Misc,
        target: tk.Text | tk.Canvas,
        trough_color: str,
    ) -> tk.Canvas:
        """Create a compact dark scrollbar independent of the Windows theme."""

        bar = tk.Canvas(
            parent,
            width=9,
            background=trough_color,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
        )
        thumb = bar.create_rectangle(
            2,
            0,
            7,
            20,
            fill=colors["border"],
            outline="",
        )
        position = [0.0, 1.0]
        drag_offset = [0.0]

        def redraw(_event: object | None = None) -> None:
            height = max(bar.winfo_height(), 1)
            top = position[0] * height
            bottom = position[1] * height
            bar.coords(thumb, 2, top, 7, max(bottom, top + 18))
            bar.itemconfigure(
                thumb,
                state="hidden" if position == [0.0, 1.0] else "normal",
            )

        def sync(first: str, last: str) -> None:
            position[:] = [float(first), float(last)]
            redraw()

        def move_to_pointer(event: tk.Event[tk.Misc]) -> None:
            height = max(bar.winfo_height(), 1)
            visible_fraction = position[1] - position[0]
            target.yview_moveto(
                max(
                    0.0,
                    min(
                        1.0 - visible_fraction,
                        (event.y - drag_offset[0]) / height,
                    ),
                )
            )

        def begin_drag(event: tk.Event[tk.Misc]) -> None:
            height = max(bar.winfo_height(), 1)
            top = position[0] * height
            bottom = position[1] * height
            drag_offset[0] = (
                event.y - top if top <= event.y <= bottom else (bottom - top) / 2
            )
            move_to_pointer(event)

        bar.bind("<Configure>", redraw)
        bar.bind("<Button-1>", begin_drag)
        bar.bind("<B1-Motion>", move_to_pointer)
        bar.bind(
            "<Enter>",
            lambda _event: bar.itemconfigure(thumb, fill=colors["faint"]),
        )
        bar.bind(
            "<Leave>",
            lambda _event: bar.itemconfigure(thumb, fill=colors["border"]),
        )
        target.configure(yscrollcommand=sync)
        return bar

    shell = tk.Frame(root, background=colors["window"])
    shell.pack(fill="both", expand=True)
    shell.grid_rowconfigure(0, weight=1)
    shell.grid_columnconfigure(2, weight=1)

    # Command deck sidebar.
    sidebar = tk.Frame(
        shell,
        width=370,
        background=colors["sidebar"],
        highlightbackground=colors["border"],
        highlightthickness=1,
    )
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)
    sidebar.grid_columnconfigure(0, weight=1)
    sidebar.grid_rowconfigure(5, weight=1)

    brand = tk.Frame(sidebar, background=colors["sidebar"])
    brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 4))
    tk.Label(
        brand,
        text="VC // 01",
        background=colors["teal"],
        foreground=colors["window"],
        font=("Consolas", 9, "bold"),
        padx=7,
        pady=3,
    ).pack(side="left")
    tk.Label(
        brand,
        text="COMMAND DECK",
        background=colors["sidebar"],
        foreground=colors["text"],
        font=("Segoe UI Semibold", 15),
    ).pack(side="left", padx=(10, 0))
    tk.Button(
        brand,
        text="ROUTINES",
        command=lambda: toggle_routine_panel(True),
        background=colors["card"],
        activebackground=colors["pink"],
        foreground=colors["muted"],
        activeforeground=colors["window"],
        font=("Consolas", 7, "bold"),
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=7,
        pady=4,
    ).pack(side="right")
    tk.Label(
        sidebar,
        text="Every supported voice phrase, organized and ready to load.",
        background=colors["sidebar"],
        foreground=colors["muted"],
        font=("Segoe UI", 9),
        anchor="w",
        justify="left",
        wraplength=320,
    ).grid(row=1, column=0, sticky="ew", padx=22, pady=(2, 16))

    search_frame = tk.Frame(
        sidebar,
        background=colors["card"],
        highlightbackground=colors["border"],
        highlightthickness=1,
    )
    search_frame.grid(row=2, column=0, sticky="ew", padx=22)
    tk.Label(
        search_frame,
        text="/",
        background=colors["card"],
        foreground=colors["cyan"],
        font=("Consolas", 14, "bold"),
    ).pack(side="left", padx=(11, 2), pady=8)
    search_query = tk.StringVar()
    search_entry = tk.Entry(
        search_frame,
        textvariable=search_query,
        background=colors["card"],
        foreground=colors["text"],
        insertbackground=colors["cyan"],
        selectbackground=colors["cyan"],
        selectforeground=colors["window"],
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    search_entry.pack(side="left", fill="x", expand=True, padx=(4, 10), pady=8)

    categories = tk.Frame(sidebar, background=colors["sidebar"])
    categories.grid(row=3, column=0, sticky="ew", padx=18, pady=(14, 8))
    active_category = tk.StringVar(value="All")
    category_buttons: dict[str, tk.Button] = {}

    result_summary = tk.StringVar(value="")
    tk.Label(
        sidebar,
        textvariable=result_summary,
        background=colors["sidebar"],
        foreground=colors["faint"],
        font=("Consolas", 8, "bold"),
        anchor="w",
    ).grid(row=4, column=0, sticky="ew", padx=22, pady=(2, 6))

    legend_frame = tk.Frame(sidebar, background=colors["sidebar"])
    legend_frame.grid(row=5, column=0, sticky="nsew", padx=(14, 8), pady=(0, 10))
    legend_frame.grid_rowconfigure(0, weight=1)
    legend_frame.grid_columnconfigure(0, weight=1)
    legend_canvas = tk.Canvas(
        legend_frame,
        background=colors["sidebar"],
        highlightthickness=0,
        borderwidth=0,
    )
    legend_scroll = make_dark_scrollbar(
        legend_frame,
        legend_canvas,
        colors["sidebar"],
    )
    legend_canvas.grid(row=0, column=0, sticky="nsew")
    legend_scroll.grid(row=0, column=1, sticky="ns")
    legend_content = tk.Frame(legend_canvas, background=colors["sidebar"])
    legend_window = legend_canvas.create_window(
        (0, 0), window=legend_content, anchor="nw"
    )
    legend_content.bind(
        "<Configure>",
        lambda _event: legend_canvas.configure(scrollregion=legend_canvas.bbox("all")),
    )
    legend_canvas.bind(
        "<Configure>",
        lambda event: legend_canvas.itemconfigure(legend_window, width=event.width),
    )

    tk.Label(
        sidebar,
        text="Click any command to load it  //  <WORDS> means replace this part",
        background=colors["sidebar"],
        foreground=colors["faint"],
        font=("Consolas", 8),
        anchor="w",
        justify="left",
        wraplength=330,
    ).grid(row=6, column=0, sticky="ew", padx=22, pady=(0, 16))

    # Swappable routine builder. Commands are arranged and run left-to-right.
    routine_panel = tk.Frame(
        shell,
        width=360,
        background=colors["panel"],
        highlightbackground=colors["border"],
        highlightthickness=1,
    )
    routine_panel.grid(row=0, column=1, sticky="nsew")
    routine_panel.grid_propagate(False)
    routine_panel.grid_columnconfigure(0, weight=1)
    routine_panel.grid_rowconfigure(5, weight=1)

    routine_header = tk.Frame(routine_panel, background=colors["panel"])
    routine_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(21, 6))
    routine_header.grid_columnconfigure(0, weight=1)
    tk.Label(
        routine_header,
        text="ROUTINE BUILDER",
        background=colors["panel"],
        foreground=colors["text"],
        font=("Segoe UI Semibold", 15),
    ).grid(row=0, column=0, sticky="w")
    tk.Button(
        routine_header,
        text="HIDE",
        command=lambda: toggle_routine_panel(False),
        background=colors["card"],
        activebackground=colors["border"],
        foreground=colors["muted"],
        activeforeground=colors["text"],
        font=("Consolas", 8, "bold"),
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=8,
        pady=4,
    ).grid(row=0, column=1, sticky="e")
    tk.Label(
        routine_panel,
        text="Drag commands from the deck. Steps run in numbered order from left to right.",
        background=colors["panel"],
        foreground=colors["muted"],
        font=("Segoe UI", 9),
        justify="left",
        anchor="w",
        wraplength=320,
    ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 13))

    routine_name_row = tk.Frame(routine_panel, background=colors["panel"])
    routine_name_row.grid(row=2, column=0, sticky="ew", padx=18)
    routine_name_row.grid_columnconfigure(0, weight=1)
    routine_name = tk.StringVar()
    routine_name_entry = tk.Entry(
        routine_name_row,
        textvariable=routine_name,
        background=colors["card"],
        foreground=colors["text"],
        insertbackground=colors["pink"],
        relief="flat",
        borderwidth=0,
        font=("Consolas", 10),
    )
    routine_name_entry.grid(row=0, column=0, sticky="ew", ipady=8)
    tk.Button(
        routine_name_row,
        text="NEW",
        command=lambda: create_routine(),
        background=colors["pink"],
        activebackground="#FA94C5",
        foreground=colors["window"],
        activeforeground=colors["window"],
        font=("Consolas", 8, "bold"),
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=10,
    ).grid(row=0, column=1, sticky="ns", padx=(7, 0))

    routine_select_row = tk.Frame(routine_panel, background=colors["panel"])
    routine_select_row.grid(row=3, column=0, sticky="ew", padx=18, pady=(9, 0))
    routine_select_row.grid_columnconfigure(0, weight=1)
    current_routine = tk.StringVar()
    routine_selector = ttk.Combobox(
        routine_select_row,
        textvariable=current_routine,
        state="readonly",
        style="Console.TCombobox",
    )
    routine_selector.grid(row=0, column=0, sticky="ew")
    routine_selector.bind("<<ComboboxSelected>>", lambda _event: select_routine())
    tk.Button(
        routine_select_row,
        text="RUN",
        command=lambda: run_selected_routine(),
        background=colors["teal"],
        activebackground="#4BE2BD",
        foreground=colors["window"],
        activeforeground=colors["window"],
        font=("Consolas", 8, "bold"),
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=10,
    ).grid(row=0, column=1, sticky="ns", padx=(7, 0))

    routine_toolbar = tk.Frame(routine_panel, background=colors["panel"])
    routine_toolbar.grid(row=4, column=0, sticky="ew", padx=15, pady=(9, 4))
    for label, callback in (
        ("RENAME", lambda: rename_routine()),
        ("DELETE", lambda: prepare_delete_routine()),
        ("ADD LOADED", lambda: add_loaded_command()),
    ):
        tk.Button(
            routine_toolbar,
            text=label,
            command=callback,
            background=colors["card"],
            activebackground=colors["border"],
            foreground=colors["muted"],
            activeforeground=colors["text"],
            font=("Consolas", 8, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            padx=7,
            pady=5,
        ).pack(side="left", padx=3)

    routine_body = tk.Frame(routine_panel, background=colors["panel"])
    routine_body.grid(row=5, column=0, sticky="nsew", padx=18, pady=(5, 8))
    routine_body.grid_columnconfigure(0, weight=1)
    routine_body.grid_rowconfigure(1, weight=1)
    tk.Label(
        routine_body,
        text="SEQUENCE  //  LEFT TO RIGHT",
        background=colors["panel"],
        foreground=colors["pink"],
        font=("Consolas", 9, "bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", pady=(4, 7))
    routine_lane = tk.Canvas(
        routine_body,
        background=colors["sidebar"],
        highlightbackground=colors["border"],
        highlightthickness=1,
        borderwidth=0,
        height=250,
        cursor="hand2",
    )
    routine_lane.grid(row=1, column=0, sticky="nsew")
    routine_steps = tk.Frame(routine_lane, background=colors["sidebar"])
    routine_steps_window = routine_lane.create_window(
        (10, 10), window=routine_steps, anchor="nw"
    )
    routine_steps.bind(
        "<Configure>",
        lambda _event: routine_lane.configure(scrollregion=routine_lane.bbox("all")),
    )
    routine_lane.bind(
        "<Configure>",
        lambda event: routine_lane.itemconfigure(
            routine_steps_window,
            height=max(event.height - 20, routine_steps.winfo_reqheight()),
        ),
    )
    routine_lane.bind(
        "<MouseWheel>",
        lambda event: routine_lane.xview_scroll(-1 if event.delta > 0 else 1, "units"),
    )

    lane_nav = tk.Frame(routine_body, background=colors["panel"])
    lane_nav.grid(row=2, column=0, sticky="ew", pady=(6, 10))
    tk.Button(
        lane_nav,
        text="<",
        command=lambda: routine_lane.xview_scroll(-3, "units"),
        background=colors["card"], foreground=colors["muted"],
        relief="flat", borderwidth=0, cursor="hand2", padx=12,
    ).pack(side="left")
    tk.Button(
        lane_nav,
        text=">",
        command=lambda: routine_lane.xview_scroll(3, "units"),
        background=colors["card"], foreground=colors["muted"],
        relief="flat", borderwidth=0, cursor="hand2", padx=12,
    ).pack(side="left", padx=(5, 0))
    routine_step_count = tk.StringVar(value="00 STEPS")
    tk.Label(
        lane_nav,
        textvariable=routine_step_count,
        background=colors["panel"],
        foreground=colors["faint"],
        font=("Consolas", 8, "bold"),
    ).pack(side="right")

    tk.Label(
        routine_body,
        text="SELECTED STEP",
        background=colors["panel"],
        foreground=colors["faint"],
        font=("Consolas", 8, "bold"),
        anchor="w",
    ).grid(row=3, column=0, sticky="ew")
    step_editor = tk.Entry(
        routine_body,
        background=colors["card"],
        foreground=colors["text"],
        insertbackground=colors["pink"],
        relief="flat",
        borderwidth=0,
        font=("Consolas", 9),
    )
    step_editor.grid(row=4, column=0, sticky="ew", pady=(5, 7), ipady=8)
    step_controls = tk.Frame(routine_body, background=colors["panel"])
    step_controls.grid(row=5, column=0, sticky="ew")
    for label, callback in (
        ("UPDATE", lambda: update_selected_step()),
        ("REMOVE", lambda: remove_selected_step()),
        ("MOVE <", lambda: move_selected_step(-1)),
        ("MOVE >", lambda: move_selected_step(1)),
    ):
        tk.Button(
            step_controls,
            text=label,
            command=callback,
            background=colors["card"],
            activebackground=colors["border"],
            foreground=colors["muted"],
            activeforeground=colors["text"],
            font=("Consolas", 7, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            padx=5,
            pady=5,
        ).pack(side="left", padx=(0, 4))

    routine_panel_visible = [True]
    selected_step = [-1]
    drag_payload: dict[str, object] = {}

    # Main command console.
    main = tk.Frame(shell, background=colors["window"])
    main.grid(row=0, column=2, sticky="nsew", padx=28, pady=24)
    main.grid_columnconfigure(0, weight=1)
    main.grid_rowconfigure(2, weight=1)

    topbar = tk.Frame(main, background=colors["window"])
    topbar.grid(row=0, column=0, sticky="ew")
    topbar.grid_columnconfigure(0, weight=1)
    heading = tk.Frame(topbar, background=colors["window"])
    heading.grid(row=0, column=0, sticky="w")
    tk.Label(
        heading,
        text="VOICE CONTROL",
        background=colors["window"],
        foreground=colors["text"],
        font=("Segoe UI Semibold", 24),
    ).pack(anchor="w")
    tk.Label(
        heading,
        text="WINDOWS ASSISTANT  /  LOCAL COMMAND CONSOLE",
        background=colors["window"],
        foreground=colors["cyan"],
        font=("Consolas", 9, "bold"),
    ).pack(anchor="w", pady=(2, 0))

    status = tk.StringVar(value="READY")
    status_pill = tk.Label(
        topbar,
        textvariable=status,
        background="#102D2A",
        foreground=colors["teal"],
        font=("Consolas", 9, "bold"),
        padx=13,
        pady=7,
        highlightbackground="#1C5149",
        highlightthickness=1,
    )
    status_pill.grid(row=0, column=1, sticky="ne")

    tk.Label(
        main,
        text="Control Excel, Windows, media, the web, and Discord by voice or keyboard.",
        background=colors["window"],
        foreground=colors["muted"],
        font=("Segoe UI", 10),
        anchor="w",
    ).grid(row=1, column=0, sticky="ew", pady=(14, 12))

    transcript_card = tk.Frame(
        main,
        background=colors["panel"],
        highlightbackground=colors["border"],
        highlightthickness=1,
    )
    transcript_card.grid(row=2, column=0, sticky="nsew")
    transcript_card.grid_rowconfigure(1, weight=1)
    transcript_card.grid_columnconfigure(0, weight=1)
    transcript_header = tk.Frame(transcript_card, background=colors["panel"])
    transcript_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(14, 8))
    tk.Label(
        transcript_header,
        text="SESSION FEED",
        background=colors["panel"],
        foreground=colors["text"],
        font=("Consolas", 10, "bold"),
    ).pack(side="left")
    tk.Label(
        transcript_header,
        text="LIVE",
        background="#102D2A",
        foreground=colors["teal"],
        font=("Consolas", 8, "bold"),
        padx=7,
        pady=2,
    ).pack(side="right")
    transcript = tk.Text(
        transcript_card,
        wrap="word",
        state="disabled",
        background=colors["panel"],
        foreground=colors["text"],
        insertbackground=colors["cyan"],
        selectbackground=colors["cyan"],
        selectforeground=colors["window"],
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 10),
        padx=18,
        pady=8,
        spacing1=4,
        spacing3=8,
    )
    transcript.grid(row=1, column=0, sticky="nsew")
    transcript_scroll = make_dark_scrollbar(
        transcript_card,
        transcript,
        colors["panel"],
    )
    transcript_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 8))
    transcript.tag_configure("You", foreground=colors["cyan"], font=("Consolas", 9, "bold"))
    transcript.tag_configure("Voice", foreground=colors["purple"], font=("Consolas", 9, "bold"))
    transcript.tag_configure("Interpretation", foreground=colors["amber"], font=("Consolas", 9, "bold"))
    transcript.tag_configure("Assistant", foreground=colors["teal"], font=("Consolas", 9, "bold"))

    control_card = tk.Frame(
        main,
        background=colors["panel"],
        highlightbackground=colors["border"],
        highlightthickness=1,
    )
    control_card.grid(row=3, column=0, sticky="ew", pady=(14, 0))
    control_card.grid_columnconfigure(1, weight=1)
    tk.Label(
        control_card,
        text="MIC",
        background=colors["panel"],
        foreground=colors["faint"],
        font=("Consolas", 9, "bold"),
    ).grid(row=0, column=0, sticky="w", padx=(16, 10), pady=(14, 7))
    try:
        devices = transcriber.available_input_devices()
    except (ImportError, RuntimeError, ValueError) as error:
        devices = ()
        status.set("SPEECH UNAVAILABLE")
    default_microphone_label = "System default"
    microphone = tk.StringVar(value=default_microphone_label)
    microphone_picker = ttk.Combobox(
        control_card,
        textvariable=microphone,
        values=(default_microphone_label, *devices),
        state="readonly",
        style="Console.TCombobox",
    )
    microphone_picker.grid(
        row=0, column=1, columnspan=2, sticky="ew", padx=(0, 16), pady=(10, 5)
    )

    command_entry = tk.Entry(
        control_card,
        background=colors["card"],
        foreground=colors["text"],
        insertbackground=colors["cyan"],
        selectbackground=colors["cyan"],
        selectforeground=colors["window"],
        disabledbackground="#101827",
        disabledforeground=colors["faint"],
        relief="flat",
        borderwidth=0,
        font=("Consolas", 11),
    )
    command_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(16, 8), pady=(7, 14), ipady=11)

    speech_results: SimpleQueue[TranscriptionResult | Exception] = SimpleQueue()

    def set_status(message: str, tone: str = "ready") -> None:
        palettes = {
            "ready": ("#102D2A", colors["teal"], "#1C5149"),
            "working": ("#10263B", colors["cyan"], "#1E4E70"),
            "warning": ("#33260D", colors["amber"], "#695018"),
            "error": ("#35151E", colors["danger"], "#672635"),
        }
        background, foreground, border = palettes[tone]
        status.set(message.upper())
        status_pill.configure(
            background=background,
            foreground=foreground,
            highlightbackground=border,
        )

    def append_line(prefix: str, message: str) -> None:
        transcript.configure(state="normal")
        transcript.insert("end", f"{prefix.upper()}  ", prefix)
        transcript.insert("end", f"{message}\n")
        transcript.see("end")
        transcript.configure(state="disabled")

    def execute_command(command: str, source: str) -> None:
        append_line(source, command)
        set_status("Working", "working")
        root.update_idletasks()
        try:
            response = app.handle_text(command)
        except Exception as error:
            response = str(error)
            set_status("Command failed", "error")
        else:
            if response.startswith("[CONFIRMATION REQUIRED]"):
                set_status("Confirmation required", "warning")
            else:
                set_status("Ready")
        append_line("Assistant", response)
        refresh_routine_selector()

    def submit(_event: object | None = None) -> None:
        command = command_entry.get().strip()
        if not command:
            set_status("Enter a command", "warning")
            return
        command_entry.delete(0, "end")
        execute_command(command, "You")

    def capture_speech() -> None:
        selected_device = microphone.get()
        try:
            transcriber.select_input_device(
                selected_device if selected_device in devices else None
            )
        except (ImportError, RuntimeError, ValueError) as error:
            append_line("Assistant", f"Speech input unavailable: {error}")
            set_status("Speech unavailable", "error")
            return

        voice_button.configure(state="disabled", background=colors["faint"])
        command_entry.configure(state="disabled")
        set_status("Listening - speak one command", "working")

        def worker() -> None:
            try:
                speech_results.put(transcriber.transcribe_result("record"))
            except Exception as error:
                speech_results.put(error)

        Thread(target=worker, daemon=True, name="voice-control-speech").start()

    def poll_speech_result() -> None:
        try:
            result = speech_results.get_nowait()
        except Empty:
            root.after(100, poll_speech_result)
            return

        voice_button.configure(state="normal", background=colors["cyan"])
        command_entry.configure(state="normal")
        command_entry.focus_set()
        if isinstance(result, Exception):
            append_line("Assistant", record_speech_failure(app, result))
            set_status("Speech unavailable", "error")
        else:
            set_status("Processing speech", "working")
            root.update_idletasks()
            dispatch = dispatch_transcription(app, result)
            if dispatch.executed:
                append_line("Voice", dispatch.transcript)
                if dispatch.interpreted_text != dispatch.transcript:
                    append_line("Interpretation", dispatch.interpreted_text)
            append_line("Assistant", dispatch.message)
            set_status("Ready")
        root.after(100, poll_speech_result)

    def poll_shutdown_request() -> None:
        if shutdown_requested is not None and shutdown_requested():
            set_status("Stopping safely for USB removal", "warning")
            root.after(50, root.destroy)
            return
        root.after(250, poll_shutdown_request)

    run_button = tk.Button(
        control_card,
        text="RUN  >",
        command=submit,
        background=colors["teal"],
        activebackground="#4BE2BD",
        foreground=colors["window"],
        activeforeground=colors["window"],
        font=("Consolas", 10, "bold"),
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=18,
    )
    run_button.grid(row=1, column=2, sticky="nsew", padx=(0, 8), pady=(7, 14))
    voice_button = tk.Button(
        control_card,
        text="PUSH TO TALK",
        command=capture_speech,
        background=colors["cyan"],
        activebackground="#6ED0FA",
        foreground=colors["window"],
        activeforeground=colors["window"],
        disabledforeground=colors["window"],
        font=("Consolas", 10, "bold"),
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        padx=17,
    )
    voice_button.grid(row=1, column=3, sticky="nsew", padx=(0, 16), pady=(7, 14))

    tk.Label(
        main,
        text="PRIVACY-FIRST  //  RISKY ACTIONS REQUIRE CONFIRMATION  //  DISCORD SENDS REQUIRE YOUR ENTER KEY",
        background=colors["window"],
        foreground=colors["faint"],
        font=("Consolas", 8),
        anchor="w",
    ).grid(row=4, column=0, sticky="ew", pady=(10, 0))

    def load_command(example: str) -> None:
        command_entry.configure(state="normal")
        command_entry.delete(0, "end")
        command_entry.insert(0, example)
        command_entry.focus_set()
        command_entry.selection_range(0, "end")
        set_status("Example loaded", "working")

    def toggle_routine_panel(visible: bool | None = None) -> None:
        show = not routine_panel_visible[0] if visible is None else visible
        if show:
            routine_panel.grid()
            root.geometry("1520x820")
        else:
            routine_panel.grid_remove()
            root.geometry("1180x760")
        routine_panel_visible[0] = show

    def routine_failure(error: Exception | str) -> None:
        message = str(error)
        set_status("Routine needs attention", "error")
        append_line("Assistant", message)

    def refresh_routine_selector(selected_name: str | None = None) -> None:
        routines = app.routines.list()
        names = tuple(routine.name for routine in routines)
        routine_selector.configure(values=names)
        desired = selected_name or current_routine.get()
        if desired not in names:
            desired = names[0] if names else ""
        current_routine.set(desired)
        if desired:
            routine_name.set(desired)
        render_routine_steps()

    def select_routine() -> None:
        selected_step[0] = -1
        routine_name.set(current_routine.get())
        render_routine_steps()

    def create_routine() -> None:
        try:
            routine = app.routines.create(routine_name.get())
        except (RuntimeError, ValueError) as error:
            routine_failure(error)
            return
        refresh_routine_selector(routine.name)
        set_status("Routine created")

    def rename_routine() -> None:
        if not current_routine.get():
            routine_failure("Create or select a routine first.")
            return
        try:
            routine = app.routines.rename(current_routine.get(), routine_name.get())
        except (RuntimeError, ValueError) as error:
            routine_failure(error)
            return
        refresh_routine_selector(routine.name)
        set_status("Routine renamed")

    def prepare_delete_routine() -> None:
        name = current_routine.get()
        if not name:
            routine_failure("Create or select a routine first.")
            return
        load_command(f"delete routine {name}")
        set_status("Delete loaded - run to review", "warning")

    def run_selected_routine() -> None:
        name = current_routine.get()
        if not name:
            routine_failure("Create or select a routine first.")
            return
        execute_command(f"start {name} routine", "Routine")

    def add_loaded_command() -> None:
        command = command_entry.get().strip()
        if not command:
            routine_failure("Load or type a command first.")
            return
        add_command_to_routine(command)

    def add_command_to_routine(command: str, index: int | None = None) -> None:
        name = current_routine.get()
        if not name:
            routine_failure("Create or select a routine before adding commands.")
            return
        try:
            app.routines.add_command(name, command, index=index)
        except (IndexError, RuntimeError, ValueError) as error:
            routine_failure(error)
            return
        render_routine_steps()
        set_status("Routine step added")

    def select_step_at(index: int) -> None:
        routine = app.routines.get(current_routine.get())
        if routine is None or not 0 <= index < len(routine.commands):
            return
        selected_step[0] = index
        step_editor.delete(0, "end")
        step_editor.insert(0, routine.commands[index])
        render_routine_steps()

    def update_selected_step() -> None:
        if selected_step[0] < 0:
            routine_failure("Select a routine step first.")
            return
        try:
            app.routines.update_command(
                current_routine.get(),
                selected_step[0],
                step_editor.get(),
            )
        except (IndexError, RuntimeError, ValueError) as error:
            routine_failure(error)
            return
        render_routine_steps()
        set_status("Routine step updated")

    def remove_selected_step() -> None:
        if selected_step[0] < 0:
            routine_failure("Select a routine step first.")
            return
        try:
            app.routines.remove_command(current_routine.get(), selected_step[0])
        except (IndexError, RuntimeError, ValueError) as error:
            routine_failure(error)
            return
        selected_step[0] = -1
        step_editor.delete(0, "end")
        render_routine_steps()
        set_status("Routine step removed")

    def move_selected_step(delta: int) -> None:
        routine = app.routines.get(current_routine.get())
        index = selected_step[0]
        if routine is None or not 0 <= index < len(routine.commands):
            routine_failure("Select a routine step first.")
            return
        target = max(0, min(len(routine.commands) - 1, index + delta))
        if target == index:
            return
        app.routines.move_command(routine.name, index, target)
        selected_step[0] = target
        render_routine_steps()
        set_status("Routine order updated")

    def begin_step_drag(event: tk.Event[tk.Misc], index: int) -> None:
        drag_payload.clear()
        drag_payload.update(kind="step", index=index, start_x=event.x_root)
        select_step_at(index)

    def finish_step_drag(event: tk.Event[tk.Misc], index: int) -> None:
        if drag_payload.get("kind") != "step":
            return
        source_index = int(drag_payload.get("index", index))
        start_x = int(drag_payload.get("start_x", event.x_root))
        if abs(event.x_root - start_x) < 8:
            drag_payload.clear()
            select_step_at(source_index)
            return
        cards = routine_steps.winfo_children()
        if not cards:
            drag_payload.clear()
            return
        target = min(
            range(len(cards)),
            key=lambda item: abs(
                event.x_root
                - (cards[item].winfo_rootx() + cards[item].winfo_width() // 2)
            ),
        )
        drag_payload.clear()
        app.routines.move_command(current_routine.get(), source_index, target)
        selected_step[0] = target
        render_routine_steps()
        set_status("Routine order updated")

    def render_routine_steps() -> None:
        for child in routine_steps.winfo_children():
            child.destroy()
        routine = app.routines.get(current_routine.get())
        commands = () if routine is None else routine.commands
        routine_step_count.set(f"{len(commands):02d} STEPS")
        if not commands:
            tk.Label(
                routine_steps,
                text="DROP COMMANDS HERE\n\nCreate a routine, then drag command cards\nfrom the left deck into this lane.",
                background=colors["sidebar"],
                foreground=colors["faint"],
                font=("Consolas", 9),
                justify="left",
                anchor="nw",
            ).pack(side="left", anchor="n", padx=10, pady=12)
            routine_lane.configure(scrollregion=routine_lane.bbox("all"))
            return
        for index, command in enumerate(commands):
            selected = index == selected_step[0]
            card = tk.Frame(
                routine_steps,
                width=176,
                height=190,
                background=colors["card_hover"] if selected else colors["card"],
                highlightbackground=colors["pink"] if selected else colors["border"],
                highlightthickness=2 if selected else 1,
                cursor="fleur",
            )
            card.pack(side="left", anchor="n", padx=(0, 9), pady=4)
            card.pack_propagate(False)
            number = tk.Label(
                card,
                text=f"STEP {index + 1:02d}",
                background=card.cget("background"),
                foreground=colors["pink"],
                font=("Consolas", 8, "bold"),
                anchor="w",
            )
            number.pack(fill="x", padx=11, pady=(11, 8))
            phrase = tk.Label(
                card,
                text=command,
                background=card.cget("background"),
                foreground=colors["text"],
                font=("Consolas", 9, "bold"),
                justify="left",
                anchor="nw",
                wraplength=150,
                cursor="fleur",
            )
            phrase.pack(fill="both", expand=True, padx=11, pady=(0, 10))
            for widget in (card, number, phrase):
                widget.bind(
                    "<ButtonPress-1>",
                    lambda event, step=index: begin_step_drag(event, step),
                )
                widget.bind(
                    "<ButtonRelease-1>",
                    lambda event, step=index: finish_step_drag(event, step),
                )
        routine_lane.configure(scrollregion=routine_lane.bbox("all"))

    def begin_command_drag(event: tk.Event[tk.Misc], example: str) -> None:
        drag_payload.clear()
        drag_payload.update(
            kind="command",
            command=example,
            start_x=event.x_root,
            start_y=event.y_root,
        )

    def finish_command_drag(event: tk.Event[tk.Misc], example: str) -> None:
        start_x = int(drag_payload.get("start_x", event.x_root))
        start_y = int(drag_payload.get("start_y", event.y_root))
        moved = abs(event.x_root - start_x) + abs(event.y_root - start_y) >= 8
        lane_left = routine_lane.winfo_rootx()
        lane_top = routine_lane.winfo_rooty()
        over_lane = (
            routine_panel_visible[0]
            and lane_left <= event.x_root <= lane_left + routine_lane.winfo_width()
            and lane_top <= event.y_root <= lane_top + routine_lane.winfo_height()
        )
        drag_payload.clear()
        if moved and over_lane:
            add_command_to_routine(example)
        elif not moved:
            load_command(example)

    def bind_legend_scroll(widget: tk.Misc) -> None:
        widget.bind(
            "<MouseWheel>",
            lambda event: legend_canvas.yview_scroll(
                -1 if event.delta > 0 else 1, "units"
            ),
        )

    def render_legend(*_args: object) -> None:
        for child in legend_content.winfo_children():
            child.destroy()
        sections = filter_command_sections(search_query.get(), active_category.get())
        count = sum(len(section.commands) for section in sections)
        result_summary.set(f"{count:02d} COMMANDS  //  {len(sections):02d} GROUPS")
        if not sections:
            empty = tk.Label(
                legend_content,
                text="NO MATCHING COMMANDS\nTry another word or category.",
                background=colors["sidebar"],
                foreground=colors["muted"],
                font=("Consolas", 9),
                justify="left",
            )
            empty.pack(anchor="w", padx=8, pady=18)
            bind_legend_scroll(empty)
        for section in sections:
            section_label = tk.Label(
                legend_content,
                text=section.name.upper(),
                background=colors["sidebar"],
                foreground=section.accent,
                font=("Consolas", 9, "bold"),
                anchor="w",
            )
            section_label.pack(fill="x", padx=8, pady=(12, 7))
            bind_legend_scroll(section_label)
            for command in section.commands:
                card = tk.Frame(
                    legend_content,
                    background=colors["card"],
                    highlightbackground=colors["border"],
                    highlightthickness=1,
                    cursor="hand2",
                )
                card.pack(fill="x", padx=8, pady=4)
                card.grid_columnconfigure(0, weight=1)
                phrase = tk.Label(
                    card,
                    text=command.phrase,
                    background=colors["card"],
                    foreground=colors["text"],
                    font=("Consolas", 9, "bold"),
                    anchor="w",
                    justify="left",
                    wraplength=255,
                    cursor="hand2",
                )
                phrase.grid(row=0, column=0, sticky="ew", padx=(11, 5), pady=(9, 2))
                card_widgets: list[tk.Misc] = [card, phrase]
                if command.badge:
                    badge_color = (
                        colors["danger"]
                        if command.badge == "BLOCKED"
                        else colors["amber"]
                    )
                    badge = tk.Label(
                        card,
                        text=command.badge,
                        background=colors["card"],
                        foreground=badge_color,
                        font=("Consolas", 7, "bold"),
                    )
                    badge.grid(row=0, column=1, sticky="ne", padx=(2, 9), pady=(10, 0))
                    card_widgets.append(badge)
                phrase.grid_configure(pady=(10, 10))
                for widget in card_widgets:
                    widget.bind(
                        "<ButtonPress-1>",
                        lambda event, example=command.example: begin_command_drag(event, example),
                    )
                    widget.bind(
                        "<ButtonRelease-1>",
                        lambda event, example=command.example: finish_command_drag(event, example),
                    )
                    bind_legend_scroll(widget)
        legend_canvas.yview_moveto(0)

    def choose_category(category: str) -> None:
        active_category.set(category)
        for name, button in category_buttons.items():
            selected = name == category
            button.configure(
                background=colors["cyan"] if selected else colors["card"],
                foreground=colors["window"] if selected else colors["muted"],
            )
        render_legend()

    category_names = ("All", *(section.short_name for section in COMMAND_SECTIONS))
    for index, name in enumerate(category_names):
        button = tk.Button(
            categories,
            text=name.upper(),
            command=lambda selected=name: choose_category(selected),
            background=colors["card"],
            activebackground=colors["cyan"],
            foreground=colors["muted"],
            activeforeground=colors["window"],
            font=("Consolas", 8, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            padx=7,
            pady=5,
        )
        button.grid(
            row=index // 3,
            column=index % 3,
            sticky="ew",
            padx=3,
            pady=3,
        )
        categories.grid_columnconfigure(index % 3, weight=1)
        category_buttons[name] = button

    search_query.trace_add("write", render_legend)
    refresh_routine_selector()
    choose_category("All")
    append_line(
        "Assistant",
        "Console online. Choose a command from the deck, type one below, or push to talk.",
    )
    command_entry.bind("<Return>", submit)
    command_entry.focus_set()
    root.after(100, poll_speech_result)
    root.after(250, poll_shutdown_request)
    root.mainloop()
