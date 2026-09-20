import stepselected
reload(stepselected)  # pick up edits without restarting Phoebus

# "-" button: subtract the step quantity from CURRENT_SP of the selected magnets

stepselected.run(widget, -1)
