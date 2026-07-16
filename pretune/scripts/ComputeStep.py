from org.csstudio.display.builder.runtime.script import PVUtil
from org.phoebus.pv import PVPool
from java.lang import Exception

TAG = "loc://apply:unimag:"

counter = PVUtil.getLong(pvs[0])

roots = set()
for pvr in PVPool.getPVReferences():
    pvname = pvr.getEntry().getName()
    if pvname.startswith(TAG) and pvname.endswith(":I1"):
        roots.add(pvname[len(TAG):-len(":I1")])

for root in roots:
    try:
        ## Reuse the fixed baseline/step from ComputeCalcStep.py (set only when nsteps
        ## changes) instead of re-reading the live CURRENT_RB on every counter move.
        i0set = PVUtil.getDouble(PVUtil.createPV(TAG+root+":I0SET", 10))
        calcstep = PVUtil.getDouble(PVUtil.createPV(TAG+root+":calcstep", 10))

        current_set_sp = i0set + calcstep * counter
        next_sp = i0set + calcstep * (counter + 1)
        prev_sp = i0set + calcstep * (counter - 1)

        PVUtil.createPV(TAG+root+":CURRENT_SET_SP", 10).write(current_set_sp)
        PVUtil.createPV(TAG+root+":CURRENT_NEXT_SP", 10).write(next_sp)
        PVUtil.createPV(TAG+root+":CURRENT_PREV_SP", 10).write(prev_sp)

        print("STEP "+root+" counter="+str(counter)+" currentSet="+str(current_set_sp)+" nextSet="+str(next_sp)+" prevSet="+str(prev_sp))
    except Exception as e:
        print("## Error computing next/prev for "+root+": "+str(e))
