import stepapply
reload(stepapply)  # pick up edits without restarting Phoebus

# "<" button: push the previous step (CURRENT_PREV_SP) of the selected rows, then go back on the counter

stepapply.run(widget, "CURRENT_PREV_SP", counter_delta=-1)
