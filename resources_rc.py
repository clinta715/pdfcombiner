# -*- coding: utf-8 -*-

# Resource object code
#
# Created by: The Resource Compiler for PyQt5 (Qt v5.15.14)
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore

qt_resource_data = b"\
\x00\x00\x00\x1c\
\x5b\
\x41\x64\x64\x20\x61\x20\x50\x44\x46\x20\x69\x63\x6f\x6e\x20\x69\
\x6d\x61\x67\x65\x20\x68\x65\x72\x65\x5d\x0a\
"

qt_resource_name = b"\
\x00\x05\
\x00\x6f\xa6\x53\
\x00\x69\
\x00\x63\x00\x6f\x00\x6e\x00\x73\
\x00\x0c\
\x08\xb4\xdc\xa7\
\x00\x70\
\x00\x64\x00\x66\x00\x5f\x00\x69\x00\x63\x00\x6f\x00\x6e\x00\x2e\x00\x70\x00\x6e\x00\x67\
"

qt_resource_struct_v1 = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x02\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03\
\x00\x00\x00\x10\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
"

qt_resource_struct_v2 = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x10\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
\x00\x00\x01\x94\xd7\x49\x6a\xcd\
"

qt_version = [int(v) for v in QtCore.qVersion().split('.')]
if qt_version < [5, 8, 0]:
    rcc_version = 1
    qt_resource_struct = qt_resource_struct_v1
else:
    rcc_version = 2
    qt_resource_struct = qt_resource_struct_v2

def qInitResources():
    QtCore.qRegisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()
