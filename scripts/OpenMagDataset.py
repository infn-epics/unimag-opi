from org.csstudio.display.builder.runtime.script import ScriptUtil
from org.phoebus.framework.macros import MacroHandler
from java.util import HashMap

# DID is a widget property macro, absent from getEffectiveMacros(). The
# standard open-display action expands its arguments using only that latter
# provider, leaving $(DID) to resolve against the NEW display instead.
provider = widget.getMacrosOrProperties()
source_id = MacroHandler.replace(provider, '$(DID)')
macros = HashMap()
macros.put('MAGNET_SOURCE_ID', source_id)
macros.put('GROUP', 'mag')
macros.put('CONFFILE', MacroHandler.replace(provider, '$(CONFFILE)'))
macros.put('FACILITY', MacroHandler.replace(provider, '$(FACILITY=ALL)'))
filename = 'restore/restore.bob' if widget.getPropertyValue('name') == 'RestoreBtn' else 'pretune/pretune.bob'
ScriptUtil.openDisplay(widget, filename, 'WINDOW', macros)
