from org.csstudio.display.builder.runtime.script import PVUtil
import pretuneutil
reload(pretuneutil)  # pick up edits without restarting Phoebus

did = pretuneutil.window_id(widget)

counter = PVUtil.getLong(pvs[0])

for base in pretuneutil.bases(did):
    try:
        def local(field):
            return PVUtil.createPV(pretuneutil.local_name(did, base, field), 10)
        ## Reuse the fixed baseline/step from ComputeCalcStep.py (set only when nsteps
        ## changes) instead of re-reading the live CURRENT_RB on every counter move.
        i0set = PVUtil.getDouble(local("I0SET"))
        calcstep = PVUtil.getDouble(local("calcstep"))

        current_set_sp = i0set + calcstep * counter
        next_sp = i0set + calcstep * (counter + 1)
        prev_sp = i0set + calcstep * (counter - 1)

        local("CURRENT_SET_SP").write(current_set_sp)
        local("CURRENT_NEXT_SP").write(next_sp)
        local("CURRENT_PREV_SP").write(prev_sp)

        print("STEP "+base+" counter="+str(counter)+" currentSet="+str(current_set_sp)+" nextSet="+str(next_sp)+" prevSet="+str(prev_sp))
    except Exception as e:
        print("## Error computing next/prev for "+base+": "+str(e))
