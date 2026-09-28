from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
import re
import epik8sutil
import magapply
reload(magapply)  # pick up edits without restarting Phoebus

# Shared by the restore scripts.
#
# Every local PV of a restore window is named  loc://restore-<DID>:<P>:<R>:<FIELD>
# (DID keeps windows independent, so a closed and re-opened display never sees stale values).
# The list of devices currently shown is kept in loc://restore-list-<DID> as one "P:R" per line.

# States that can be commanded via STATE_SP, anything else (INTERLOCK, FAULT ...) is skipped
RESTORABLE_STATES = magapply.RESTORABLE_STATES

# StateCode column of a dataset file -> desired STATE_SP
DAT_STATE_CODES = {"1": "OFF", "2": "ON"}


def window_id(widget, pv=None):
    """$(DID) of this window. Inside scripts getEffectiveMacros() does not reliably provide DID
    (see Scripts/SelectionAll.py), while $(DID) is always resolved in a PV name: so it is taken
    from `pv` (a script trigger PV) or from the widget's own pv_name, both named ...-$(DID) or
    ..._$(DID). Every script of the window must agree with the PV names used in the .bob files."""
    if pv is None:
        try:
            pv = ScriptUtil.getPrimaryPV(widget)
        except Exception:
            pv = None
    if pv is not None:
        name = pv.getName().split("<")[0].split("(")[0]
        did = re.split("[-_]", name)[-1]
        if did and "$" not in did:
            return did
    did = widget.getEffectiveMacros().getValue("DID")
    if did:
        return did
    print("## Cannot determine the window id (DID): local PVs will not match the display")
    return "0"


def local_name(did, base, field):
    return "loc://restore-" + did + ":" + base + ":" + field


def list_name(did):
    return "loc://restore-list-" + did


def status_name(did):
    return "loc://restore-status-" + did


def tolerance_name(did):
    return "loc://restore-tol-" + did


def timeout_name(did):
    return "loc://restore-timeout-" + did


def zero_tolerance_name(did):
    return "loc://restore-zerotol-" + did


def read_csv(filename):
    """*.csv, header "Name,Prefix,Current,State" (written by SaveDynamic.py).
    Returns (devices, unknown)."""
    with open(filename, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    if not lines:
        return [], []
    header = [h.strip() for h in lines[0].split(",")]
    devices = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        devices.append(dict(zip(header, parts)))
    return devices, []


def read_dat(filename, widget):
    """Plain-text dataset, whitespace separated, no header:  [index] Name Current Pol StateCode
    (e.g. BTF_RUN.dat, same syntax and conventions as pretune/scripts/LoadPretuneDataSet.py).
    Returns (devices, unknown): devices use the same keys as the CSV rows, unknown lists the
    names that could not be mapped to a PV prefix."""
    default_prefix = widget.getEffectiveMacros().getValue("P")

    # Real PV base (prefix:root) of every configured device, from the YAML configuration
    by_name = {}
    confdevs = epik8sutil.conf_to_dev(widget, "ALL", "ALL", "ALL")
    for dev in confdevs:
        by_name[dev['R']] = (dev['P'], dev['R'])
    for dev in confdevs:
        by_name.setdefault(dev['NAME'], (dev['P'], dev['R']))

    devices = []
    unknown = []
    with open(filename, "r") as f:
        for line in f:
            if "#" in line:
                continue
            parts = line.split()
            if len(parts) == 5:
                _, identifier, value, pol, statecode = parts
            elif len(parts) == 4:
                identifier, value, pol, statecode = parts
            else:
                continue

            try:
                current = float(value)
            except ValueError:
                unknown.append(identifier + " (bad value \"" + value + "\")")
                continue
            ## '*' and '+' : value as given (its own sign, if any); '-' : sign inverted
            if pol == "-":
                current = -current

            if identifier in by_name:
                prefix, root = by_name[identifier]
            elif default_prefix:
                prefix, root = default_prefix, identifier
            else:
                unknown.append(identifier + " (not in configuration)")
                continue

            devices.append({"Name": root, "Prefix": prefix,
                            "Current": str(current),
                            "State": DAT_STATE_CODES.get(statecode, "")})
    return devices, unknown


def read_file(filename, widget):
    if filename.lower().endswith(".csv"):
        return read_csv(filename)
    return read_dat(filename, widget)


def selected_devices(widget):
    """The checked rows, with the (possibly edited) restore set and desired state."""
    did = window_id(widget)
    try:
        bases = [b for b in PVUtil.getString(PVUtil.createPV(list_name(did), 10)).split("\n") if b]
    except Exception:
        bases = []

    devices = []
    for base in bases:
        def local(field):
            return PVUtil.createPV(local_name(did, base, field), 10)
        if PVUtil.getLong(local("enabled")) == 0:
            continue
        devices.append({"base": base,
                        "current": PVUtil.getDouble(local("SP")),
                        "state": PVUtil.getString(local("STATE_SP"))})
    return devices


def run(widget, retry):
    """Restore Selected (retry=False), or redo the checked rows that have not reached their
    restore set yet (retry=True). State first, then current: see magapply.apply."""
    devices = selected_devices(widget)
    if not devices:
        ScriptUtil.showMessageDialog(widget, "No power supply selected: load a file and check at least one row.")
        return

    if not retry and not ScriptUtil.showConfirmationDialog(widget, "Restore " + str(len(devices)) + " power supplies?"):
        return

    did = window_id(widget)
    tolerance = PVUtil.getDouble(PVUtil.createPV(tolerance_name(did), 10))
    timeout = magapply.read_timeout(timeout_name(did))
    zero_tolerance = magapply.read_zero_tolerance(zero_tolerance_name(did))
    PVUtil.createPV(status_name(did), 10).write(
        ("Retry" if retry else "Restore") + " running: DID=" + did + " tolerance=" + str(tolerance) +
        " zero tol.=" + str(zero_tolerance) + " timeout=" + str(timeout) + " s")
    result = magapply.apply(devices, tolerance, retry=retry, force_current=retry, timeout=timeout,
                            zero_tolerance=zero_tolerance)
    prefix = "Retry complete. " if retry else "Restore complete. "
    ScriptUtil.showMessageDialog(widget, prefix + magapply.summary(result, len(devices)))
