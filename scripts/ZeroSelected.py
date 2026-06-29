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

def zero_selected():
    lpvs = _get_pv_refs()
    count = 0
    errors = []

    for pvr in lpvs:
        selection_pv = pvr.getEntry()
        name = selection_pv.getName()

        if name.startswith("loc://selection:"):
            if selection_pv.read().getValue() == 1:
                pv_prefix = name.replace("loc://selection:", "")
                prefix, identifier = pv_prefix.rsplit(":", 1)
                try:
                    cur_sp_pv = PVUtil.createPV(pv_prefix + ":CURRENT_SP", 100)
                    cur_sp_pv.write(0.0)
                    count += 1
                    print("Zeroed magnet: " + identifier)
                except Exception as e:
                    errors.append("Error zeroing " + identifier + ": " + str(e))

    if errors:
        ScriptUtil.showMessageDialog(widget,
            "Zeroed " + str(count) + " magnets\n\nErrors:\n" + "\n".join(errors))
    else:
        ScriptUtil.showMessageDialog(widget,
            "Successfully zeroed " + str(count) + " selected magnets")

zero_selected()
