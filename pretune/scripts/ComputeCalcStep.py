from org.csstudio.display.builder.runtime.script import PVUtil
from org.phoebus.pv import PVPool
from java.lang import Exception

TAG = "loc://apply:unimag:"

nsteps = PVUtil.getLong(pvs[0])

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
        i1 = PVUtil.getDouble(PVUtil.createPV(TAG+root+":I1", 10))
        ## I0 is captured here, once, as the fixed baseline for the whole stepping run:
        ## it must NOT be re-read every time the counter moves, or calcstep/next/prev
        ## would drift as the real readback ramps during stepping.
        i0 = PVUtil.getDouble(PVUtil.createPV(root+":CURRENT_RB", 100))
        calcstep = (i1 - i0) / float(nsteps)

        PVUtil.createPV(TAG+root+":I0SET", 10).write(i0)
        PVUtil.createPV(TAG+root+":calcstep", 10).write(calcstep)

        print("CALCSTEP "+root+" I0="+str(i0)+" I1="+str(i1)+" nsteps="+str(nsteps)+" calcstep="+str(calcstep))
    except Exception as e:
        print("## Error computing calcstep for "+root+": "+str(e))
