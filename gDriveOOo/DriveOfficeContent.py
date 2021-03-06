#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.beans import XPropertyContainer
from com.sun.star.container import XChild
from com.sun.star.lang import XServiceInfo, NoSupportException
from com.sun.star.ucb import XContent, XCommandProcessor2, XContentCreator, IllegalIdentifierException
from com.sun.star.ucb.ConnectionMode import ONLINE, OFFLINE

from gdrive import Component, Initialization, PropertiesChangeNotifier, CmisDocument
from gdrive import PropertySetInfoChangeNotifier, ContentIdentifier, CommandInfoChangeNotifier
from gdrive import getUri, getUriPath, getParentUri, getContentInfo, getPropertiesValues
from gdrive import CommandInfo, PropertySetInfo, Row, InputStream, createService
from gdrive import getResourceLocation, parseDateTime, getPropertySetInfoChangeEvent
from gdrive import getContent, getSimpleFile, getCommandInfo, getProperty, getUcp
from gdrive import propertyChange, setPropertiesValues, getLogger, getCmisProperty, getPropertyValue
#from gdrive import PyPropertiesChangeNotifier, PyPropertySetInfoChangeNotifier, PyCommandInfoChangeNotifier, PyPropertyContainer
import requests
import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = 'com.gmail.prrvchr.extensions.gDriveOOo.DriveOfficeContent'


class DriveOfficeContent(unohelper.Base, XServiceInfo, Component, Initialization, PropertiesChangeNotifier,
                         XContent, XCommandProcessor2, XChild, XPropertyContainer, PropertySetInfoChangeNotifier,
                         CommandInfoChangeNotifier, XContentCreator):
#                         PyPropertyContainer, PyPropertiesChangeNotifier, PyPropertySetInfoChangeNotifier, PyCommandInfoChangeNotifier):
    def __init__(self, ctx, *namedvalues):
        try:
            self.ctx = ctx
            self.Logger = getLogger(self.ctx)
            level = uno.getConstantByName("com.sun.star.logging.LogLevel.INFO")
            msg = "DriveOfficeContent loading ..."
            self.Logger.logp(level, "DriveOfficeContent", "__init__()", msg)
            self.ConnectionMode = OFFLINE
            self.UserName = None
            self._Id = None
            self.Uri = None
            
            self.ContentType = 'application/vnd.oasis.opendocument'
            self.IsFolder = False
            self.IsDocument = True
            self._Title = 'Sans Nom'
            
            self.MediaType = None
            self._Size = 0
            self.DateModified = parseDateTime()
            self.DateCreated = parseDateTime()
            
            self.CreatableContentsInfo = self._getCreatableContentsInfo()
            self.IsReadOnly = False
            
            self._commandInfo = self._getCommandInfo()
            self._propertySetInfo = self._getPropertySetInfo()
            self.listeners = []
            self.contentListeners = []
            self.propertiesListener = {}
            self.propertyInfoListeners = []
            self.commandInfoListeners = []
            
            self.Author = 'Pierre Vacher'
            self.Keywords = 'clefs de recherche'
            self.Subject = 'Test de GoogleDriveFileContent'
            self.IsVersionable = False
            self._CmisProperties = None
            self._TitleOnServer = None
            self.CanRename = False
            self._IsWrite = False
            self._IsRead = False
            
            self.IsHidden = False
            self.IsVolume = False
            self.IsRemote = False
            self.IsRemoveable = False
            self.IsFloppy = False
            self.IsCompactDisc = False
            
            self.statement = None
            self.initialize(namedvalues)
            
            self.ObjectId = self.Id
            self.CanCheckOut = True
            self.CanCheckIn = True
            self.CanCancelCheckOut = True
            self.TargetURL = self.Uri.getUriReference()
            self.BaseURI = getParentUri(self.ctx, self.Uri).getUriReference()
            self.CasePreservingURL = self.Uri.getUriReference()
#            print("DriveOfficeContent.__init__(): %s - %s" % (self.Uri.getUriReference(), self.BaseURI))
            msg = "DriveOfficeContent loading Uri: %s ... Done" % self.Uri.getUriReference()
            self.Logger.logp(level, "DriveOfficeContent", "__init__()", msg)            
            print("DriveOfficeContent.__init__()")
        except Exception as e:
            print("DriveOfficeContent.__init__().Error: %s - %e" % (e, traceback.print_exc()))

    @property
    def Id(self):
        return self._Id
    @Id.setter
    def Id(self, id):
        propertyChange(self, 'Id', self._Id, id)
        self._Id = id
    @property
    def TitleOnServer(self):
        print("DriveOfficeContent.TitleOnServer(): 1")
        #LibreOffice look for this property!!! Need this hack to have Transfer working fine in LibreOffice...
        if self._TitleOnServer is None:
            self._TitleOnServer = self._Title
            self._Title = self.Id
        return self._TitleOnServer
    @property
    def CmisProperties(self):
        print("DriveOfficeContent.CmisProperties(): 1")
        if self._CmisProperties is None:
            self._CmisProperties = self._getCmisProperties()
        return self._CmisProperties
    @property
    def Title(self):
        return self._Title
    @Title.setter
    def Title(self, title):
        if self._TitleOnServer is None:
            propertyChange(self, 'Title', self._Title, title)
        self._Title = title
    @property
    def Size(self):
        return self._Size
    @Size.setter
    def Size(self, size):
        propertyChange(self, 'Size', self._Size, size)
        self._Size = size
    @property
    def IsRead(self):
        return self._IsRead
    @IsRead.setter
    def IsRead(self, isread):
        propertyChange(self, 'IsRead', self._IsRead, isread)
        self._IsRead = isread
    @property
    def IsWrite(self):
        return self._IsWrite
    @IsWrite.setter
    def IsWrite(self, iswrite):
        propertyChange(self, 'IsWrite', self._IsWrite, iswrite)
        self._IsWrite = iswrite

    # XContentCreator
    def queryCreatableContentsInfo(self):
        print("DriveDocumentContent.queryCreatableContentsInfo():*************************")
        return self.CreatableContentsInfo
    def createNewContent(self, contentinfo):
        print("DriveDocumentContent.createNewContent():************************* %s" % contentinfo)
        pass

    # XPropertyContainer
    def addProperty(self, name, attribute, default):
        print("DriveOfficeContent.addProperty()")
    def removeProperty(self, name):
        print("DriveOfficeContent.removeProperty()")

     # XChild
    def getParent(self):
        print("DriveOfficeContent.getParent() ***********************************************")
        uri = getParentUri(self.ctx, self.Uri)
        identifier = ContentIdentifier(uri)
        return getContent(self.ctx, identifier)
    def setParent(self, parent):
        print("DriveOfficeContent.setParent() ***********************************************")
        raise NoSupportException('Parent can not be set', self)

    # XContent
    def getIdentifier(self):
        return ContentIdentifier(self.Uri)
    def getContentType(self):
        return self.ContentType
    def addContentEventListener(self, listener):
        if listener not in self.contentListeners:
            self.contentListeners.append(listener)
    def removeContentEventListener(self, listener):
        if listener in self.contentListeners:
            self.contentListeners.remove(listener)

    # XCommandProcessor2
    def createCommandIdentifier(self):
        return 0
    def execute(self, command, id, environment):
        try:
            result = None
            level = uno.getConstantByName("com.sun.star.logging.LogLevel.INFO")
            msg = "Command name: %s ..." % command.Name
            print("DriveOfficeContent.execute(): %s" % command.Name)
            if command.Name == 'getCommandInfo':
                print("DriveOfficeContent.getCommandInfo()?????????????????????????????????????????????????")
                result = CommandInfo(self._commandInfo)
            elif command.Name == 'getPropertySetInfo':
                result = PropertySetInfo(self._propertySetInfo, self._getCmisPropertySetInfo)
            elif command.Name == 'getPropertyValues':
                namedvalues = getPropertiesValues(self, command.Argument, self.Logger)
                print("DriveOfficeContent.getPropertyValues(): %s" % (namedvalues, ))
                result = Row(namedvalues)
            elif command.Name == 'setPropertyValues':
                result = setPropertiesValues(self, command.Argument, self.Logger)
            elif command.Name == 'open':
                print ("DriveOfficeContent.open(): %s" % command.Argument.Mode)
                sink = command.Argument.Sink
                if self.IsReadOnly and sink.queryInterface(uno.getTypeByName('com.sun.star.io.XActiveDataSink')):
                    msg += " ReadOnly mode selected ..."
                    sink.setInputStream(self._getInputStream())
                elif not self.IsReadOnly and sink.queryInterface(uno.getTypeByName('com.sun.star.io.XActiveDataStreamer')):
                    msg += " ReadWrite mode selected ..."
                    sink.setStream(self._getStream())
                result = None
            elif command.Name == 'createNewContent':
                print("DriveDocumentContent.execute(): createNewContent %s" % command.Argument)
            elif command.Name == 'insert':
                # The Insert command is only used to create a new document (File Save As)
                # it saves content from createNewContent from the parent folder
                input = command.Argument.Data
                replace = command.Argument.ReplaceExisting
                print("DriveOfficeContent.execute() insert %s" % (replace, ))
                if input.queryInterface(uno.getTypeByName('com.sun.star.io.XInputStream')):
                    sf = getSimpleFile(self.ctx)
                    target = getResourceLocation(self.ctx, '%s/%s' % (self.Uri.getScheme(), self.Id))
                    sf.writeFile(target, input)
                    self.MediaType = self._getMediaType(input)
                    input.closeInput()
                    self.Size = sf.getSize(target)
                    self.IsWrite = True
                    self.IsRead = True
                    ucp = getUcp(self.ctx, self.Uri.getUriReference())
                    self.addPropertiesChangeListener(('Id', 'IsWrite', 'IsRead', 'Title', 'Size'), ucp)
                    self.Id = self.Id
                    print("DriveOfficeContent.execute() insert %s - %s" % (self.Size, self.MediaType))
            elif command.Name == 'addProperty':
                print("DriveOfficeContent.addProperty():")
            elif command.Name == 'removeProperty':
                print("DriveOfficeContent.removeProperty():")
            elif command.Name == 'lock':
                print("DriveOfficeContent.lock()")
            elif command.Name == 'unlock':
                print("DriveOfficeContent.unlock()")
            elif command.Name == 'close':
                print("DriveOfficeContent.close()")
            elif command.Name == 'updateProperties':
                print("DriveOfficeContent.updateProperties()")
            elif command.Name == 'getAllVersions':
                print("DriveOfficeContent.getAllVersions()")
            elif command.Name == 'checkout':
                print("DriveOfficeContent.checkout()")
            elif command.Name == 'cancelCheckout':
                print("DriveOfficeContent.cancelCheckout()")
            elif command.Name == 'checkIn':
                print("DriveOfficeContent.checkin()")
            msg += " Done"
            self.Logger.logp(level, "DriveOfficeContent", "execute()", msg)
            return result
        except Exception as e:
            print("DriveOfficeContent.execute().Error: %s - %e" % (e, traceback.print_exc()))
    def abort(self, id):
        pass
    def releaseCommandIdentifier(self, id):
        pass

    def _getStream(self):
        sf = getSimpleFile(self.ctx)
        url = self._getUrl(sf)
        return sf.openFileReadWrite(url)

    def _getInputStream(self):
        sf = getSimpleFile(self.ctx)
        url = self._getUrl(sf)
        return sf.openFileRead(url)

    def _getUrl(self, sf):
        url = getResourceLocation(self.ctx, '%s/%s' % (self.Uri.getScheme(), self.Id))
        if not sf.exists(url):
            input = InputStream(self.ctx, self.Uri.getScheme(), self.UserName, self.Id, self.Size)
            sf.writeFile(url, input)
            input.closeInput()
            self.IsRead = True
        return url

    def _getMediaType(self, input):
        mediatype = "application/octet-stream"
        detection = self.ctx.ServiceManager.createInstance('com.sun.star.document.TypeDetection')
        descriptor = (getPropertyValue('InputStream', input), )
        format, dummy = detection.queryTypeByDescriptor(descriptor, True)
        if detection.hasByName(format):
            properties = detection.getByName(format)
            for property in properties:
                if property.Name == "MediaType":
                    mediatype = property.Value
        return mediatype

    def _getCommandInfo(self):
        commands = {}
        commands['getCommandInfo'] = getCommandInfo('getCommandInfo')
        commands['getPropertySetInfo'] = getCommandInfo('getPropertySetInfo')
        commands['getPropertyValues'] = getCommandInfo('getPropertyValues', '[]com.sun.star.beans.Property')
        commands['setPropertyValues'] = getCommandInfo('setPropertyValues', '[]com.sun.star.beans.Property')
        commands['addProperty'] = getCommandInfo('addProperty', 'com.sun.star.ucb.PropertyCommandArgument')
        commands['removeProperty'] = getCommandInfo('removeProperty', 'string')
        commands['open'] = getCommandInfo('open', 'com.sun.star.ucb.OpenCommandArgument2')
        commands['createNewContent'] = getCommandInfo('createNewContent', 'com.sun.star.ucb.ContentInfo')
        commands['insert'] = getCommandInfo('insert', 'com.sun.star.ucb.InsertCommandArgument')
#        commands['insert'] = getCommandInfo('insert', 'com.sun.star.ucb.InsertCommandArgument2')
#        commands['lock'] = getCommandInfo('lock')
#        commands['unlock'] = getCommandInfo('unlock')
#        commands['close'] = getCommandInfo('close')
        return commands
        
    def _updateCommandInfo(self):
        commands = {}
        commands['insert'] = getCommandInfo('insert', 'com.sun.star.ucb.InsertCommandArgument2')
        commands['checkout'] = getCommandInfo('checkout')
        commands['cancelCheckout'] = getCommandInfo('cancelCheckout')
        commands['checkin'] = getCommandInfo('checkin', 'com.sun.star.ucb.CheckinArgument')
        commands['updateProperties'] = getCommandInfo('updateProperties', '[]com.sun.star.document.CmisProperty')
        commands['getAllVersions'] = getCommandInfo('getAllVersions', '[]com.sun.star.document.CmisVersion')
        self._commandInfo.update(commands)

    def _getPropertySetInfo(self):
        properties = {}
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        properties['Id'] = getProperty('Id', 'string', bound | readonly)
        properties['ContentType'] = getProperty('ContentType', 'string', bound | readonly)
        properties['MediaType'] = getProperty('MediaType', 'string', bound)
        properties['IsDocument'] = getProperty('IsDocument', 'boolean', bound | readonly)
        properties['IsFolder'] = getProperty('IsFolder', 'boolean', bound | readonly)
        properties['Title'] = getProperty('Title', 'string', bound)
        properties['Size'] = getProperty('Size', 'long', bound | readonly)
        properties['DateModified'] = getProperty('DateModified', 'com.sun.star.util.DateTime', bound | readonly)
        properties['DateCreated'] = getProperty('DateCreated', 'com.sun.star.util.DateTime', bound | readonly)
        properties['IsReadOnly'] = getProperty('IsReadOnly', 'boolean', bound | readonly)
        properties['IsRead'] = getProperty('IsRead', 'boolean', bound)
        properties['BaseURI'] = getProperty('BaseURI', 'string', bound | readonly)
        properties['TargetURL'] = getProperty('TargetURL', 'string', bound | readonly)
        properties['TitleOnServer'] = getProperty('TitleOnServer', 'string', bound)
#        properties['CanCheckIn'] = getProperty('CanCheckIn', 'boolean', bound)
#        properties['CanCancelCheckOut'] = getProperty('CanCancelCheckOut', 'boolean', bound)
        properties['ObjectId'] = getProperty('ObjectId', 'string', bound | readonly)
        properties['CasePreservingURL'] = getProperty('CasePreservingURL', 'string', bound | readonly)
        properties['CreatableContentsInfo'] = getProperty('CreatableContentsInfo', '[]com.sun.star.ucb.ContentInfo', bound | readonly)
        properties['Author'] = getProperty('Author', 'string', bound)
        properties['Keywords'] = getProperty('Keywords', 'string', bound)
        properties['Subject'] = getProperty('Subject', 'string', bound)
        
        properties['IsHidden'] = getProperty('IsHidden', 'boolean', bound | readonly)
        properties['IsVolume'] = getProperty('IsVolume', 'boolean', bound | readonly)
        properties['IsRemote'] = getProperty('IsRemote', 'boolean', bound | readonly)
        properties['IsRemoveable'] = getProperty('IsRemoveable', 'boolean', bound | readonly)
        properties['IsFloppy'] = getProperty('IsFloppy', 'boolean', bound | readonly)
        properties['IsCompactDisc'] = getProperty('IsCompactDisc', 'boolean', bound | readonly)
        return properties

    def _getCmisPropertySetInfo(self):
        properties = {}
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        properties['CmisProperties'] = getProperty('CmisProperties', '[]com.sun.star.document.CmisProperty', bound | readonly)
        properties['IsVersionable'] = getProperty('IsVersionable', 'boolean', bound | readonly)
        properties['CanCheckOut'] = getProperty('CanCheckOut', 'boolean', bound)
        properties['CanCheckIn'] = getProperty('CanCheckIn', 'boolean', bound)
        properties['CanCancelCheckOut'] = getProperty('CanCancelCheckOut', 'boolean', bound)
        self._propertySetInfo.update(properties)
        self._updateCommandInfo()
        return properties

    def _getCmisProperties(self):
        properties = []
        properties.append(getCmisProperty('cmis:isVersionSeriesCheckedOut', 'isVersionSeriesCheckedOut', 'boolean', True, True, False, True, (), True))
        properties.append(getCmisProperty('cmis:title', 'title', 'string', True, True, False, True, (), 'nouveau titre'))
        return tuple(properties)

#        self._propertySetInfo.update({property.Name: property})
#        reason = uno.getConstantByName('com.sun.star.beans.PropertySetInfoChange.PROPERTY_INSERTED')
#        event = getPropertySetInfoChangeEvent(self, property.Name, reason)
#        for listener in self.propertyInfoListeners:
#            listener.propertySetInfoChange(event)

    def _getCreatableContentsInfo(self):
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        document = uno.getConstantByName('com.sun.star.ucb.ContentInfoAttribute.KIND_DOCUMENT')
        folder = uno.getConstantByName('com.sun.star.ucb.ContentInfoAttribute.KIND_FOLDER')
        foldertype = 'application/vnd.google-apps.folder'
        documenttype = 'application/vnd.oasis.opendocument'
        folderproperties = (getProperty('Title', 'string', bound), )
        documentproperties = (getProperty('Title', 'string', bound), )
        content = (getContentInfo(documenttype, document, documentproperties), )
        return content

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(DriveOfficeContent,                                                 # UNO object class
                                         g_ImplementationName,                                               # Implementation name
                                        (g_ImplementationName, 'com.sun.star.ucb.Content'))                  # List of implemented services
