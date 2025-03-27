from org.csstudio.display.builder.runtime.script import ScriptUtil,PVUtil
from confutils import csv_to_dict
import os
from java.lang import Exception
embedded_width = 800
embedded_height = 30



logger = ScriptUtil.getLogger()

conffile = widget.getEffectiveMacros().getValue("CONFFILE")
display_model =  widget.getDisplayModel()

display_path = os.path.dirname(display_model.getUserData(display_model.USER_DATA_INPUT_FILE))

confpath=display_path+"/"+conffile

if not os.path.exists(confpath):
    ScriptUtil.showMessageDialog(widget,"Cannot find  file \""+confpath+"\" please set CONFFILE macro to a correct file")
    
  
## parse conf file
print "LOADING CONFIGURATION:"+ confpath

maginfo=csv_to_dict(confpath)
combozone = ScriptUtil.findWidgetByName(widget, "Zonecombo")
combotype = ScriptUtil.findWidgetByName(widget, "Typecombo")
devices = []

# zones=["all"]
# types=["all"]
zones=set()
types=set()
zones.add("all")
types.add("all")
# for key in maginfo:
#     devices.append({'R': key,"P":maginfo[key]['Prefix']})

for key in maginfo:
    z=maginfo[key]['Zone']
    # print(key+" zone:"+z)
    zones.add(z)

for key in maginfo:
    t=maginfo[key]['Type']
    # print(key+" type:"+t)
    types.add(t) 


zones = list(zones)
types = list(types)
print "Zones:"+ str(zones)
print "Types:"+ str(types)


#pvn="loc://maginfo-"+DID
# print ("MAGINFO:"+ pvn)

#loc_pv = PVUtil.createPV(pvn,1)
pvs[0].write(str(maginfo))

combozone.setItems(zones)
combotype.setItems(types)
#pvs[1].write("('all', 'TT', 'TB', 'TM')")
#pvs[2].write(types)



# display = widget.getDisplayModel()
# rows = 35
# for i in range(len(devices)):
#     # x = (i / rows) * embedded_width
#     # y = 170 + embedded_height*(i % rows)
#     x=0
#     y= i * embedded_height
#     instance = createInstance(x, y, devices[i])
#     display.runtimeChildren().addChild(instance)
    
