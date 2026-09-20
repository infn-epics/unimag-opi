from org.csstudio.display.builder.runtime.script import PVUtil

# Every local PV of a pretune window is named  loc://pretune-<DID>:<P>:<R>:<FIELD>
# (DID keeps windows independent: a closed display, or a previously loaded file, never leaks into
# the steps applied by another one). The devices currently shown are kept in loc://pretune-list-<DID>
# as one "P:R" per line, written by LoadPretuneDataSet.py.


def window_id(widget):
    return widget.getEffectiveMacros().getValue("DID") or "0"


def local_name(did, base, field):
    return "loc://pretune-" + did + ":" + base + ":" + field


def list_name(did):
    return "loc://pretune-list-" + did


def bases(did):
    try:
        return [b for b in PVUtil.getString(PVUtil.createPV(list_name(did), 10)).split("\n") if b]
    except Exception:
        return []
