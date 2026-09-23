from org.csstudio.display.builder.runtime.script import PVUtil
from org.csstudio.display.builder.model import WidgetFactory
import magsafeutil

reload(magsafeutil)

ROW_WIDTH = 760
ROW_HEIGHT = 30
INTERLINE = 5


def create_instance(y, dev, did):
    embedded = WidgetFactory.getInstance().getWidgetDescriptor("embedded").createWidget()
    embedded.setPropertyValue("name", "magsafe-item-" + str(y // (ROW_HEIGHT + INTERLINE)))
    embedded.setPropertyValue("x", 0)
    embedded.setPropertyValue("y", y)
    embedded.setPropertyValue("width", ROW_WIDTH)
    embedded.setPropertyValue("height", ROW_HEIGHT)
    embedded.getPropertyValue("macros").add("NAME", dev["NAME"])
    embedded.getPropertyValue("macros").add("P", dev["P"])
    embedded.getPropertyValue("macros").add("R", dev["R"])
    embedded.getPropertyValue("macros").add("SID", did)
    embedded.getPropertyValue("macros").add("MAGSAFE_ID", did)
    embedded.setPropertyValue("file", "magsafe-ele.bob")
    return embedded


try:
    devices = magsafeutil.tagged_devices(widget)
    did = magsafeutil.window_id(widget)

    # Create the visible rows first.  The safety LED is helpful, but a failure in
    # its local-PV setup must never hide the protected-magnet list.
    for index, dev in enumerate(devices):
        widget.runtimeChildren().addChild(
            create_instance(index * (ROW_HEIGHT + INTERLINE), dev, did))

    try:
        bases = [dev["P"] + ":" + dev["R"] for dev in devices]
        PVUtil.createPV(magsafeutil.managed_list_name(widget), 10).write("\n".join(bases))
        PVUtil.createPV(magsafeutil.local_name(widget, "snapshot-valid"), 10).write(0)
        magsafeutil.update_safe_status(widget)
        magsafeutil.status(widget, "Managing " + str(len(devices)) + " magnets tagged '" +
                           magsafeutil.safety_tag(widget) + "'. No local snapshot yet.")
    except Exception as e:
        message = ("Showing " + str(len(devices)) + " tagged magnets; " +
                   "safety LED initialization failed: " + str(e))
        print(message)
        magsafeutil.status(widget, message)
except Exception as e:
    magsafeutil.status(widget, "Cannot load MagSafe devices: " + str(e))
