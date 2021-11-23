#!/usr/bin/env python3
# Copyright 2021 afrikha
# See LICENSE file for licensing details.


import jinja2
import json
import logging
import os
from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import MaintenanceStatus, ActiveStatus, BlockedStatus
from charmhelpers.core import hookenv, host
import uuid


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
        sections_extra_config = {"databases": [], "pgbouncer": []}
        auth_user_dir = "/etc/pgbouncer/auth_user/"
        extra_dbs_dir = "/etc/pgbouncer/extra_dbs/"
        for unit in self._rel_get_remote_units('pgbouncer-extra-config'):
            if 'extra_db_config' in charm_config:
                self.prepare_folder(extra_dbs_dir)
                extra_dbs_conf = extra_dbs_dir + str(uuid.uuid4()) + '.ini'
                self.render_config(extra_dbs_conf,
                                   'extra_databases.ini.tmpl')
                sections_extra_config["databases"].append(extra_dbs_conf)

            if 'auth_user' in charm_config:
                if 'auth_query' in charm_config:
                    self.prepare_folder(auth_user_dir)
                    auth_user_conf = auth_user_dir + str(uuid.uuid4()) + '.ini'
                    self.render_config(auth_user_conf, 'auth_user.ini.tmpl')
                    sections_extra_config["pgbouncer"].append(auth_user_conf)
                else:
                    self.unit.status = BlockedStatus(
                        "auth_query needs to be configured when auth_user is set")
                    return
            remote.data[self.unit]['section_extra_parameters'] = json.dumps(sections_extra_config)

        self.unit.status = ActiveStatus("Unit is ready")

    def render_config(self, path, tmpl_name):
        """Render extra configuration files"""
        loader = jinja2.FileSystemLoader(
            os.path.join(hookenv.charm_dir(), 'src/templates'))
        env = jinja2.Environment(loader=loader)
        env.globals['config'] = self.framework.model.config
        template = env.get_template(tmpl_name)
        contents = template.render()
        if not os.path.exists(path):
            open(path, 'a').close()
        if contents.encode() != open(path, 'rb').read():
            host.write_file(path, contents.encode())

    def prepare_folder(self, dir):
        if not os.path.exists(dir):
            os.makedirs(dir)
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))


if __name__ == "__main__":
    main(CharmPgbouncerExtraConfig)
