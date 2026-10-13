"""Mechanical dialogue controls grounded in unchanged authored source prose."""


def source_dialogue_controls(dialogue, prompt, output):
    if dialogue is None or dialogue.mode != "dialogue":
        return ()
    if not output.native_audio:
        raise ValueError("source dialogue requires native audio output")
    if dialogue.end_seconds is not None and dialogue.end_seconds > output.duration_seconds:
        raise ValueError("source dialogue window exceeds bound output duration")
    if (dialogue.language not in {"zh", "zh-CN"} or not dialogue.verbatim_text
            or dialogue.verbatim_text not in prompt
            or not any("\u4e00" <= char <= "\u9fff" for char in dialogue.verbatim_text)):
        return ()
    prefix = "generation_intent.dialogue_intent."
    controls = (prefix + "mode", prefix + "language")
    if dialogue.start_seconds is None or dialogue.end_seconds is None:
        return controls

    def seconds(value):
        return str(int(value)) if value.is_integer() else str(value)

    screen = {True: "画内；", False: "画外；", None: ""}[dialogue.on_screen]
    lip = "口型与对白同步" if dialogue.lip_sync_required else "不要求口型同步"
    declaration = (f"原生对白约束：普通话；[{seconds(dialogue.start_seconds)}–"
                   f"{seconds(dialogue.end_seconds)}s]“{dialogue.verbatim_text}”；{screen}{lip}。")
    if declaration not in prompt.splitlines():
        return controls
    controls += (prefix + "start_seconds", prefix + "end_seconds", prefix + "lip_sync_required")
    if dialogue.on_screen is not None:
        controls += (prefix + "on_screen",)
    return controls
