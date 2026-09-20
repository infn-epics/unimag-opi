from org.csstudio.display.builder.runtime.script import PVUtil, ScriptUtil
import magapply
import pretuneutil
reload(magapply)  # pick up edits without restarting Phoebus
reload(pretuneutil)

# Shared by StepUp.py, StepDown.py, RetryStep.py and SetStates.py: pushes the selected rows of the
# pretune display to the hardware, STATE first (waiting for it to be reached), then CURRENT,
# see magapply.apply. Only the rows loaded in this window are considered.


def selected_devices(did, field):
    """Every checked row, with the current found in the local PV `field`
    (CURRENT_NEXT_SP, CURRENT_PREV_SP or CURRENT_SET_SP) and its desired state."""
    devices = []
    for base in pretuneutil.bases(did):
        def local(f):
            return PVUtil.createPV(pretuneutil.local_name(did, base, f), 10)
        try:
            if PVUtil.getLong(local("enabled")) == 0:
                print("SKIP " + base + " (deselected)")
                continue
            devices.append({"base": base,
                            "current": PVUtil.getDouble(local(field)) if field else 0.0,
                            "state": PVUtil.getString(local("STATE_SP"))})
        except Exception as e:
            print("## Error reading " + base + ": " + str(e))
    return devices


def run(widget, field, counter_delta=0, retry=False):
    """counter_delta: moved on the step counter (the widget's primary PV) once applied.
    retry: redo only the rows that did not reach their target, re-sending the current."""
    did = pretuneutil.window_id(widget)
    tolerance = PVUtil.getDouble(PVUtil.createPV("loc://tolerance_" + did, 10))

    devices = selected_devices(did, field)
    result = magapply.apply(devices, tolerance, retry=retry, force_current=True)

    text = magapply.summary(result, len(devices))
    print(text)
    if result["state_timeout"] or result["errors"]:
        ScriptUtil.showMessageDialog(widget, text)

    if counter_delta:
        pv = ScriptUtil.getPrimaryPV(widget)
        pv.write(PVUtil.getLong(pv) + counter_delta)


def set_states(widget):
    """"Set Selected States": states only. Rows without a state to restore are left alone."""
    did = pretuneutil.window_id(widget)
    for d in selected_devices(did, None):
        if d["state"] not in magapply.RESTORABLE_STATES:
            print("SKIP " + d["base"] + " (no state to restore)")
            continue
        try:
            PVUtil.createPV(d["base"] + ":STATE_SP", 100).write(d["state"])
            print("APPLY " + d["base"] + ":STATE_SP = " + d["state"])
        except Exception as e:
            print("## Error applying state for " + d["base"] + ": " + str(e))
