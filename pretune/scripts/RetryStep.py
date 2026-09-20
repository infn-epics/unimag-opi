import stepapply
reload(stepapply)  # pick up edits without restarting Phoebus

# "Retry" button: redo the current step (CURRENT_SET_SP), state first then current, for the selected
# rows that have not reached it; the step counter does not move

stepapply.run(widget, "CURRENT_SET_SP", retry=True)
