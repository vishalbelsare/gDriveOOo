#!
# -*- coding: utf-8 -*-

#from pkgutil import iter_modules

#from com.sun.star.document import document

#def existModule(module, path):
#    return module in (name for loader, name, ispkg in iter_modules(path))

#exist = existModule('XCmisDocument', document.__path__)
#print("__init__ %s" % exist)

#from .unotools import isCmisReady

from .cmislib import CmisDocument

from .dbtools import getDbConnection, parseDateTime

from .items import selectRoot, mergeRoot, selectItem, insertItem

from .children import isChildOfItem, updateChildren, getChildSelect

from .identifiers import getCountOfIdentifier, getIdUpdate, getIdSelect, getIdInsert, getNewId


from .contentlib import ContentIdentifier, Row, DynamicResultSet, CommandInfo, CommandInfoChangeNotifier

from .contenttools import getUri, getUriPath, getUcb, getSimpleFile, getContentInfo, getCommandInfo
from .contenttools import getContent, getContentEvent, getUcp, getNewItem, getParentUri
from .contenttools import getId, getContentProperties, getPropertiesValues, setPropertiesValues, propertyChange
from .contenttools import getCmisProperty, setContentProperties, mergeContent

from .google import InputStream, getItem

from .logger import getLogger, getLoggerSetting, setLoggerSetting, getLoggerUrl

from .unotools import getResourceLocation, createService, getStringResource, getPropertyValue
from .unotools import getFileSequence, getProperty, getPropertySetInfoChangeEvent

from .unolib import Component, Initialization, InteractionHandler, PropertiesChangeNotifier
from .unolib import PropertySetInfo, PropertySet, PropertySetInfoChangeNotifier
