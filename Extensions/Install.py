#  ATContentTypes http://sf.net/projects/collective/
#  Archetypes reimplementation of the CMF core types
#  Copyright (c) 2003-2004 AT Content Types development team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA 
#
"""

$Id: Install.py,v 1.3 2004/03/16 20:33:23 tiran Exp $
""" 
__author__  = ''
__docformat__ = 'restructuredtext'

from Products.Archetypes import listTypes
from Products.Archetypes.Extensions.utils import installTypes, install_subskin
from Products.CMFCore.utils import getToolByName
from StringIO import StringIO
from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
from Acquisition import aq_base

from Products.Archetypes.interfaces.base import IBaseFolder, IBaseContent
from Products.ATContentTypes.interfaces.IATTopic import IATTopic, IATTopicCriterion
from Products.ATContentTypes.interfaces.IATContentType import IATContentType

from Products.ATContentTypes.config import *

def install(self):
    out = StringIO()

    typeInfo = listTypes(PROJECTNAME)
    installTypes(self, out,
                 typeInfo,
                 PROJECTNAME)

    install_subskin(self, out, GLOBALS)

    #register folderish classes in use_folder_contents
    props=getToolByName(self,'portal_properties').site_properties
    use_folder_tabs=list(props.use_folder_tabs)

    print >> out, 'adding classes to use_folder_tabs:'
    for cl in typeInfo:
        print >> out,  'type:',cl['klass'].portal_type
        if cl['klass'].isPrincipiaFolderish:
            use_folder_tabs.append(cl['klass'].portal_type)
    
    print >> out, 'Successfully installed %s' % PROJECTNAME
    
    # register switch methods to toggle old plonetypes on/off
    portal=getToolByName(self,'portal_url').getPortalObject()
    manage_addExternalMethod(portal,'switch_old_plone_types_off',    
        'switch_old_plone_types_off',    
        PROJECTNAME+'.switchOldPloneTypes', 
        'switch_old_plone_types_off')    
    manage_addExternalMethod(portal,'switch_old_plone_types_on',    
        'switch_old_plone_types_on',    
        PROJECTNAME+'.switchOldPloneTypes', 
        'switch_old_plone_types_on')    

    # changing workflow
    setupWorkflows(self, typeInfo, out)

    return out.getvalue()

def uninstall(self):
    out = StringIO()
    classes=listTypes(PROJECTNAME)

    #unregister folderish classes in use_folder_contents
    props = getToolByName(self,'portal_properties').site_properties
    use_folder_tabs = list(props.use_folder_tabs)

    print >> out, 'removing classes from use_folder_tabs:'
    for cl in classes:
        print >> out,  'type:', cl['klass'].portal_type
        if cl['klass'].isPrincipiaFolderish:
            if cl['klass'].portal_type in use_folder_tabs:
                use_folder_tabs.remove(cl['klass'].portal_type)

    props.use_folder_tabs=tuple(use_folder_tabs)
    
    # remove external methods for toggling between old and new types
    portal=getToolByName(self,'portal_url').getPortalObject()
    for script in ('switch_old_plone_types_on', 'switch_old_plone_types_off'):
        if hasattr(aq_base(portal), script):
            portal.manage_delObjects(ids=[script,])
    
    return out.getvalue()

def setupWorkflows(self, typeInfo, out):
    wftool = getToolByName(self, 'portal_workflow')
    for t in typeInfo:
        klass       = t['klass']
        portal_type = t['portal_type']
        if IBaseFolder.isImplementedByInstancesOf(klass) and not \
          IATTopic.isImplementedByInstancesOf(klass):
            print >>out, 'Assigning workflow %s with portal type %s' % (WORKFLOW_FOLDER or 'NONE', portal_type )
            wftool.setChainForPortalTypes(portal_type, WORKFLOW_FOLDER)
        elif IATTopic.isImplementedByInstancesOf(klass):
            print >>out, 'Assigning workflow %s with portal type %s' % (WORKFLOW_TOPIC or 'NONE', portal_type )
            wftool.setChainForPortalTypes(portal_type, WORKFLOW_TOPIC)
        elif IATTopicCriterion.isImplementedByInstancesOf(klass):
            print >>out, 'Assigning workflow %s with portal type %s' % (WORKFLOW_CRITERIA or 'NONE', portal_type )
            wftool.setChainForPortalTypes(portal_type, WORKFLOW_CRITERIA)
        elif IATContentType.isImplementedByInstancesOf(klass):
            print >>out, 'Assigning workflow %s with portal type %s' % (WORKFLOW_DEFAULT or 'NONE', portal_type )
            wftool.setChainForPortalTypes(portal_type, WORKFLOW_DEFAULT)
        else:
            print >>out, 'NOT assigning %s' % portal_type
