from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from org.csstudio.display.builder.model import WidgetFactory
import restoreutil
reload(restoreutil)  # pick up edits without restarting Phoebus

# Triggered by the file selector's local PV (pvs[0]) holding the chosen file path, the same
# way pretune loads its datasets. One row (restore-ele.bob) is created for every device in the
# file, whether or not it is part of the list shown in mag_dynamic.bob.

ROW_WIDTH  = 760
ROW_HEIGHT = 30
INTERLINE  = 5


def createInstance(y, macros):
    embedded = WidgetFactory.getInstance().getWidgetDescriptor("embedded").createWidget()
    embedded.setPropertyValue("name", "item-" + str(y // (ROW_HEIGHT + INTERLINE)))
    embedded.setPropertyValue("x", 0)
    embedded.setPropertyValue("y", y)
    embedded.setPropertyValue("width", ROW_WIDTH)
    embedded.setPropertyValue("height", ROW_HEIGHT)
    for macro, value in macros.items():
        embedded.getPropertyValue("macros").add(macro, value)
    embedded.setPropertyValue("file", "restore-ele.bob")
    return embedded


def clear_rows():
    """Drop the rows of a previously loaded file. Returns False if this Phoebus cannot."""
    children = widget.runtimeChildren()
    try:
        for child in list(children.getValue()):
            if child.getName().startswith("item-"):
                children.removeChild(child)
        return True
    except Exception as e:
        print("## Cannot remove previous rows: " + str(e))
        return False


def write_local(did, base, field, value):
    PVUtil.createPV(restoreutil.local_name(did, base, field), 10).write(value)


def main():
    name = PVUtil.getString(pvs[0])
    if not name:
        return  # initial value, or the reset done below

    did = restoreutil.window_id(widget)
    status = PVUtil.createPV(restoreutil.status_name(did), 10)
    print("Loading: " + name)

    try:
        devices, unknown = restoreutil.read_file(name, widget)
        if not devices:
            status.write("No devices found in " + name)
            return

        if not clear_rows():
            status.write("Cannot replace the loaded file: close and reopen this display")
            return

        bases = []
        for d in devices:
            identifier = d.get("Name", "")
            prefix     = d.get("Prefix", "")
            if not identifier or not prefix:
                unknown.append(str(d) + " (missing Name/Prefix)")
                continue
            try:
                current = float(d.get("Current", ""))
            except ValueError:
                unknown.append(identifier + " (bad current \"" + d.get("Current", "") + "\")")
                continue
            ## INTERLOCK, FAULT ... cannot be commanded: leave the desired state blank
            state = d.get("State", "")
            if state not in restoreutil.RESTORABLE_STATES:
                state = ""
            base = prefix + ":" + identifier

            y = len(bases) * (ROW_HEIGHT + INTERLINE)
            widget.runtimeChildren().addChild(
                createInstance(y, {"R": identifier, "P": prefix, "RID": did}))
            ## restore set (editable) and desired state start at the values of the file
            write_local(did, base, "SP", current)
            write_local(did, base, "STATE_SP", state)
            write_local(did, base, "enabled", 1)
            print("ELE " + base + " current=" + str(current) + " STATE_SP=" + state)
            bases.append(base)

        PVUtil.createPV(restoreutil.list_name(did), 10).write("\n".join(bases))

        msg = "Loaded " + str(len(bases)) + " devices from " + name
        if unknown:
            msg += "   SKIPPED " + str(len(unknown)) + ": " + ", ".join(unknown[:5])
            if len(unknown) > 5:
                msg += ", ..."
        status.write(msg)
    except Exception as e:
        status.write("Cannot load " + name + ": " + str(e))
    finally:
        # forget the path so that picking the same file again reloads it
        pvs[0].write("")


main()
