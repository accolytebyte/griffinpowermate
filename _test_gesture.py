"""Unit tests for the gesture state machine (no hardware needed)."""
import time
from gesture import GestureDetector, GestureConfig, Trigger

fails = []

def run(name, fn):
    try:
        fn()
        print(f"[PASS] {name}")
    except AssertionError as e:
        fails.append(name)
        print(f"[FAIL] {name}: {e}")


def make(multi=120, long=300):
    events = []
    cfg = GestureConfig(multi_click_ms=multi, long_press_ms=long)
    g = GestureDetector(lambda t, a: events.append((t, a)), cfg)
    return g, events


def test_rotate_right():
    g, ev = make()
    g.on_knob(1)
    assert ev == [(Trigger.ROTATE_RIGHT, 1)], ev

def test_rotate_left():
    g, ev = make()
    g.on_knob(-1)
    assert ev == [(Trigger.ROTATE_LEFT, 1)], ev

def test_single_press():
    g, ev = make(multi=80)
    g.on_button(True); g.on_button(False)
    g.update()  # too soon
    assert ev == [], f"fired too early: {ev}"
    time.sleep(0.12)
    g.update()
    assert ev == [(Trigger.PRESS, 0)], ev

def test_double_press():
    g, ev = make(multi=100)
    g.on_button(True); g.on_button(False)
    g.on_button(True); g.on_button(False)
    time.sleep(0.13)
    g.update()
    assert ev == [(Trigger.DOUBLE_PRESS, 0)], ev

def test_triple_press():
    g, ev = make(multi=100)
    for _ in range(3):
        g.on_button(True); g.on_button(False)
    time.sleep(0.13)
    g.update()
    assert ev == [(Trigger.TRIPLE_PRESS, 0)], ev

def test_long_press():
    g, ev = make(long=100)
    g.on_button(True)
    time.sleep(0.13)
    g.update()
    assert ev == [(Trigger.LONG_PRESS, 0)], ev
    # Release should NOT produce a spurious single press.
    g.on_button(False)
    time.sleep(0.13)
    g.update()
    assert ev == [(Trigger.LONG_PRESS, 0)], f"spurious event after long press: {ev}"

def test_press_rotate_right():
    g, ev = make()
    g.on_button(True)
    g.on_knob(1)
    assert ev == [(Trigger.PRESS_ROTATE_RIGHT, 1)], ev

def test_press_rotate_no_spurious_press():
    # The key regression: rotating while held must NOT also fire a single press.
    g, ev = make(multi=80, long=300)
    g.on_button(True)
    g.on_knob(1)          # press+rotate
    g.on_button(False)    # release
    time.sleep(0.12)
    g.update()
    assert ev == [(Trigger.PRESS_ROTATE_RIGHT, 1)], f"spurious press: {ev}"

def test_long_press_not_fired_while_rotating():
    # Holding and rotating past long_press_ms should not trigger long_press.
    g, ev = make(long=100)
    g.on_button(True)
    g.on_knob(1)          # now pressed_and_rotating
    time.sleep(0.13)
    g.update()
    assert all(t != Trigger.LONG_PRESS for t, _ in ev), f"unexpected long press: {ev}"


for n, f in list(globals().items()):
    if n.startswith("test_") and callable(f):
        run(n, f)

print("\n" + ("ALL GESTURE TESTS PASSED" if not fails else f"FAILURES: {fails}"))
raise SystemExit(1 if fails else 0)
