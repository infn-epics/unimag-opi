from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from javax.swing import JFileChooser, JOptionPane, JScrollPane, JTextArea
from javax.swing.filechooser import FileNameExtensionFilter
import time

# States that can be commanded via STATE_SP — anything else (INTERLOCK, FAULT …) is skipped
RESTORABLE_STATES = {"ON", "STANDBY", "OFF"}

# ── 1. File selection ──────────────────────────────────────────────────────────
chooser = JFileChooser()
chooser.setDialogTitle("Select snapshot file to restore")
chooser.setFileFilter(FileNameExtensionFilter("CSV Snapshot files (*.csv)", ["csv"]))
if chooser.showOpenDialog(None) != JFileChooser.APPROVE_OPTION:
    pass  # cancelled
else:
    filename = chooser.getSelectedFile().getAbsolutePath()

    # ── 2. Parse CSV ───────────────────────────────────────────────────────────
    with open(filename, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    header = [h.strip() for h in lines[0].split(",")]
    devices = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        devices.append(dict(zip(header, parts)))

    if not devices:
        ScriptUtil.showMessageDialog(widget, "No devices found in:\n" + filename)
    else:
        # ── 3. Read current state from EPICS and build diff ────────────────────
        devdata = []
        for dev in devices:
            name      = dev.get("Name", "")
            prefix    = dev.get("Prefix", "")
            saved_cur = dev.get("Current", "")
            saved_st  = dev.get("State",   "")
            pv_base   = prefix + ":" + name

            entry = {"name": name, "pv_base": pv_base,
                     "saved_cur": saved_cur, "saved_st": saved_st}
            try:
                pv_cur_rb = PVUtil.createPV(pv_base + ":CURRENT_RB", 500)
                pv_st_rb  = PVUtil.createPV(pv_base + ":STATE_RB",   500)
                actual_cur = str(pv_cur_rb.read().getValue())
                actual_st  = str(pv_st_rb.read().getValue())
                entry["actual_cur"] = actual_cur
                entry["actual_st"]  = actual_st

                try:
                    entry["cur_diff"] = abs(float(actual_cur) - float(saved_cur)) > 0.001
                except Exception:
                    entry["cur_diff"] = actual_cur != saved_cur

                # Only flag state diff when the saved state is actually restorable
                entry["st_diff"] = (actual_st != saved_st) and (saved_st in RESTORABLE_STATES)

            except Exception as e:
                entry["error"] = str(e)
                entry["cur_diff"] = False
                entry["st_diff"]  = False

            devdata.append(entry)

        diffs = [d for d in devdata if d.get("st_diff") or d.get("cur_diff") or "error" in d]

        # ── 4. Build diff report ───────────────────────────────────────────────
        sep = "-" * 84
        if not diffs:
            diff_lines = [
                "No differences between saved snapshot and current state.",
                "Total devices: " + str(len(devdata)),
                "",
                "Do you still want to apply the restore?"
            ]
        else:
            diff_lines = [
                "Differences (" + str(len(diffs)) + " of " + str(len(devdata)) + " devices):",
                "",
                "{:<18} {:>11} {:>11}   {:<12} {:<12}".format(
                    "Device", "Saved_A(A)", "Now_A(A)", "Saved_St", "Now_St"),
                sep
            ]
            for d in diffs:
                if "error" in d:
                    diff_lines.append("{:<18}  ERROR: {}".format(d["name"][:17], d["error"][:55]))
                else:
                    mark_a = " <" if d["cur_diff"] else "  "
                    mark_s = " <" if d["st_diff"]  else "  "
                    note = "" if d["saved_st"] in RESTORABLE_STATES else "  [state skipped]"
                    diff_lines.append("{:<18} {:>11}{} {:>12}{}   {:>11} {:>11}{}".format(
                        d["name"][:17],
                        d["saved_cur"][:10], mark_a,
                        d["saved_st"][:11],  mark_s,
                        d.get("actual_cur", "?")[:10],
                        d.get("actual_st",  "?")[:10],
                        note
                    ))
            diff_lines += [
                sep,
                "",
                "\"<\" = will change.  States not in {ON, STANDBY, OFF} are not restored.",
                "Proceed?"
            ]

        diff_text = "\n".join(diff_lines)

        text_area = JTextArea(diff_text, min(25, len(diff_lines) + 3), 90)
        text_area.setEditable(False)
        text_area.setFont(
            text_area.getFont().deriveFont(
                text_area.getFont().getStyle(),
                12.0
            )
        )
        scroll = JScrollPane(text_area)

        choice = JOptionPane.showConfirmDialog(
            None, scroll,
            "Restore from: " + chooser.getSelectedFile().getName(),
            JOptionPane.YES_NO_OPTION,
            JOptionPane.WARNING_MESSAGE
        )

        if choice != JOptionPane.YES_OPTION:
            pass  # user cancelled
        else:
            # ── 5. Apply: STATE first (if restorable), then CURRENT ────────────
            applied = 0
            errors  = []

            for d in devdata:
                if "error" in d:
                    errors.append(d["name"] + ": " + d["error"])
                    continue
                pv_base = d["pv_base"]
                try:
                    if d["st_diff"]:  # already False when state is not restorable
                        pv_st_sp = PVUtil.createPV(pv_base + ":STATE_SP", 500)
                        pv_st_sp.write(d["saved_st"])
                        time.sleep(0.2)

                    if d["cur_diff"]:
                        pv_cur_sp = PVUtil.createPV(pv_base + ":CURRENT_SP", 500)
                        pv_cur_sp.write(float(d["saved_cur"]))

                    applied += 1
                except Exception as e:
                    errors.append(d["name"] + ": " + str(e))

            msg = "Restore complete. Applied to " + str(applied) + " of " + str(len(devdata)) + " devices."
            if errors:
                msg += "\n\nErrors:\n" + "\n".join(errors[:10])
            ScriptUtil.showMessageDialog(widget, msg)
