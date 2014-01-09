#!/usr/bin/env python
# Copyright (c) 2013 VMware, Inc. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import argparse
import ldap
import sys
import time
import uuid

import ovs.daemon
import ovs.vlog
vlog = ovs.vlog.Vlog(__name__)


#NOTE: LDAP filters: http://tinyurl.com/la9jw7m

LDAP_URI = 'ldap://ad-server:389'
BASE_DN = 'dc=corp,dc=example,dc=com'
BIND_USER = 'cn=administrator,cn=Users' + ',' + BASE_DN
BIND_PW = 'p@ssw0rd'


class UserGroupDataModel(object):
    """An in-memory data model.
    """

    def __init__(self):
        self.items = {}  # {uuid: (user, group)}
        self.by_user = {}  # {user: {group:uuid}}

    def get_items(self):
        """Get items in model.

        Returns: A dict of {id, item} for all items in model.
        """
        return self.items

    def get_item(self, id_):
        """Retrieve item with id id_ from model.

        Args:
            id_: The ID of the item to retrieve.

        Returns:
             The matching item or None if item with id_ does not exist.
        """
        return self.items.get(id_)

    def update_from_ad(self):
        """Fetch user group info from AD and update model.

        Raises:
            ldap.INVALID_CREDENTIALS
            XXX: probably a bunch of ther ldap exceptions
        """
        # TODO(pjb): rewrite to be scalable, robust
        #vlog.dbg('Updating users from AD')
        l = ldap.initialize(LDAP_URI)
        l.simple_bind_s(BIND_USER, BIND_PW)

        ret = l.search_s('cn=Users,%s' % BASE_DN, ldap.SCOPE_SUBTREE,
                         '(&(objectCategory=person)(objectClass=user))')
        user_dns = [(u[1]['sAMAccountName'][0], u[0]) for u in ret]

        users_to_del = set(self.by_user.keys()) - set([u[0] for u in user_dns])
        for user in users_to_del:
            num_groups = len(self.by_user[user])
            vlog.info("User '%s' deleted (was in %s group%s)"
                      % (user, num_groups, '' if num_groups == 1 else 's'))
            ids = self.by_user.pop(user).values()
            for i in ids:
                del self.items[i]

        for user, dn in user_dns:
            filter_ = '(member:1.2.840.113556.1.4.1941:= %s)' % dn
            ret = l.search_s('cn=Users,%s' % BASE_DN, ldap.SCOPE_SUBTREE,
                             filter_)
            new_groups = set([r[1]['cn'][0] for r in ret])

            old_groups = set(self.by_user.get(user, {}).keys())
            membership_to_del = old_groups - new_groups
            membership_to_add = new_groups - old_groups

            for group in membership_to_del:
                id_ = self.by_user[user].pop(group)
                vlog.info("User '%s' removed from group '%s' (%s)"
                          % (user, group, id_))
                del self.items[id_]
            for group in membership_to_add:
                new_id = str(uuid.uuid4())
                self.by_user.setdefault(user, {})[group] = new_id
                vlog.info("User '%s' added to group '%s' (%s)"
                          % (user, group, new_id))
                self.items[new_id] = (user, group)


def main():
    parser = argparse.ArgumentParser()
    ovs.vlog.add_args(parser)
    args = parser.parse_args()
    ovs.vlog.handle_args(args)

    model = UserGroupDataModel()

    vlog.info("Starting AD sync service")
    while True:
        model.update_from_ad()
        time.sleep(3)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        vlog.exception("traceback")
        sys.exit(ovs.daemon.RESTART_EXIT_CODE)
