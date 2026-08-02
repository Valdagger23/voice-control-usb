"""Small native Windows shell for the typed Excel vertical slice."""

from __future__ import annotations

from voice_control_usb.assistant.app import AssistantApp


def run_windows_shell(app: AssistantApp) -> None:
    """Run a visible typed-command window against the shared assistant pipeline."""

    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Voice Control Assistant")
    root.geometry("760x520")
    root.minsize(620, 400)

    frame = ttk.Frame(root, padding=18)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Windows Assistant", font=("Segoe UI", 18, "bold")).pack(
        anchor="w"
    )
    ttk.Label(
        frame,
        text="Basic Excel control — type a supported command below.",
    ).pack(anchor="w", pady=(2, 14))

    status = tk.StringVar(value="Ready")
    ttk.Label(frame, textvariable=status).pack(anchor="w", pady=(0, 8))

    transcript = tk.Text(frame, height=16, wrap="word", state="disabled")
    transcript.pack(fill="both", expand=True)

    command_row = ttk.Frame(frame)
    command_row.pack(fill="x", pady=(12, 0))
    command_entry = ttk.Entry(command_row)
    command_entry.pack(side="left", fill="x", expand=True)

    def append_line(prefix: str, message: str) -> None:
        transcript.configure(state="normal")
        transcript.insert("end", f"{prefix}: {message}\n")
        transcript.see("end")
        transcript.configure(state="disabled")

    def submit(_event: object | None = None) -> None:
        command = command_entry.get().strip()
        if not command:
            status.set("Enter a command first")
            return
        command_entry.delete(0, "end")
        append_line("You", command)
        status.set("Working…")
        root.update_idletasks()
        try:
            response = app.handle_text(command)
        except Exception as error:
            response = str(error)
            status.set("Could not complete command")
        else:
            status.set("Ready")
        append_line("Assistant", response)

    run_button = ttk.Button(command_row, text="Run", command=submit)
    run_button.pack(side="left", padx=(8, 0))

    ttk.Label(
        frame,
        text=(
            "Examples: open excel · go to A1 · enter 42 · report current cell · "
            "undo last change"
        ),
    ).pack(anchor="w", pady=(10, 0))

    command_entry.bind("<Return>", submit)
    command_entry.focus_set()
    root.mainloop()
