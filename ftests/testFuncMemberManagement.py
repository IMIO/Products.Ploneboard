import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFMember.tests import CMFMemberTestCase
from Products.CMFCore.utils import getToolByName
from Interface.Verify import verifyClass
from AccessControl.SecurityManagement import newSecurityManager

import Products.CMFMember
from Products.CMFMember.MemberDataContainer import MemberDataContainer
from Products.CMFMember.Member import Member as MemberData

ZopeTestCase.utils.startZServer()

# for functional testing
from mechanize import Browser
from urllib import urlencode
from urlparse import urlparse
import pullparser
import re

default_user = CMFMemberTestCase.default_user
_d = {'__ac_name': default_user,
      '__ac_password': 'password'}

class TestFuncMemberManagement(ZopeTestCase.Functional, CMFMemberTestCase.CMFMemberTestCase):

    def afterSetUp(self):
        self.b = Browser()
        self.memberdata_url = self.portal.portal_memberdata.absolute_url()
        self.portal_url = self.portal.absolute_url()
        CMFMemberTestCase.CMFMemberTestCase.afterSetUp(self)
        self.addUsers()
 
    def testManageOrphansTab(self):
        #set an email to have a Member object created
        tmpUser = self.membership.getMemberById(self.portal_user_info['id'])
        self.failUnless(tmpUser)
        tmpUser.setMemberProperties({'email': 'foo@bar.com'})
        #check that we don't have any orphans before we begin
        noMembers = self.memberdata.getMemberDataContents()[0]
        self.failIf(noMembers['member_count'] == 0)
        self.assertEqual(noMembers['orphan_count'], 0)
        #delete the user in acl_users and check if we have one orphan
        self.portal.acl_users.userFolderDelUsers( [self.portal_user_info['id']] )
        #load portal_memberdata/folder_contents
        page = self.b.open(self.memberdata_url + '/folder_contents', urlencode(_d))
        noMembers = self.memberdata.getMemberDataContents()[0]
        self.assertEqual(noMembers['orphan_count'], 1)
        manageOrphans = self.b.follow_link(url_regex=re.compile("manage_orphans"), nr=0)
        self.b.select_form('manage_orphans')
        destination = self.b.open(self.b.click('form.button.PruneOrphans'))
        noMembers = self.memberdata.getMemberDataContents()[0]
        self.assertEqual(noMembers['orphan_count'], 0)

    def testAddMemberDataAnonymous(self):
        page = self.b.open(self.portal_url + '/index_html')        
        p = pullparser.PullParser(page)
        # now we shouldn't have a view tab if right permission is set on MemberDataContainer
        # and or invoke_factory method of it.
        self.failIf(self.getTheTag(p, "li",**{'id':'contentview-view'}))

    def testPloneControlPanel(self):
        # test for issue 21
        # login
        self.b.open(self.portal_url, data=urlencode(_d))
        # go to controlpanel
        page = self.b.open(self.portal_url + '/plone_control_panel')
        # check if we have our link
        try:
            self.b.find_link(text_regex=re.compile("CMFMember control"))
        except:
            self.fail('No CMFMember control link in plone control panel')

    def testAddModifyMember(self):
        # checking in particular to see if the temporary member_catalog
        # entry gets cleaned up

        self.fail('This test fails all others after the commit, verify it by commenting this line.')
        mcat = self.portal.member_catalog
        # login
        self.b.open(self.portal_url, data=urlencode(_d))
        page = self.b.open(self.memberdata_url + '/createObject',
                           data=urlencode({'type_name':'Member'}))
        get_transaction().commit(1)

        self.b.select_form('edit_form')
        # get autogenerated id
        action = self.b.action
        tmp_id = action[action.find('member.'):action.find('/base_edit')]
        real_id = 'test1'
        cat_ids = [brain.id for brain in mcat()]
        self.failUnless(tmp_id in cat_ids)
        self.failIf(real_id in cat_ids)

        self.b['id'] = real_id
        self.b['fullname'] = real_id
        self.b['email'] = 'test@example.com'
        self.b['password'] = 'secret'
        self.b['confirm_password'] = 'secret'
        destination = self.b.open(self.b.click())

        cat_ids = [brain.id for brain in mcat()]
        self.failUnless(real_id in cat_ids)
        self.failIf(tmp_id in cat_ids)


if __name__ == '__main__':
    framework(verbosity=1)
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestFuncMemberManagement))
        return suite
