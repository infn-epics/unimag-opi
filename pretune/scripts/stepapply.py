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


def _settings(did):
    tolerance = PVUtil.getDouble(PVUtil.createPV("loc://tolerance_" + did, 10))
    return {"tolerance": tolerance,
            "timeout": magapply.read_timeout("loc://timeout_" + did),
            "zero_tolerance": magapply.read_zero_tolerance("loc://zerotol_" + did)}


def run(widget, field, counter_delta=0, retry=False):
    """counter_delta: moved on the step counter (the widget's primary PV) once applied.
    retry: redo only the rows that did not reach their target, re-sending the current."""
    did = pretuneutil.window_id(widget)
    devices = selected_devices(did, field)
    result = magapply.apply(devices, retry=retry, force_current=True, **_settings(did))

    text = magapply.summary(result, len(devices))
    print(text)
    if magapply.incomplete(result):
        ScriptUtil.showMessageDialog(widget, text)

    if counter_delta:
        pv = ScriptUtil.getPrimaryPV(widget)
        pv.write(PVUtil.getLong(pv) + counter_delta)


def set_states(widget):
    """"Set Selected States": states only (ON -> OFF still brings the current to 0 first).
    Rows without a state to restore are left alone."""
    did = pretuneutil.window_id(widget)
    devices = selected_devices(did, None)
    result = magapply.apply(devices, set_current=False, **_settings(did))

    text = magapply.summary(result, len(devices))
    print(text)
    if magapply.incomplete(result):
        ScriptUtil.showMessageDialog(widget, text)
