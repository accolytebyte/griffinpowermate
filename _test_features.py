"""Tests for new features: macro action, debug panel, startup module."""
import sys, time, threading, traceback

fails = []
def check(name, fn):
    print(f"... {name}", flush=True)
    try:
        fn(); print(f"[PASS] {name}", flush=True)
    except Exception as e:
        fails.append(name); print(f"[FAIL] {name}: {e}"); traceback.print_exc()

def watchdog():
    time.sleep(30); print("[WATCHDOG] timeout"); import os; os._exit(3)
threading.Thread(target=watchdog, daemon=True).start()


def test_startup_module():
    import startup
    assert isinstance(startup.is_enabled(), bool)
    cmd = startup._launch_command()
    assert isinstance(cmd, str) and len(cmd) > 0, cmd
    print("    launch command:", cmd)


def test_macro_action_executor():
    # Ensure the executor handles a macro config without error (empty + populated).
    from actions import ActionExecutor
    from audio import AudioController
    ex = ActionExecutor(AudioController())
    ex.execute({"action": "macro", "sequence": []})        # no-op, must not raise
    # Don't actually send keys in CI-ish run; just confirm dispatch path exists.
    assert hasattr(ex, "_macro")


def test_macro_editor_roundtrip():
    import customtkinter as ctk
    from ui.action_editor import ActionEditor
    root = ctk.CTk(); root.withdraw()
    ed = ActionEditor(root, "triple_press"); ed.create()
    # Load a macro and read it back.
    ed.load({"action": "macro", "sequence": ["ctrl+c", "alt+tab", "ctrl+v"]})
    assert ed.current_action == "macro", ed.current_action
    out = ed.get_action()
    assert out["action"] == "macro", out
    assert out["sequence"] == ["ctrl+c", "alt+tab", "ctrl+v"], out["sequence"]
    # 'key' action still works.
    ed.load({"action": "key", "keys": "f5"})
    assert ed.get_action() == {"action": "key", "keys": "f5"}, ed.get_action()
    root.destroy()


def test_triple_and_long_bindable_and_debug_panel():
    from config import Config
    from ui.app_window import AppWindow
    cfg = Config("config.features_test.json")
    aw = AppWindow(cfg, on_config_change=lambda: None, on_quit=lambda: None)
    root = aw.create(); root.update()
    # All 8 triggers present, including triple_press and long_press.
    trig = set(aw.profile_view.action_editors.keys())
    assert {"triple_press", "long_press"} <= trig, trig
    # Bind a macro to long_press and a key to triple_press, save, verify in config.
    aw.profile_view.action_editors["long_press"].load(
        {"action": "macro", "sequence": ["win+d", "ctrl+a"]})
    aw.profile_view.action_editors["triple_press"].load(
        {"action": "key", "keys": "ctrl+shift+n"})
    aw.profile_view.save()
    raw = cfg.get_profile_raw("default")
    assert raw["long_press"]["action"] == "macro", raw.get("long_press")
    assert raw["long_press"]["sequence"] == ["win+d", "ctrl+a"], raw["long_press"]
    assert raw["triple_press"] == {"action": "key", "keys": "ctrl+shift+n"}, raw["triple_press"]
    # Debug panel accepts events.
    aw.log_event("rotate_right +1 -> volume_up"); root.update()
    assert aw.debug_box is not None
    root.destroy()
    import os
    os.remove("config.features_test.json")


for n, f in list(globals().items()):
    if n.startswith("test_") and callable(f):
        check(n, f)

print("\n" + ("ALL FEATURE TESTS PASSED" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
