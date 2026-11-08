from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from org.csstudio.display.builder.model import WidgetFactory
import restoreutil
import magselection
reload(magselection)
reload(restoreutil)  # pick up edits without restarting Phoebus

# Triggered by the file selector's local PV (pvs[0]) holding the chosen file path, the same
# way pretune loads its datasets. One row (restore-ele.bob) is created for every device in the
# file that is also in the source mag_dynamic.bob selection.

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
    embedded.getPropertyValue("macros").add("RL", restoreutil.epik8sutil.loc_safe(macros["R"]))
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

    did = restoreutil.window_id(widget, pvs[0])
    status = PVUtil.createPV(restoreutil.status_name(did), 10)
    PVUtil.createPV(restoreutil.list_name(did), 10).write("")
    print("Loading: " + name)

    try:
        devices, unknown = restoreutil.read_file(name, widget)
        allowed = magselection.visible_bases(widget, did)

        if not clear_rows():
            status.write("Cannot replace the loaded file: close and reopen this display")
            return

        skipped = []
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
            if base not in allowed:
                skipped.append(base)
                continue

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
        if not bases:
            msg = "No magnets from the file are in the current Zone, Type and Model selection"
        if unknown:
            msg += "   SKIPPED " + str(len(unknown)) + ": " + ", ".join(unknown[:5])
            if len(unknown) > 5:
                msg += ", ..."
        status.write(msg)
        notice = magselection.skipped_message(skipped, 'dataset')
        if notice:
            ScriptUtil.showMessageDialog(widget, notice)
        elif not bases:
            ScriptUtil.showMessageDialog(widget, msg)
    except Exception as e:
        status.write("Cannot load " + name + ": " + str(e))
    finally:
        # forget the path so that picking the same file again reloads it
        pvs[0].write("")


main()
