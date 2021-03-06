#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.awt import XCallback
from com.sun.star.beans import XPropertyContainer
from com.sun.star.lang import XServiceInfo, XComponent
from com.sun.star.ucb import XContent, XCommandProcessor2, XContentCreator
from com.sun.star.ucb import InteractiveBadTransferURLException, IllegalIdentifierException
from com.sun.star.ucb.ConnectionMode import ONLINE, OFFLINE

from gdrive import Initialization, CommandInfo, PropertySetInfo, Row, DynamicResultSet, ContentIdentifier
from gdrive import PropertySetInfoChangeNotifier, PropertiesChangeNotifier, CommandInfoChangeNotifier
from gdrive import parseDateTime, isChildOfItem, getChildSelect, getLogger, setContentProperties
from gdrive import updateChildren, createService, getSimpleFile, getResourceLocation
from gdrive import getUcb, getCommandInfo, getProperty, getContentInfo, getContent
from gdrive import propertyChange, getPropertiesValues, setPropertiesValues
from gdrive import getId, getUri, getUriPath, getUcp, getNewItem

#from gdrive import PyPropertiesChangeNotifier, PyPropertySetInfoChangeNotifier, PyCommandInfoChangeNotifier, PyPropertyContainer, PyDynamicResultSet
import requests
import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = 'com.gmail.prrvchr.extensions.gDriveOOo.DriveRootContent'


class DriveRootContent(unohelper.Base, XServiceInfo, XComponent, Initialization, PropertiesChangeNotifier, XContent,
                       PropertySetInfoChangeNotifier, XCommandProcessor2, XContentCreator, XCallback,
                       CommandInfoChangeNotifier, XPropertyContainer):
    def __init__(self, ctx, *namedvalues):
        try:
            self.ctx = ctx
            self.Logger = getLogger(self.ctx)
            level = uno.getConstantByName("com.sun.star.logging.LogLevel.INFO")
            msg = "DriveRootContent loading ..."
            self.Logger.logp(level, "DriveRootContent", "__init__()", msg)
            self.ConnectionMode = OFFLINE
            self.UserName = None
            self.Id = None
            self.Uri = None
            
            self.ContentType = 'application/vnd.google-apps.folder-root'
            self.IsFolder = True
            self.IsDocument = False
            self._Title = 'Sans Nom'
            
            self.MediaType = 'application/vnd.google-apps.folder'
            self.Size = 0
            self.DateModified = parseDateTime()
            self.DateCreated = parseDateTime()
            self._IsRead = False
            self.IsWrite = False
            self.CanRename = False
            self.IsVersionable = False
            self.CreatableContentsInfo = self._getCreatableContentsInfo()
            
            self.IsHidden = False
            self.IsVolume = False
            self.IsRemote = False
            self.IsRemoveable = False
            self.IsFloppy = False
            self.IsCompactDisc = False

            self._commandInfo = self._getCommandInfo()
            self._propertySetInfo = self._getPropertySetInfo()
            self.listeners = []
            self.contentListeners = []
            self.propertiesListener = {}
            self.propertyInfoListeners = []
            self.commandInfoListeners = []
            
            self.statement = None
            self.initialize(namedvalues)
            msg = "DriveRootContent loading Uri: %s ... Done" % self.Uri.getUriReference()
            self.Logger.logp(level, "DriveRootContent", "__init__()", msg)
            print("DriveRootContent.__init__()")
        except Exception as e:
            print("DriveRootContent.__init__().Error: %s - %s" % (e, traceback.print_exc()))

    @property
    def IsRead(self):
        return self._IsRead
    @IsRead.setter
    def IsRead(self, isread):
        propertyChange(self, 'IsRead', self._IsRead, isread)
        self._IsRead = isread
    @property
    def Title(self):
        return self._Title
    @Title.setter
    def Title(self, title):
        propertyChange(self, 'Title', self._Title, title)
        self._Title = title

    # XPropertyContainer
    def addProperty(self, name, attribute, default):
        print("DriveRootContent.addProperty()")
    def removeProperty(self, name):
        print("DriveRootContent.removeProperty()")

    # XComponent
    def dispose(self):
        print("DriveRootContent.dispose()")
        event = uno.createUnoStruct('com.sun.star.lang.EventObject', self)
        for listener in self.listeners:
            listener.disposing(event)
    def addEventListener(self, listener):
        print("DriveRootContent.addEventListener()")
        if listener not in self.listeners:
            self.listeners.append(listener)
    def removeEventListener(self, listener):
        print("DriveRootContent.removeEventListener()")
        if listener in self.listeners:
            self.listeners.remove(listener)

    # XCallback
    def notify(self, data):
        for listener in self.contentListeners:
            listener.contentEvent(data)

    # XContentCreator
    def queryCreatableContentsInfo(self):
        print("DriveRootContent.queryCreatableContentsInfo():*************************")
        return self.CreatableContentsInfo
    def createNewContent(self, contentinfo):
        print("DriveRootContent.createNewContent():************************* %s" % contentinfo)
        return self._createNewContent(contentinfo)

    # XContent
    def getIdentifier(self):
        print("DriveRootContent.getIdentifier()")
        return ContentIdentifier(self.Uri)
    def getContentType(self):
        print("DriveRootContent.getContentType()")
        return self.ContentType
    def addContentEventListener(self, listener):
        print("DriveRootContent.addContentEventListener()")
        self.contentListeners.append(listener)
    def removeContentEventListener(self, listener):
        print("DriveRootContent.removeContentEventListener()")
        if listener in self.contentListeners:
            self.contentListeners.remove(listener)

    # XCommandProcessor2
    def createCommandIdentifier(self):
        return 0
    def execute(self, command, id, environment):
        print("DriveRootContent.execute(): %s" % command.Name)
        if command.Name == 'getCommandInfo':
            return CommandInfo(self._commandInfo)
        elif command.Name == 'getPropertySetInfo':
            return PropertySetInfo(self._propertySetInfo)
        elif command.Name == 'getPropertyValues':
            namedvalues = getPropertiesValues(self, command.Argument, self.Logger)
            return Row(namedvalues)
        elif command.Name == 'setPropertyValues':
            return setPropertiesValues(self, command.Argument, self.Logger)
        elif command.Name == 'open':
            scheme = self.Uri.getScheme()
            connection = self.statement.getConnection()
            if self.ConnectionMode == ONLINE and not self.IsRead:
                self.IsRead = updateChildren(self.ctx, connection, scheme, self.UserName, self.Id)
            # Not Used: command.Argument.Properties - Implement me!!!
            select = getChildSelect(connection, self.ConnectionMode, self.Id, self.Uri.getUriReference())
            return DynamicResultSet(self.ctx, scheme, select)
        elif command.Name == 'createNewContent':
            print("DriveRootContent.execute(): createNewContent %s" % command.Argument)
            return self._createNewContent(command.Argument)
        elif command.Name == 'insert':
            print("DriveRootContent.execute() insert")
        elif command.Name == 'delete':
            print("DriveRootContent.execute(): delete")
        elif command.Name == 'transfer':
            # Transfer command is only used for existing document (File Save)
            # For new document (File Save As) we use command: createNewContent and Insert
            id = command.Argument.NewTitle
            source = command.Argument.SourceURL
            if not isChildOfItem(self.statement.getConnection(), id, self.Id):
                print("DriveRootContent.execute(): transfer: %s - %s" % (source, id))
                raise InteractiveBadTransferURLException("Couln't handle Url: %s" % source, self)
            print("DriveRootContent.execute(): transfer: %s - %s" % (source, id))
            sf = getSimpleFile(self.ctx)
            if sf.exists(source):
                target = getResourceLocation(self.ctx, '%s/%s' % (self.Uri.getScheme(), id))
                inputstream = sf.openFileRead(source)
                sf.writeFile(target, inputstream)
                inputstream.closeInput()
                # Root Uri end whith '/': ie: 'scheme://authority/'
                uri = getUri(self.ctx, '%s%s' % (self.Uri.getUriReference(), id))
                identifier = ContentIdentifier(uri)
                content = getContent(self.ctx, identifier)
                setContentProperties(content, {'Size': sf.getSize(target), 'IsWrite': True})
                if command.Argument.MoveData:
                    pass #must delete object
        elif command.Name == 'close':
            print("DriveRootContent.execute(): close")
        elif command.Name == 'flush':
            print("DriveRootContent.execute(): flush")
        #except Exception as e:
        #    print("DriveRootContent.execute().Error: %s - %e" % (e, traceback.print_exc()))
    def abort(self, id):
        pass
    def releaseCommandIdentifier(self, id):
        pass

    def _createNewContent(self, contentinfo):
        print("DriveRootContent.execute(): createNewContent %s" % contentinfo)
        item = getNewItem(self.ctx, self.Uri, self.UserName)
        if contentinfo.Type == 'application/vnd.google-apps.folder':
            name = 'com.gmail.prrvchr.extensions.gDriveOOo.DriveFolderContent'
        elif contentinfo.Type == 'application/vnd.oasis.opendocument':
            name = 'com.gmail.prrvchr.extensions.gDriveOOo.DriveOfficeContent'
        return createService(name, self.ctx, **item)

    def _getCommandInfo(self):
        commands = {}
        commands['getCommandInfo'] = getCommandInfo('getCommandInfo')
        commands['getPropertySetInfo'] = getCommandInfo('getPropertySetInfo')
        commands['getPropertyValues'] = getCommandInfo('getPropertyValues', '[]com.sun.star.beans.Property')
        commands['setPropertyValues'] = getCommandInfo('setPropertyValues', '[]com.sun.star.beans.PropertyValue')
        commands['open'] = getCommandInfo('open', 'com.sun.star.ucb.OpenCommandArgument2')
        commands['createNewContent'] = getCommandInfo('createNewContent', 'com.sun.star.ucb.ContentInfo')
        commands['insert'] = getCommandInfo('insert', 'com.sun.star.ucb.InsertCommandArgument')
#        commands['insert'] = getCommandInfo('insert', 'com.sun.star.ucb.InsertCommandArgument2')
        commands['delete'] = getCommandInfo('delete', 'boolean')
        commands['transfer'] = getCommandInfo('transfer', 'com.sun.star.ucb.TransferInfo')
        commands['close'] = getCommandInfo('close')
        commands['flush'] = getCommandInfo('flush')
        return commands

    def _getPropertySetInfo(self):
        properties = {}
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        properties['Id'] = getProperty('Id', 'string', bound | readonly)
        properties['ContentType'] = getProperty('ContentType', 'string', bound | readonly)
        properties['MediaType'] = getProperty('MediaType', 'string', bound | readonly)
        properties['IsDocument'] = getProperty('IsDocument', 'boolean', bound | readonly)
        properties['IsFolder'] = getProperty('IsFolder', 'boolean', bound | readonly)
        properties['Title'] = getProperty('Title', 'string', bound)
        properties['Size'] = getProperty('Size', 'long', bound | readonly)
        properties['DateModified'] = getProperty('DateModified', 'com.sun.star.util.DateTime', bound | readonly)
        properties['DateCreated'] = getProperty('DateCreated', 'com.sun.star.util.DateTime', bound | readonly)
        properties['IsRead'] = getProperty('IsRead', 'boolean', bound)
        properties['CreatableContentsInfo'] = getProperty('CreatableContentsInfo', '[]com.sun.star.ucb.ContentInfo', bound | readonly)

        properties['IsHidden'] = getProperty('IsHidden', 'boolean', bound | readonly)
        properties['IsVolume'] = getProperty('IsVolume', 'boolean', bound | readonly)
        properties['IsRemote'] = getProperty('IsRemote', 'boolean', bound | readonly)
        properties['IsRemoveable'] = getProperty('IsRemoveable', 'boolean', bound | readonly)
        properties['IsFloppy'] = getProperty('IsFloppy', 'boolean', bound | readonly)
        properties['IsCompactDisc'] = getProperty('IsCompactDisc', 'boolean', bound | readonly)
        return properties

    def _getCreatableContentsInfo(self):
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        document = uno.getConstantByName('com.sun.star.ucb.ContentInfoAttribute.KIND_DOCUMENT')
        folder = uno.getConstantByName('com.sun.star.ucb.ContentInfoAttribute.KIND_FOLDER')
        foldertype = 'application/vnd.google-apps.folder'
        documenttype = 'application/vnd.oasis.opendocument'
        folderprop = (getProperty('Title', 'string', bound), )
        documentprop = (getProperty('Title', 'string', bound), getProperty('Id', 'string', bound))
        content = (getContentInfo(foldertype, folder, folderprop), getContentInfo(documenttype, document, documentprop))
        return content

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(DriveRootContent,                                                   # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, 'com.sun.star.ucb.Content'))                  # List of implemented services
