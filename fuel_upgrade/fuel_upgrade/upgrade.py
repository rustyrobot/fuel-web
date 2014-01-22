#    Copyright 2013 Mirantis, Inc.
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


class Upgrade(object):

    def __init__(self):
        pass

    def run(self):
        self.before_upgrade()

        try:
            self.upgrade()
            self.after_upgrade()
        except Exception:
            self.rollback()

    def before_upgrade(self):
        self.check_upgrade_opportunity()
        self.shutdown_services()
        self.make_backup()

    def upgrade(self):
        """Run docker's container deployment
        """
        pass

    def after_upgrade(self):
        self.run_services()
        self.check_health()

    def make_backup(self):
        pass

    def shutdown_services(self):
        pass

    def check_upgrade_opportunity(self):
        pass

    def run_services(self):
        pass

    def check_health(self):
        pass

    def rollback(self):
        pass
