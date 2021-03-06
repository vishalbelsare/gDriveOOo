#!
# -*- coding: utf_8 -*-

from .dbtools import getItemFromResult


def selectRoot(connection, username):
    retrived, root = False, {}
    select = connection.prepareCall('CALL "selectRoot"(?)')
    select.setString(1, username)
    result = select.executeQuery()
    if result.next():
        retrived, root = True, getItemFromResult(result)
    select.close()
    return retrived, username, root

def mergeRoot(connection, username, item):
    retrived, root = False, {}
    merge = connection.prepareCall('CALL "mergeRoot"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    merge.setString(1, username)
    _setCallParameters(merge, item, 2)
    result = merge.executeQuery()
    if result.next():
        retrived, root = True, getItemFromResult(result)
    merge.close()
    return retrived, root

def selectItem(connection, id):
    retrived, item = False, {}
    select = connection.prepareCall('CALL "selectItem"(?)')
    select.setString(1, id)
    result = select.executeQuery()
    if result.next():
        retrived, item = True, getItemFromResult(result)
    select.close()
    return retrived, item

def insertItem(connection, item):
    retrived, item = False, {}
    insert = connection.prepareCall('CALL "insertItem"(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    _setCallParameters(insert, item)
    result = insert.executeQuery()
    if result.next():
        retrived, item = True, getItemFromResult(result)
    insert.close()
    return retrived, item

def mergeItem(merge, item):
    _setCallParameters(merge, item)
    merge.execute()
    return merge.getLong(11)

# Call Parameter:
# IN(Id, Title, DateCreated, DateModified, MediaType, IsReadOnly, CanRename, CanAddChild, Size, IsVersionable)
# OUT(NumRow)
def _setCallParameters(call, item, index=1):
    call.setString(index, item['Id'])
    index += 1
    call.setString(index, item['Title'])
    index += 1
    call.setTimestamp(index, item['DateCreated'])
    index += 1
    call.setTimestamp(index, item['DateModified'])
    index += 1
    call.setString(index, item['MediaType'])
    index += 1
    call.setBoolean(index, item['IsReadOnly'])
    index += 1
    call.setBoolean(index, item['CanRename'])
    index += 1
    call.setBoolean(index, item['IsFolder'])
    index += 1
    call.setLong(index, item['Size'])
    index += 1
    call.setBoolean(index, item['IsVersionable'])
