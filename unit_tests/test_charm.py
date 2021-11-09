# Copyright 2021 pguimaraes
# See LICENSE file for licensing details.

import unittest
from ops.model import Relation, BlockedStatus
from ops.testing import Harness
from src.charm import CharmPgbouncerExtraConfig



class TestCharm(unittest.TestCase):

    def setUp(self):
        self.harness = Harness(CharmPgbouncerExtraConfig)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        self.harness.set_leader(True)
        self.model = self.harness.model
        self.pooler = \
            self.harness.add_relation('pgbouncer-extra-config', 'pgbouncer')
        self.harness.add_relation_unit(self.pooler, 'pgbouncer/0')
       
    def test_config_changed(self):
        conf_dict = {
          "extra_db_config": "mydb_primary = \
           host=125.25.32.52  port=5432 dbname=mydb",
          "auth_user": "test_auth",
          "auth_query": "SELECT usename, passwd FROM \
           pg_shadow WHERE usename = $1 ;"
        }
        self.harness.update_config(conf_dict)
        rel = self.model.get_relation('pgbouncer-extra-config', 0)
        self.assertIsInstance(rel, Relation)
        self.assertEqual(
            rel.data[self.model.unit], conf_dict)

    def test_blocked_status(self):
        self.harness.update_config(unset=["auth_query"])
        conf_dict = {
          "extra_db_config": "mydb_primary = \
           host=125.25.32.52  port=5432 dbname=mydb",
          "auth_user": "test_auth",
        }
        self.harness.update_config(conf_dict)
        self.harness.charm.on.update_status.emit()
        self.assertEqual(
            self.harness.charm.unit.status.message,
            "auth_query needs"\
             " to be configured when auth_user is set")
        self.assertIsInstance(
            self.harness.charm.unit.status,
            BlockedStatus)

