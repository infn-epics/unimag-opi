import restoreutil
reload(restoreutil)  # pick up edits without restarting Phoebus

# "Restore Selected" button: pushes the (possibly edited) restore set and desired state of every
# checked row to the hardware, STATE first, then CURRENT (see magapply.apply).

restoreutil.run(widget, False)
