#!
# -*- coding: utf-8 -*-

import uno
import unohelper

from com.sun.star.lang import XComponent, XInitialization
from com.sun.star.beans import XPropertyContainer, XPropertySet, XPropertySetInfo
from com.sun.star.beans import XPropertiesChangeNotifier, XPropertySetInfoChangeNotifier, UnknownPropertyException
from com.sun.star.task import XInteractionHandler


class Component(XComponent):
    def __init__(self):
        self.listeners = []

    # XComponent
    def dispose(self):
        print("unolib.Component.dispose() 1")
        event = uno.createUnoStruct('com.sun.star.lang.EventObject', self)
        for listener in self.listeners:
            listener.disposing(event)
        print("unolib.Component.dispose() 2 ********************************************************")
    def addEventListener(self, listener):
        print("unolib.Component.addEventListener() *************************************************")
        if listener not in self.listeners:
            self.listeners.append(listener)
    def removeEventListener(self, listener):
        print("unolib.Component.removeEventListener() **********************************************")
        if listener in self.listeners:
            self.listeners.remove(listener)


class Initialization(XInitialization):
    # XInitialization
    def initialize(self, namedvalues=()):
        for namedvalue in namedvalues:
            if hasattr(namedvalue, 'Name') and hasattr(namedvalue, 'Value') and hasattr(self, namedvalue.Name):
                setattr(self, namedvalue.Name, namedvalue.Value)


class InteractionHandler(unohelper.Base, XInteractionHandler):
    # XInteractionHandler
    def handle(self, requester):
        pass


class PropertySet(XPropertySet):
    def _getPropertySetInfo(self):
        raise NotImplementedError

    # XPropertySet
    def getPropertySetInfo(self):
        properties = self._getPropertySetInfo()
        return PropertySetInfo(properties)
    def setPropertyValue(self, name, value):
        properties = self._getPropertySetInfo()
        if name in properties and hasattr(self, name):
            setattr(self, name, value)
        else:
            msg = 'Cant setPropertyValue, UnknownProperty: %s - %s' % (name, value)
            raise UnknownPropertyException(msg, self)
    def getPropertyValue(self, name):
        if name in self._getPropertySetInfo() and hasattr(self, name):
            return getattr(self, name)
        else:
            msg = 'Cant getPropertyValue, UnknownProperty: %s' % name
            raise UnknownPropertyException(msg, self)
    def addPropertyChangeListener(self, name, listener):
        pass
    def removePropertyChangeListener(self, name, listener):
        pass
    def addVetoableChangeListener(self, name, listener):
        pass
    def removeVetoableChangeListener(self, name, listener):
        pass


class PropertiesChangeNotifier(XPropertiesChangeNotifier):
    def __init__(self):
        print("PyPropertiesChangeNotifier.__init__()")
        self.propertiesListener = {}

    #XPropertiesChangeNotifier
    def addPropertiesChangeListener(self, names, listener):
        print("PyPropertiesChangeNotifier.addPropertiesChangeListener()")
        for name in names:
            if name not in self.propertiesListener:
                self.propertiesListener[name] = []
            self.propertiesListener[name].append(listener)
    def removePropertiesChangeListener(self, names, listener):
        print("PyPropertiesChangeNotifier.removePropertiesChangeListener()")
        for name in names:
            if name in self.propertiesListener:
                if listener in self.propertiesListener[name]:
                    self.propertiesListener[name].remove(listener)


class PropertySetInfo(unohelper.Base, XPropertySetInfo):
    def __init__(self, properties, getCmisProperty):
        self.properties = properties
        self.getCmisProperty = getCmisProperty

    # XPropertySetInfo
    def getProperties(self):
        print("PyPropertySetInfo.getProperties()")
        return tuple(self.properties.values())
    def getPropertyByName(self, name):
        print("PyPropertySetInfo.getPropertyByName(): %s" % name)
        if name in self.properties:
            return self.properties[name]
        print("PyPropertySetInfo.getPropertyByName() Error: %s" % name)
        msg = 'Cant getPropertyByName, UnknownProperty: %s' % name
        raise UnknownPropertyException(msg, self)
    def hasPropertyByName(self, name):
        print("PyPropertySetInfo.hasPropertyByName(): %s" % name)
        if name == 'CmisProperties'  and name not in self.properties:
            print("PyPropertySetInfo.hasPropertyByName(): %s" % (name in self.properties, ))
            properties = self.getCmisProperty()
            self.properties.update(properties)
            print("PyPropertySetInfo.hasPropertyByName(): %s" % (name in self.properties, ))
        return name in self.properties


class PropertySetInfoChangeNotifier(XPropertySetInfoChangeNotifier):
    def __init__(self):
        self.propertyInfoListeners = []

    # XPropertySetInfoChangeNotifier
    def addPropertySetInfoChangeListener(self, listener):
        self.propertyInfoListeners.append(listener)
    def removePropertySetInfoChangeListener(self, listener):
        if listener in self.propertyInfoListeners:
            self.propertyInfoListeners.remove(listener)
