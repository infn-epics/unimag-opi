from org.csstudio.display.builder.runtime.script import ScriptUtil, PVUtil
from confutil import csv_to_list
from org.csstudio.display.builder.model import WidgetFactory
import os
import epik8sutil
def createInstance(x, y,macros):
    embedded = WidgetFactory.getInstance().getWidgetDescriptor("embedded").createWidget()
    embedded.setPropertyValue("name", "item-"+str(y/embedded_height))

    embedded.setPropertyValue("x", x)
    embedded.setPropertyValue("y", y)
    embedded.setPropertyValue("width", embedded_width)
    embedded.setPropertyValue("height", embedded_height)
    for macro, value in macros.items():
            embedded.getPropertyValue("macros").add(macro, value)

    embedded.setPropertyValue("file", "pretune-ele.bob")
    return embedded

# logger = ScriptUtil.getLogger()
device_prefix = widget.getEffectiveMacros().getValue("P")

# logger.info("device " +device_prefix )
if not device_prefix:
    device_prefix="NOPREFIX"

name = PVUtil.getString(pvs[0])


# pv = ScriptUtil.getPrimaryPV(filename)
# name = PVUtil.getString(pv)
print "Loading: "+name
#dataset =  ScriptUtil.findWidgetByName(widget, "DataSet")
#loadset = ScriptUtil.findWidgetByName(widget, "LoadSetting")
#loadset.setPropertyValue("enabled",False)

wtemplate = ScriptUtil.findWidgetByName(widget, "element_template") ## name of the hidden template

interlinea=5

embedded_width  = wtemplate.getPropertyValue("width")
embedded_height = wtemplate.getPropertyValue("height") +interlinea
offy=0
cnt=0

def addElement(identifier, prefix, current):
    global cnt
    x=0
    y= offy+ cnt * (embedded_height)

    m={'R': identifier,'P': prefix}
    instance = createInstance(x, y, m)
    widget.runtimeChildren().addChild(instance)
    ## I1 (target), CURRENT_NEXT_SP (pushed to hardware on StepUp) and CURRENT_PREV_SP
    ## (pushed on StepDown) all start at the loaded value: no step is in progress yet,
    ## so target == next set == prev set. ComputeStep.py refines next/prev once nsteps is set.
    loc_i1 = PVUtil.createPV("loc://apply:unimag:"+prefix+":"+identifier+":I1",10)
    loc_next_sp = PVUtil.createPV("loc://apply:unimag:"+prefix+":"+identifier+":CURRENT_NEXT_SP",10)
    loc_prev_sp = PVUtil.createPV("loc://apply:unimag:"+prefix+":"+identifier+":CURRENT_PREV_SP",10)
    loc_i1.write(current)
    loc_next_sp.write(current)
    loc_prev_sp.write(current)
    cnt=cnt+1

if name:
    if name.endswith(".csv"):
        ## Name, Prefix, Current, State
        devinfo = csv_to_list(name)
        for d in devinfo:
            print("ELE "+str(d))
            addElement(d['Name'], d['Prefix'], d['Current'])
    else:
        ## plain text dataset: [index] Name Current Pol Type , whitespace separated, no header
        ## look up each device's real prefix from the same YAML config used elsewhere (e.g. mag_dynamic.bob),
        ## since a single P macro isn't reliably forwarded through every "open in window" action
        prefix_by_name = {}
        for dev in epik8sutil.conf_to_dev(widget):
            prefix_by_name[dev['R']] = dev['P']

        with open(name, 'r') as file:
            for line in file:
                if "#" in line:
                    continue
                parts = line.split()
                if len(parts) == 5:
                    _, identifier, value, pol, _ = parts
                elif len(parts) == 4:
                    identifier, value, pol, _ = parts
                else:
                    continue

                value = float(value)
                if pol == "+":
                    current = abs(value)
                    state = "ON"
                elif pol == "-":
                    current = -abs(value)
                    state = "ON"
                elif pol == "*":
                    current = 0
                    state = "STANDBY"
                else:
                    current = value
                    state = "ON"

                prefix = prefix_by_name.get(identifier, device_prefix)
                if identifier not in prefix_by_name:
                    print("%% "+identifier+" not found in configuration, using prefix \""+prefix+"\"")

                print("ELE "+identifier+" "+prefix+" "+str(current)+" "+state)
                addElement(identifier, prefix, current)

    