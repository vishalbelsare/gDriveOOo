#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XComponent
from com.sun.star.ucb import XContentIdentifier, XContentAccess, XDynamicResultSet
from com.sun.star.sdbc import XRow, XResultSet, XResultSetMetaDataSupplier, XCloseable
from com.sun.star.beans import XPropertiesChangeNotifier
#from com.sun.star.document import XCmisDocument

from .unolib import Component, PropertySet
from .unotools import createService, getProperty, getResourceLocation
from .contenttools import getContent
from .dbtools import getDbConnection
from .children import getChildSelect


class ContentIdentifier(unohelper.Base, XContentIdentifier):
    def __init__(self, uri):
        self.uri = uri

    # XContentIdentifier
    def getContentIdentifier(self):
        return self.uri.getUriReference()
    def getContentProviderScheme(self):
        return self.uri.getScheme()


class Row(unohelper.Base, XRow):
    def __init__(self, namedvalues):
        self.namedvalues = namedvalues
        self.isNull = False

    # XRow
    def wasNull(self):
        return self.isNull
    def getString(self, index):
        return self._getValue(index -1)
    def getBoolean(self, index):
        return self._getValue(index -1)
    def getByte(self, index):
        return self._getValue(index -1)
    def getShort(self, index):
        return self._getValue(index -1)
    def getInt(self, index):
        return self._getValue(index -1)
    def getLong(self, index):
        return self._getValue(index -1)
    def getFloat(self, index):
        return self._getValue(index -1)
    def getDouble(self, index):
        return self._getValue(index -1)
    def getBytes(self, index):
        return self._getValue(index -1)
    def getDate(self, index):
        return self._getValue(index -1)
    def getTime(self, index):
        return self._getValue(index -1)
    def getTimestamp(self, index):
        return self._getValue(index -1)
    def getBinaryStream(self, index):
        return self._getValue(index -1)
    def getCharacterStream(self, index):
        return self._getValue(index -1)
    def getObject(self, index, map):
        return self._getValue(index -1)
    def getRef(self, index):
        return self._getValue(index -1)
    def getBlob(self, index):
        return self._getValue(index -1)
    def getClob(self, index):
        return self._getValue(index -1)
    def getArray(self, index):
        return self._getValue(index -1)

    def _getValue(self, index):
        value  = None
        self.isNull = True
        if index in range(len(self.namedvalues)):
            value = self.namedvalues[index].Value
            self.isNull = value is None
        return value
        

class DynamicResultSet(unohelper.Base, XDynamicResultSet):
    def __init__(self, ctx, scheme, select):
        self.ctx = ctx
        self.scheme = scheme
        self.select = select

    # XDynamicResultSet
    def getStaticResultSet(self):
        return ContentResultSet(self.ctx, self.scheme, self.select,)
    def setListener(self, listener):
        print("DynamicResultSet.setListener():")
        pass
    def connectToCache(self, cache):
        print("DynamicResultSet.connectToCache():")
        pass
    def getCapabilities(self):
        print("DynamicResultSet.getCapabilities():")
        return uno.getConstantByName('com.sun.star.ucb.ContentResultSetCapability.SORTED')


class ContentResultSet(unohelper.Base, PropertySet, XComponent, XRow, XResultSet, XResultSetMetaDataSupplier,
                       XCloseable, XContentAccess):
    def __init__(self, ctx, scheme, select):
        self.ctx = ctx
        self.scheme = scheme
        self.resultset = select.executeQuery()
        self.resultset.last()
        self.RowCount = self.resultset.Row
        self.IsRowCountFinal = not select.MoreResults
        self.resultset.beforeFirst()
        self.listeners = []

    def _getPropertySetInfo(self):
        properties = {}
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        properties['RowCount'] = getProperty('RowCount', 'long', readonly)
        properties['IsRowCountFinal'] = getProperty('IsRowCountFinal', 'boolean', readonly)
        return properties

    # XComponent
    def dispose(self):
        print("contentlib.ContentResultSet.dispose() 1")
        #if not self.connection.isClosed():
        #    self.connection.close()
        event = uno.createUnoStruct('com.sun.star.lang.EventObject', self)
        for listener in self.listeners:
            listener.disposing(event)
        print("contentlib.ContentResultSet.dispose() 2 ********************************************************")
    def addEventListener(self, listener):
        print("contentlib.ContentResultSet.addEventListener() *************************************************")
        self.listeners.append(listener)
    def removeEventListener(self, listener):
        print("contentlib.ContentResultSet.removeEventListener() **********************************************")
        if listener in self.listeners:
            self.listeners.remove(listener)

    # XResultSet
    def next(self):
        return self.resultset.next()
    def isBeforeFirst(self):
        return self.resultset.isBeforeFirst()
    def isAfterLast(self):
        return self.resultset.isAfterLast()
    def isFirst(self):
        return self.resultset.isFirst()
    def isLast(self):
        return self.resultset.isLast()
    def beforeFirst(self):
        self.resultset.beforeFirst()
    def afterLast(self):
        self.resultset.afterLast()
    def first(self):
        return self.resultset.first()
    def last(self):
        return self.resultset.last()
    def getRow(self):
        return self.resultset.getRow()
    def absolute(self, row):
        return self.resultset.absolute(row)
    def relative(self, row):
        return self.resultset.relative(row)
    def previous(self):
        return self.resultset.previous()
    def refreshRow(self):
        self.resultset.refreshRow()
    def rowUpdated(self):
        return self.resultset.rowUpdated()
    def rowInserted(self):
        return self.resultset.rowInserted()
    def rowDeleted(self):
        return self.resultset.rowDeleted()
    def getStatement(self):
        return self.resultset.getStatement()

    # XContentAccess
    def queryContentIdentifierString(self):
        return self.resultset.getString(self.resultset.findColumn('TargetURL'))
    def queryContentIdentifier(self):
        identifier = self.queryContentIdentifierString()
        return ContentIdentifier(self.scheme, identifier)
    def queryContent(self):
        identifier = self.queryContentIdentifier()
        return getContent(self.ctx, identifier)

    # XResultSetMetaDataSupplier
    def getMetaData(self):
        return self.resultset.getMetaData()

    # XCloseable
    def close(self):
        print("ContentResultSet.close() *****************************************************")
        pass

    # XRow
    def wasNull(self):
        return self.resultset.wasNull()
    def getString(self, index):
        return self.resultset.getString(index)
    def getBoolean(self, index):
        return self.resultset.getBoolean(index)
    def getByte(self, index):
        return self.resultset.getByte(index)
    def getShort(self, index):
        return self.resultset.getShort(index)
    def getInt(self, index):
        return self.resultset.getInt(index)
    def getLong(self, index):
        return self.resultset.getLong(index)
    def getFloat(self, index):
        return self.resultset.getFloat(index)
    def getDouble(self, index):
        return self.resultset.getDouble(index)
    def getBytes(self, index):
        return self.resultset.getBytes(index)
    def getDate(self, index):
        return self.resultset.getDate(index)
    def getTime(self, index):
        return self.resultset.getTime(index)
    def getTimestamp(self, index):
        return self.resultset.getTimestamp(index)
    def getBinaryStream(self, index):
        return self.resultset.getBinaryStream(index)
    def getCharacterStream(self, index):
        return self.resultset.getCharacterStream(index)
    def getObject(self, index, map):
        return self.resultset.getObject(index, map)
    def getRef(self, index):
        return self.resultset.getRef(index)
    def getBlob(self, index):
        return self.resultset.getBlob(index)
    def getClob(self, index):
        return self.resultset.getClob(index)
    def getArray(self, index):
        return self.resultset.getArray(index)


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

'''
class XCmisDocument(unohelper.Base, XCmisDocument):
    def __init__(self, cmisproperties={}):
        self._CmisProperties = cmisproperties

    @property
    def CmisProperties(self):
        return tuple(self._CmisProperties.values)

    #XCmisDocument
    def checkOut(self):
        pass
    def cancelCheckOut(self):
        pass
    def checkIn(self, ismajor, comment):
        pass
    def isVersionable(self):
        return True
    def canCheckOut(self):
        return True
    def canCancelCheckOut(self):
        return True
    def canCheckIn (self):
        return True
    def updateCmisProperties(self, cmisproperties):
        for cmisproperty in cmisproperties:
            id = cmisproperty.Id
            if id in self._CmisProperties:
                self._CmisProperties[id] = cmisproperty
    def getAllVersions(self):
        return ()
'''
