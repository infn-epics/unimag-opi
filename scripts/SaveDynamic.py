from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from org.phoebus.pv import PVPool
import time

def _get_pv_refs():
    for _ in range(10):
        try:
            return list(PVPool.getPVReferences())
        except Exception:
            time.sleep(0.05)
    return []

filename = ScriptUtil.showSaveAsDialog(widget, "mag_snapshot.csv")
if filename is not None:
    if not filename.endswith(".csv"):
        filename = filename + ".csv"

    lpvs = _get_pv_refs()
    rows = []
    errors = []

    for pvr in lpvs:
        entry = pvr.getEntry()
        name = entry.getName()
        if not name.startswith("loc://selection:"):
            continue
        # Only save selected devices
        try:
            if entry.read().getValue() != 1:
                continue
        except Exception:
            continue

        pv_prefix = name.replace("loc://selection:", "")
        if "<" in pv_prefix:
            pv_prefix = pv_prefix[:pv_prefix.index("<")]
        prefix, identifier = pv_prefix.rsplit(":", 1)
        try:
            pv_cur = PVUtil.createPV(pv_prefix + ":CURRENT_SP", 500)
            pv_st  = PVUtil.createPV(pv_prefix + ":STATE_RB",   500)
            current = str(pv_cur.read().getValue())
            state   = str(pv_st.read().getValue())
            rows.append((identifier, prefix, current, state))
        except Exception as e:
            errors.append(pv_prefix + ": " + str(e))

    if not rows:
        ScriptUtil.showMessageDialog(widget,
            "No selected magnet power supplies found.\n"
            "Tick the checkboxes next to the devices you want to save.")
    else:
        with open(filename, "w") as f:
            f.write("Name,Prefix,Current,State\n")
            for r in rows:
                f.write(",".join(r) + "\n")

        msg = "Saved " + str(len(rows)) + " selected devices to:\n" + filename
        if errors:
            msg += "\n\nRead errors (" + str(len(errors)) + "):\n" + "\n".join(errors[:8])
        ScriptUtil.showMessageDialog(widget, msg)
