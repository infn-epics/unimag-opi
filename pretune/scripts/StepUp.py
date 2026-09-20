import stepapply
reload(stepapply)  # pick up edits without restarting Phoebus

# ">" button: push the next step (CURRENT_NEXT_SP) of the selected rows, then advance the counter

stepapply.run(widget, "CURRENT_NEXT_SP", counter_delta=1)
