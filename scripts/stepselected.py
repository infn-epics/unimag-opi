from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from org.phoebus.pv import PVPool
import time

# "-" / "+" buttons of mag_dynamic.bob: add or subtract the quantity typed in the step entry
# (the buttons' own local PV) to the CURRENT_SP of every selected magnet.
# Selected magnets are the ones whose loc://selection:<prefix>:<name> PV is 1, as for ON/OFF/ZERO.


def _get_pv_refs():
    for _ in range(10):
        try:
            return list(PVPool.getPVReferences())
        except Exception:
            time.sleep(0.05)
    return []


def selected_bases():
    bases = []
    for pvr in _get_pv_refs():
        entry = pvr.getEntry()
        name = entry.getName()
        if not name.startswith("loc://selection:"):
            continue
        try:
            if entry.read().getValue() != 1:
                continue
        except Exception:
            continue
        base = name.replace("loc://selection:", "")
        if "<" in base:
            base = base[:base.index("<")]
        bases.append(base)
    return bases


def run(widget, sign):
    """sign: +1 increments, -1 decrements. No dialog when all goes well: the buttons are meant
    to be clicked repeatedly, only problems are reported."""
    step = abs(PVUtil.getDouble(ScriptUtil.getPrimaryPV(widget)))
    if not step > 0:
        ScriptUtil.showMessageDialog(widget, "Enter the quantity (A) to add or subtract.")
        return

    bases = selected_bases()
    if not bases:
        ScriptUtil.showMessageDialog(widget, "No magnet selected.")
        return

    errors = []
    for base in bases:
        try:
            sp = PVUtil.createPV(base + ":CURRENT_SP", 100)
            current = float(sp.read().getValue())
            ## round: 10.1 + 0.1 must not become 10.200000000000001
            new = round(current + sign * step, 6)
            sp.write(new)
            print("CURRENT_SP " + base + ": " + str(current) + " -> " + str(new))
        except Exception as e:
            errors.append(base + ": " + str(e))

    if errors:
        ScriptUtil.showMessageDialog(widget, "Changed " + str(len(bases) - len(errors)) + " of " + str(len(bases))
                                     + " magnets.\n\nErrors:\n" + "\n".join(errors[:10]))
