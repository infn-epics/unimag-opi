from org.csstudio.display.builder.runtime.script import PVUtil
from org.phoebus.pv import PVPool
from java.lang import Exception

TAG = "loc://apply:unimag:"

nsteps = PVUtil.getLong(pvs[0])
counter = PVUtil.getLong(pvs[1])

## nsteps<=0 means "single direct step": jump straight from I0 to I1
if nsteps <= 0:
    nsteps = 1

roots = set()
for pvr in PVPool.getPVReferences():
    pvname = pvr.getEntry().getName()
    if pvname.startswith(TAG) and pvname.endswith(":I1"):
        roots.add(pvname[len(TAG):-len(":I1")])

for root in roots:
    try:
        i1_pv = PVUtil.createPV(TAG+root+":I1", 10)
        i1 = PVUtil.getDouble(i1_pv)

        i0_pv = PVUtil.createPV(root+":CURRENT_RB", 100)
        i0 = PVUtil.getDouble(i0_pv)

        calcstep = (i1 - i0) / float(nsteps)
        next_sp = i0 + calcstep * (counter + 1)
        prev_sp = i0 + calcstep * (counter - 1)

        PVUtil.createPV(TAG+root+":calcstep", 10).write(calcstep)
        PVUtil.createPV(TAG+root+":CURRENT_NEXT_SP", 10).write(next_sp)
        PVUtil.createPV(TAG+root+":CURRENT_PREV_SP", 10).write(prev_sp)

        print("STEP "+root+" I0="+str(i0)+" I1="+str(i1)+" calcstep="+str(calcstep)+" nextSet="+str(next_sp)+" prevSet="+str(prev_sp))
    except Exception as e:
        print("## Error computing step for "+root+": "+str(e))
