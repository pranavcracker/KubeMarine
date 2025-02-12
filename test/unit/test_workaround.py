#!/usr/bin/env python3
# Copyright 2021-2022 NetCracker Technology Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest

from kubemarine import demo
from paramiko.ssh_exception import SSHException

ETCD_LEADER_CHANGED_MESSAGE = 'Error from server: rpc error: code = Unavailable desc = etcdserver: leader changed'


class TestUnexpectedErrors(unittest.TestCase):

    def test_etcd_leader_changed_workaround(self):
        cluster = demo.new_cluster(demo.generate_inventory(**demo.FULLHA))

        # to increase test speed, let's override global workaround timeout value
        cluster.globals['workaround']['timeout'] = 0

        command = ['kubectl describe nodes']

        bad_results = demo.create_nodegroup_result(cluster.nodes['master'], code=-1, stderr=ETCD_LEADER_CHANGED_MESSAGE)
        good_results = demo.create_nodegroup_result(cluster.nodes['master'], stdout='Kubernetes master is running at %s'
                                                                                    % cluster.inventory['cluster_name'])

        cluster.fake_shell.add(bad_results, 'sudo', command, usage_limit=1)
        cluster.fake_shell.add(good_results, 'sudo', command)

        results = cluster.nodes['master'].get_any_member().sudo('kubectl describe nodes')

        for conn, result in results.items():
            self.assertIn('is running', result.stdout, msg="After an unsuccessful attempt, the workaround mechanism "
                                                           "should have worked and got the right result, but it seems "
                                                           "something went wrong")

    def test_encountered_rsa_key(self):
        cluster = demo.new_cluster(demo.generate_inventory(**demo.FULLHA))

        # to increase test speed, let's override global workaround timeout value
        cluster.globals['workaround']['timeout'] = 0

        command = ['kubectl describe nodes']

        bad_results = demo.create_exception_result(cluster.nodes['master'],
                                                   exception=SSHException('encountered RSA key, expected OPENSSH key'))
        good_results = demo.create_nodegroup_result(cluster.nodes['master'], stdout='Kubernetes master is running at %s'
                                                                                    % cluster.inventory['cluster_name'])

        cluster.fake_shell.add(bad_results, 'sudo', command, usage_limit=1)
        cluster.fake_shell.add(good_results, 'sudo', command)
        cluster.fake_shell.add(demo.create_nodegroup_result(cluster.nodes['all'], stdout='example result'),
                               'run', ["sudo -S -p '[sudo] password: ' last reboot"])

        results = cluster.nodes['master'].get_any_member().sudo('kubectl describe nodes')

        for conn, result in results.items():
            self.assertIn('is running', result.stdout, msg="After an unsuccessful attempt, the workaround mechanism "
                                                           "should have worked and got the right result, but it seems "
                                                           "something went wrong")


if __name__ == '__main__':
    unittest.main()
