#!/usr/bin/env python3
# Copyright 2021 afrikha
# See LICENSE file for licensing details.


import logging

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import MaintenanceStatus, ActiveStatus, BlockedStatus


logger = logging.getLogger(__name__)


class CharmPgbouncerExtraConfig(CharmBase):

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(
            self.on.install,
            self._on_install)
        self.framework.observe(
            self.on.config_changed,
            self._on_config_changed_or_upgrade)
        self.framework.observe(
            self.on.upgrade_charm,
            self._on_config_changed_or_upgrade)
        self.framework.observe(
            self.on.pgbouncer_extra_config_relation_joined,
            self._on_config_changed_or_upgrade)
        self.framework.observe(
            self.on.pgbouncer_extra_config_relation_changed,
            self._on_config_changed_or_upgrade)

    def _rel_get_remote_units(self, rel_name):
        """Get relations remote units"""
        return self.framework.model.get_relation(rel_name).units

    def _on_install(self, _):
        """Install hook execution"""
        self.unit.status = MaintenanceStatus(
            "This charm does not install any package")
        self.unit.status = ActiveStatus("Unit is ready")

    def _on_config_changed_or_upgrade(self, event):
        """Update on changed config or charm upgrade"""

        charm_config = self.framework.model.config
        remote = self.framework.model.relations.get('pgbouncer-extra-config')[0]
        for unit in self._rel_get_remote_units('pgbouncer-extra-config'):
            if 'extra_db_config' in charm_config:
                remote.data[self.unit]['extra_db_config'] = \
                    charm_config['extra_db_config']
            if 'auth_user' in charm_config:
                remote.data[self.unit]['auth_user'] = \
                    charm_config['auth_user']
                if 'auth_query' in charm_config:
                    remote.data[self.unit]['auth_query'] = \
                        charm_config['auth_query']
                else:
                    self.unit.status = BlockedStatus("auth_query needs"\
                    " to be configured when auth_user is set")
                    return
        self.unit.status = ActiveStatus("Unit is ready")


if __name__ == "__main__":
    main(CharmPgbouncerExtraConfig)
