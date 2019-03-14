# Copyright (c) 2018 NEC, Corp.
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

import sys

from oslo_config import cfg
from oslo_upgradecheck import upgradecheck

from congress.db import api as db


CONF = cfg.CONF


class Checks(upgradecheck.UpgradeCommands):

    """Contains upgrade checks

    Various upgrade checks should be added as separate methods in this class
    and added to _upgrade_checks tuple.
    """

    def _check_monasca_webhook_driver(self):
        """Check existence of monasca webhook datasource"""
        session = db.get_session()
        result = session.execute(
            "SELECT count(*) FROM datasources WHERE driver = 'monasca_webhook'"
        ).scalar()
        if result == 0:
            return upgradecheck.Result(
                upgradecheck.Code.SUCCESS,
                'No currently configured data source uses the Monasca Webhook '
                'data source driver, which contains backward-incompatible '
                'schema changes.')
        else:
            return upgradecheck.Result(
                upgradecheck.Code.WARNING,
                'There are currently {} configured data source which use the '
                'Monasca Webhook data source driver. Because this version of '
                'Congress includes backward-incompatible schema changes to '
                'the driver, Congress policies referring to Monasca Webhook '
                'data may need to be adapted to the new schema.'.format(
                    result))

    _upgrade_checks = (
        ('Monasca Webhook Driver', _check_monasca_webhook_driver),
    )


def main():
    return upgradecheck.main(
        CONF, project='congress', upgrade_command=Checks())


if __name__ == '__main__':
    sys.exit(main())
