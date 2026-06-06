"""Headless-ish smoke test: build the GUI, exercise it, then close.

Run: python _smoketest_gui.py
Exits 0 on success, non-zero on any exception during construction/interaction.
"""
import sys
import traceback

results = []

def check(name, fn):
    print(f"... {name}", flush=True)
    try:
        fn()
        results.append((name, True, ""))
        print(f"[PASS] {name}", flush=True)
    except Exception as e:
        results.append((name, False, f"{e}\n{traceback.format_exc()}"))
        print(f"[FAIL] {name}: {e}", flush=True)


def _watchdog():
    import time, os
    time.sleep(30)
    print("[WATCHDOG] timeout — forcing exit", flush=True)
    os._exit(3)


def main():
    import threading
    threading.Thread(target=_watchdog, daemon=True).start()

    from config import Config
    from ui.app_window import AppWindow

    # Use a temp config file so we don't clobber the real one.
    cfg = Config("config.smoketest.json")

    win_holder = {}

    def build():
        aw = AppWindow(cfg, on_config_change=lambda: None)
        root = aw.create()
        win_holder["aw"] = aw
        win_holder["root"] = root

    check("build_window", build)

    aw = win_holder.get("aw")
    root = win_holder.get("root")

    if aw and root:
        # Pump events so widgets realize/layout.
        check("update_idletasks", lambda: root.update())

        # Exercise: default profile must be auto-selected and load 8 trigger rows.
        def check_bindings_loaded():
            assert aw.selected_profile == "default", aw.selected_profile
            n = len(aw.profile_view.action_editors)
            assert n == 8, f"expected 8 trigger editors, got {n}"
            # The default 'press' binding should have loaded as 'mute'.
            ed = aw.profile_view.action_editors["press"]
            assert ed.current_action == "mute", f"press action = {ed.current_action}"
        check("bindings_loaded", check_bindings_loaded)

        # Exercise: round-trip a binding edit through save -> raw config.
        def check_save_roundtrip():
            ed = aw.profile_view.action_editors["rotate_right"]
            # rotate_right default is volume_up; verify it loaded and saves back.
            assert ed.current_action == "volume_up", ed.current_action
            aw.profile_view.save()
            raw = cfg.get_profile_raw("default")
            assert raw["rotate_right"]["action"] == "volume_up", raw.get("rotate_right")
        check("save_roundtrip", check_save_roundtrip)

        # Exercise: LED + timing tabs populated their widgets (proves self.pack ran).
        def check_panels():
            assert "mode" in aw.led_panel.widgets
            assert "multi_click_ms" in aw.timing_panel.widgets
            # reload() uses "end" index — would raise if ctk.END bug remained.
            aw.led_panel.reload()
            aw.timing_panel.reload()
        check("panels_populated", check_panels)

        # Exercise: inheritance — add an app profile overriding only rotate_right.
        def check_inheritance():
            cfg.add_profile("notepad.exe")
            cfg.config["profiles"]["notepad.exe"] = {
                "rotate_right": {"action": "scroll_down", "amount": 5}
            }
            eff = cfg.get_profile("notepad.exe")
            assert eff["rotate_right"]["action"] == "scroll_down", eff["rotate_right"]
            # press not overridden -> inherited from default (mute)
            assert eff["press"]["action"] == "mute", eff.get("press")
        check("profile_inheritance", check_inheritance)

        # Thread-safe status update (schedules via after()).
        check("set_status", lambda: aw.set_status("Test", "green"))
        check("pump_after", lambda: root.update())

        # Tear down.
        check("destroy", lambda: root.destroy())

    # Report
    print("\n=== GUI SMOKE TEST RESULTS ===")
    ok = True
    for name, passed, err in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if not passed:
            ok = False
            print("   " + err.replace("\n", "\n   "))
    print("==============================")
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
