"""Small native Windows shell for typed and controlled speech input."""

from __future__ import annotations

from queue import Empty, SimpleQueue
from threading import Thread

from voice_control_usb.assistant.app import AssistantApp
from voice_control_usb.assistant.speech_flow import (
    dispatch_transcription,
    record_speech_failure,
)
from voice_control_usb.audio.transcriber import (
    SpeechTranscriber,
    TranscriptionResult,
)


def run_windows_shell(app: AssistantApp, transcriber: SpeechTranscriber) -> None:
    """Run a visible typed and push-to-talk window against the shared pipeline."""

    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Voice Control Assistant")
    root.geometry("780x580")
    root.minsize(640, 460)

    frame = ttk.Frame(root, padding=18)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Windows Assistant", font=("Segoe UI", 18, "bold")).pack(
        anchor="w"
    )
    ttk.Label(
        frame,
        text="Excel, media, browser, and Discord - type or push to talk.",
    ).pack(anchor="w", pady=(2, 14))

    status = tk.StringVar(value="Ready")
    ttk.Label(frame, textvariable=status).pack(anchor="w", pady=(0, 8))

    transcript = tk.Text(frame, height=16, wrap="word", state="disabled")
    transcript.pack(fill="both", expand=True)

    microphone_row = ttk.Frame(frame)
    microphone_row.pack(fill="x", pady=(12, 0))
    ttk.Label(microphone_row, text="Microphone:").pack(side="left")
    try:
        devices = transcriber.available_input_devices()
    except (ImportError, RuntimeError, ValueError) as error:
        devices = ()
        status.set(f"Speech unavailable: {error}")
    default_microphone_label = "System default"
    microphone = tk.StringVar(value=default_microphone_label)
    microphone_picker = ttk.Combobox(
        microphone_row,
        textvariable=microphone,
        values=(default_microphone_label, *devices),
        state="readonly",
        width=55,
    )
    microphone_picker.pack(side="left", fill="x", expand=True, padx=(8, 0))

    command_row = ttk.Frame(frame)
    command_row.pack(fill="x", pady=(10, 0))
    command_entry = ttk.Entry(command_row)
    command_entry.pack(side="left", fill="x", expand=True)

    speech_results: SimpleQueue[TranscriptionResult | Exception] = SimpleQueue()

    def append_line(prefix: str, message: str) -> None:
        transcript.configure(state="normal")
        transcript.insert("end", f"{prefix}: {message}\n")
        transcript.see("end")
        transcript.configure(state="disabled")

    def execute_command(command: str, source: str) -> None:
        append_line(source, command)
        status.set("Working...")
        root.update_idletasks()
        try:
            response = app.handle_text(command)
        except Exception as error:
            response = str(error)
            status.set("Could not complete command")
        else:
            status.set("Ready")
        append_line("Assistant", response)

    def submit(_event: object | None = None) -> None:
        command = command_entry.get().strip()
        if not command:
            status.set("Enter a command first")
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
            status.set("Speech unavailable")
            return

        voice_button.configure(state="disabled")
        command_entry.configure(state="disabled")
        status.set("Listening... speak one command")

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

        voice_button.configure(state="normal")
        command_entry.configure(state="normal")
        command_entry.focus_set()
        if isinstance(result, Exception):
            append_line("Assistant", record_speech_failure(app, result))
            status.set("Speech unavailable")
        else:
            status.set("Processing speech...")
            root.update_idletasks()
            dispatch = dispatch_transcription(app, result)
            if dispatch.executed:
                append_line("Voice", dispatch.transcript)
                if dispatch.interpreted_text != dispatch.transcript:
                    append_line("Interpretation", dispatch.interpreted_text)
            append_line("Assistant", dispatch.message)
            status.set("Ready")
        root.after(100, poll_speech_result)

    run_button = ttk.Button(command_row, text="Run", command=submit)
    run_button.pack(side="left", padx=(8, 0))
    voice_button = ttk.Button(command_row, text="Push to talk", command=capture_speech)
    voice_button.pack(side="left", padx=(8, 0))

    ttk.Label(
        frame,
        text=(
            "Examples: open excel | go to A1 | enter 42 | report current cell | "
            "undo last change"
        ),
    ).pack(anchor="w", pady=(10, 0))

    command_entry.bind("<Return>", submit)
    command_entry.focus_set()
    root.after(100, poll_speech_result)
    root.mainloop()
