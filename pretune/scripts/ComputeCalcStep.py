from org.csstudio.display.builder.runtime.script import PVUtil
import pretuneutil
reload(pretuneutil)  # pick up edits without restarting Phoebus

did = pretuneutil.window_id(widget)

nsteps = PVUtil.getLong(pvs[0])

## nsteps<=0 means "single direct step": jump straight from I0 to I1
if nsteps <= 0:
    nsteps = 1

for base in pretuneutil.bases(did):
    try:
        def local(field):
            return PVUtil.createPV(pretuneutil.local_name(did, base, field), 10)
        i1 = PVUtil.getDouble(local("I1"))
        ## I0 is captured here, once, as the fixed baseline for the whole stepping run:
        ## it must NOT be re-read every time the counter moves, or calcstep/next/prev
        ## would drift as the real readback ramps during stepping.
        i0 = PVUtil.getDouble(PVUtil.createPV(base+":CURRENT_RB", 100))
        calcstep = (i1 - i0) / float(nsteps)

        local("I0SET").write(i0)
        local("calcstep").write(calcstep)

        print("CALCSTEP "+base+" I0="+str(i0)+" I1="+str(i1)+" nsteps="+str(nsteps)+" calcstep="+str(calcstep))
    except Exception as e:
        print("## Error computing calcstep for "+base+": "+str(e))
