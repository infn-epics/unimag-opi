from org.csstudio.display.builder.runtime.script import PVUtil, ScriptUtil
import re

# Every local PV of a pretune window is named  loc://pretune-<DID>:<P>:<R>:<FIELD>
# (DID keeps windows independent: a closed display, or a previously loaded file, never leaks into
# the steps applied by another one). The devices currently shown are kept in loc://pretune-list-<DID>
# as one "P:R" per line, written by LoadPretuneDataSet.py.


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
    return "loc://pretune-" + did + ":" + base + ":" + field


def list_name(did):
    return "loc://pretune-list-" + did


def bases(did):
    try:
        return [b for b in PVUtil.getString(PVUtil.createPV(list_name(did), 10)).split("\n") if b]
    except Exception:
        return []
