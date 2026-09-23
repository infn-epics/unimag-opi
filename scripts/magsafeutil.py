from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
import time
import epik8sutil
import magapply

reload(magapply)

DEFAULT_ZERO_TOLERANCE = 1.0
ZERO_TIMEOUT_S = 20.0
POLL_S = 0.2


def window_id(widget):
    macros = widget.getEffectiveMacros()
    return (macros.getValue("MAGSAFE_ID") or macros.getValue("DID") or
            macros.getValue("SID") or "magsafe")


def safety_tag(widget):
    return widget.getEffectiveMacros().getValue("SAFETY_TAG") or "machine-protection"


def local_name(widget, suffix):
    return "loc://magsafe-" + window_id(widget) + ":" + suffix


def device_local_name(widget, base, field):
    return local_name(widget, base + ":" + field)


def status(widget, message):
    PVUtil.createPV(local_name(widget, "status"), 10).write(message)


def tagged_devices(widget):
    tag = safety_tag(widget)
    devices = epik8sutil.conf_to_dev(widget, "ALL", "ALL", "ALL")
    return [d for d in devices if tag in d.get("TAGS", [])]


def managed_list_name(widget):
    return local_name(widget, "managed-list")


def zero_tolerance(widget):
    try:
        value = PVUtil.getDouble(PVUtil.createPV(local_name(widget, "zero-tolerance"), 10))
        return value if value >= 0 else DEFAULT_ZERO_TOLERANCE
    except Exception:
        return DEFAULT_ZERO_TOLERANCE


def update_safe_status(widget):
    """GREEN only when every managed magnet is set to zero, reads zero and is in STANDBY."""
    try:
        text = PVUtil.getString(PVUtil.createPV(managed_list_name(widget), 10))
        bases = [b for b in text.split("\n") if b]
    except Exception:
        bases = []

    tolerance = zero_tolerance(widget)
    safe = bool(bases)
    unsafe = []
    for base in bases:
        try:
            setpoint = float(PVUtil.createPV(base + ":CURRENT_SP", 100).read().getValue())
            readback = float(PVUtil.createPV(base + ":CURRENT_RB", 100).read().getValue())
            state = str(PVUtil.createPV(base + ":STATE_RB", 100).read().getValue())
            if (abs(setpoint) > tolerance or
                    abs(readback) > tolerance or state != "STANDBY"):
                safe = False
                unsafe.append(base)
        except Exception:
            safe = False
            unsafe.append(base)

    PVUtil.createPV(local_name(widget, "safe"), 10).write(1 if safe else 0)
    PVUtil.createPV(local_name(widget, "unsafe"), 10).write(
        "" if safe else ", ".join(unsafe))
    return safe


def snapshot_devices(widget):
    """Read every device before changing any of them; fail as one transaction."""
    devices = tagged_devices(widget)
    if not devices:
        raise Exception("No magnets tagged '" + safety_tag(widget) + "' were found")

    snapshot = []
    errors = []
    for dev in devices:
        base = dev["P"] + ":" + dev["R"]
        try:
            current = float(PVUtil.createPV(base + ":CURRENT_SP", 500).read().getValue())
            state = str(PVUtil.createPV(base + ":STATE_RB", 500).read().getValue())
            snapshot.append({"name": dev["R"], "prefix": dev["P"], "base": base,
                             "current": current, "state": state})
        except Exception as e:
            errors.append(base + ": " + str(e))
    if errors:
        raise Exception("Snapshot aborted; no magnets were changed.\n" + "\n".join(errors))
    return snapshot


def save_file(filename, snapshot):
    with open(filename, "w") as f:
        f.write("Name,Prefix,Current,State\n")
        for d in snapshot:
            f.write(d["name"] + "," + d["prefix"] + "," + str(d["current"]) + "," + d["state"] + "\n")


def save_local(widget, filename, snapshot):
    bases = []
    for d in snapshot:
        PVUtil.createPV(device_local_name(widget, d["base"], "SP"), 10).write(d["current"])
        PVUtil.createPV(device_local_name(widget, d["base"], "STATE"), 10).write(d["state"])
        bases.append(d["base"])
    PVUtil.createPV(local_name(widget, "snapshot-list"), 10).write("\n".join(bases))
    PVUtil.createPV(local_name(widget, "snapshot-file"), 10).write(filename)
    PVUtil.createPV(local_name(widget, "snapshot-valid"), 10).write(1)


def enter_standby(widget, snapshot):
    """Zero all setpoints, wait as a group, then command STANDBY for every device."""
    result = {"zeroed": [], "zero_timeout": [], "standby": [], "errors": []}
    pvcache = {}

    def pv(name):
        if name not in pvcache:
            pvcache[name] = PVUtil.createPV(name, 500)
        return pvcache[name]

    tolerance = zero_tolerance(widget)
    active = []
    for d in snapshot:
        try:
            pv(d["base"] + ":CURRENT_SP").write(0.0)
            active.append(d)
        except Exception as e:
            result["errors"].append(d["base"] + " zero: " + str(e))

    waiting = list(active)
    deadline = time.time() + ZERO_TIMEOUT_S
    while waiting and time.time() < deadline:
        time.sleep(POLL_S)
        still = []
        for d in waiting:
            try:
                if abs(float(pv(d["base"] + ":CURRENT_RB").read().getValue())) > tolerance:
                    still.append(d)
                elif d["base"] not in result["zeroed"]:
                    result["zeroed"].append(d["base"])
            except Exception as e:
                result["errors"].append(d["base"] + " readback: " + str(e))
        waiting = still

    result["zero_timeout"] = [d["base"] for d in waiting]

    # Hard safety invariant: never command STANDBY until zero current is confirmed.
    zeroed = set(result["zeroed"])
    for d in active:
        if d["base"] not in zeroed:
            continue
        try:
            pv(d["base"] + ":STATE_SP").write("STANDBY")
            result["standby"].append(d["base"])
        except Exception as e:
            result["errors"].append(d["base"] + " standby: " + str(e))
    update_safe_status(widget)
    return result


def standby_summary(result, total):
    msg = ("Standby commanded for " + str(len(result["standby"])) + " of " +
           str(total) + " tagged magnets.")
    if result["zero_timeout"]:
        msg += ("\n\nERROR: zero readback was not reached within " +
                str(int(ZERO_TIMEOUT_S)) + " s; STANDBY was NOT commanded for:\n" +
                ", ".join(result["zero_timeout"]))
    if result["errors"]:
        msg += "\n\nErrors:\n" + "\n".join(result["errors"])
    return msg


def local_snapshot(widget):
    valid = PVUtil.getLong(PVUtil.createPV(local_name(widget, "snapshot-valid"), 10))
    if valid != 1:
        return []
    text = PVUtil.getString(PVUtil.createPV(local_name(widget, "snapshot-list"), 10))
    snapshot = []
    for base in [b for b in text.split("\n") if b]:
        current = PVUtil.getDouble(PVUtil.createPV(device_local_name(widget, base, "SP"), 10))
        state = PVUtil.getString(PVUtil.createPV(device_local_name(widget, base, "STATE"), 10))
        if state not in magapply.RESTORABLE_STATES:
            state = "ON"
        snapshot.append({"base": base, "current": current, "state": state})
    return snapshot


def resume(widget):
    snapshot = local_snapshot(widget)
    if not snapshot:
        ScriptUtil.showMessageDialog(widget,
            "No local MagSafe snapshot is available. Use Resume from File instead.")
        return
    if not ScriptUtil.showConfirmationDialog(widget,
            "Resume the saved setpoints and states of " + str(len(snapshot)) + " tagged magnets?"):
        return
    status(widget, "Resuming " + str(len(snapshot)) + " tagged magnets...")
    result = magapply.apply(snapshot, zero_tolerance(widget))
    update_safe_status(widget)
    message = "MagSafe resume complete. " + magapply.summary(result, len(snapshot))
    status(widget, message.replace("\n", "  "))
    ScriptUtil.showMessageDialog(widget, message)
