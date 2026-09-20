import restoreutil
reload(restoreutil)  # pick up edits without restarting Phoebus

# "Retry" button: redoes the restore, state first then current, only for the checked rows that
# have not reached their restore set (same test as the OK led) and always re-sending the current.

restoreutil.run(widget, True)
