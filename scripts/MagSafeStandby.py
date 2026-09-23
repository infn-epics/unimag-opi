from org.csstudio.display.builder.runtime.script import ScriptUtil
import magsafeutil

reload(magsafeutil)

filename = ScriptUtil.showSaveAsDialog(widget, "magsafe_snapshot.csv")
if filename is not None:
    if not filename.lower().endswith(".csv"):
        filename += ".csv"
    if ScriptUtil.showConfirmationDialog(widget,
            "Save the tagged magnet setpoints, ramp them to zero, then command STANDBY?"):
        try:
            magsafeutil.status(widget, "Reading all tagged magnets...")
            snapshot = magsafeutil.snapshot_devices(widget)
            # The durable file must succeed before any hardware write is attempted.
            magsafeutil.save_file(filename, snapshot)
            magsafeutil.save_local(widget, filename, snapshot)
            magsafeutil.status(widget, "Snapshot saved; entering standby...")
            result = magsafeutil.enter_standby(widget, snapshot)
            message = ("Snapshot saved to:\n" + filename + "\n\n" +
                       magsafeutil.standby_summary(result, len(snapshot)))
            magsafeutil.status(widget, message.replace("\n", "  "))
            ScriptUtil.showMessageDialog(widget, message)
        except Exception as e:
            magsafeutil.status(widget, "Standby aborted: " + str(e).replace("\n", "  "))
            ScriptUtil.showMessageDialog(widget, "MagSafe standby aborted:\n" + str(e))
