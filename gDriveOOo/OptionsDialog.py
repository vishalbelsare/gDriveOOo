#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.awt import XContainerWindowEventHandler

from gdrive import getStringResource, getFileSequence, createService
from gdrive import getLoggerUrl, getLoggerSetting, setLoggerSetting, getLogger

from gdrive import getItem, getDbConnection, executeUserInsert, executeUpdateInsertItem
import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = 'com.gmail.prrvchr.extensions.gDriveOOo.OptionsDialog'


class OptionsDialog(unohelper.Base, XServiceInfo, XContainerWindowEventHandler):
    def __init__(self, ctx):
        try:
            self.ctx = ctx
            self.stringResource = getStringResource(self.ctx, None, 'OptionsDialog')
        except Exception as e:
            print("PyOptionsDialog.__init__().Error: %s - %s" % (e, traceback.print_exc()))

    # XContainerWindowEventHandler
    def callHandlerMethod(self, dialog, event, method):
        handled = False
        if method == 'external_event':
            if event == 'ok':
                self._saveSetting(dialog)
                handled = True
            elif event == 'back':
                self._loadSetting(dialog)
                handled = True
            elif event == 'initialize':
                self._loadSetting(dialog)
                handled = True
        elif method == 'Logger':
            self._doLogger(dialog, bool(event.Source.State))
            handled = True
        elif method == 'View':
            self._doView(dialog)
            handled = True
        elif method == 'Connect':
            self._doConnect(dialog)
            handled = True
        return handled
    def getSupportedMethodNames(self):
        return ('external_event', 'Logger', 'View', 'Connect')

    def _doConnect(self, dialog):
        try:
            print("PyOptionsDialog._doConnect() 1")
            #Need upload file here
            level = uno.getConstantByName("com.sun.star.logging.LogLevel.SEVERE")
            getLogger().logp(level, "OptionsDialog", "_doConnect()", "Test:")
            print("PyOptionsDialog._doConnect() 7")
        except Exception as e:
            print("PyOptionsDialog._doConnect().Error: %s - %s" % (e, traceback.print_exc()))

    def _getArgumentsFromResult(self, result):
        arguments = {}
        arguments['Scheme'] = result.getColumns().getByName('Scheme').getString()
        arguments['UserName'] = result.getColumns().getByName('UserName').getString()
        arguments['Id'] = result.getColumns().getByName('Id').getString()
        if result.getColumns().hasByName('ParentId'):
            arguments['ParentId'] = result.getColumns().getByName('ParentId').getString()
        else:
            arguments['ParentId'] = None
        arguments['Title'] = result.getColumns().getByName('Title').getString()
        arguments['MediaType'] = result.getColumns().getByName('MediaType').getString()
        arguments['DateCreated'] = result.getColumns().getByName('DateCreated').getTimestamp()
        arguments['DateModified'] = result.getColumns().getByName('DateModified').getTimestamp()
        arguments['Size'] = result.getColumns().getByName('Size').getLong()
        arguments['IsReadOnly'] = result.getColumns().getByName('IsReadOnly').getBoolean()
        arguments['CanRename'] = result.getColumns().getByName('CanRename').getBoolean()
        arguments['CanAddChild'] = result.getColumns().getByName('CanAddChild').getBoolean()
        arguments['IsInCache'] = result.getColumns().getByName('IsInCache').getBoolean()
        arguments['IsVersionable'] = result.getColumns().getByName('IsVersionable').getBoolean()
        arguments['BaseURI'] = result.getColumns().getByName('BaseURI').getString()
        arguments['TargetURL'] = result.getColumns().getByName('TargetURL').getString()
        arguments['TitleOnServer'] = result.getColumns().getByName('TitleOnServer').getString()
        arguments['CasePreservingURL'] = result.getColumns().getByName('CasePreservingURL').getString()
        return arguments

    def _loadSetting(self, dialog):
        self._loadLoggerSetting(dialog)

    def _saveSetting(self, dialog):
        self._saveLoggerSetting(dialog)

    def _doLogger(self, dialog, enabled):
        dialog.getControl('Label2').Model.Enabled = enabled
        dialog.getControl('ComboBox1').Model.Enabled = enabled
        dialog.getControl('OptionButton1').Model.Enabled = enabled
        dialog.getControl('OptionButton2').Model.Enabled = enabled
        dialog.getControl('CommandButton1').Model.Enabled = enabled

    def _doView(self, window):
        url = getLoggerUrl(self.ctx)
        length, sequence = getFileSequence(self.ctx, url)
        text = sequence.value.decode('utf-8')
        dialog = self._getLogDialog()
        dialog.Title = url
        dialog.getControl('TextField1').Text = text
        dialog.execute()
        dialog.dispose()

    def _getLogDialog(self):
        url = 'vnd.sun.star.script:gDriveOOo.LogDialog?location=application'
        return createService('com.sun.star.awt.DialogProvider', self.ctx).createDialog(url)

    def _loadLoggerSetting(self, dialog):
        enabled, index, handler = getLoggerSetting(self.ctx)
        dialog.getControl('CheckBox1').State = int(enabled)
        self._setLoggerLevel(dialog.getControl('ComboBox1'), index)
        dialog.getControl('OptionButton%s' % handler).State = 1
        self._doLogger(dialog, enabled)

    def _setLoggerLevel(self, control, index):
        name = control.Model.Name
        text = self.stringResource.resolveString('OptionsDialog.%s.StringItemList.%s' % (name, index))
        control.Text = text

    def _getLoggerLevel(self, control):
        name = control.Model.Name
        for index in range(control.ItemCount):
            text = self.stringResource.resolveString('OptionsDialog.%s.StringItemList.%s' % (name, index))
            if text == control.Text:
                break
        return index

    def _saveLoggerSetting(self, dialog):
        enabled = bool(dialog.getControl('CheckBox1').State)
        index = self._getLoggerLevel(dialog.getControl('ComboBox1'))
        handler = dialog.getControl('OptionButton1').State
        setLoggerSetting(self.ctx, enabled, index, handler)
        setLoggerSetting(self.ctx, enabled, index, handler)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(OptionsDialog,                             # UNO object class
                                         g_ImplementationName,                      # Implementation name
                                        (g_ImplementationName,))                    # List of implemented services
