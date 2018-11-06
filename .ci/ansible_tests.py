#!/usr/bin/env python
# Run tests/ansible/all.yml under Ansible and Ansible-Mitogen

import os
import sys

import ci_lib
from ci_lib import run


TESTS_DIR = os.path.join(ci_lib.GIT_ROOT, 'tests/ansible')
HOSTS_DIR = os.path.join(ci_lib.TMP, 'hosts')


with ci_lib.Fold('unit_tests'):
    os.environ['SKIP_MITOGEN'] = '1'
    ci_lib.run('./run_tests -v')


with ci_lib.Fold('docker_setup'):
    containers = ci_lib.make_containers()
    ci_lib.start_containers(containers)


with ci_lib.Fold('job_setup'):
    # Don't set -U as that will upgrade Paramiko to a non-2.6 compatible version.
    run("pip install -q ansible==%s", ci_lib.ANSIBLE_VERSION)

    os.chdir(TESTS_DIR)
    os.chmod('../data/docker/mitogen__has_sudo_pubkey.key', int('0600', 7))

    run("mkdir %s", HOSTS_DIR)
    run("ln -s %s/hosts/common-hosts %s", TESTS_DIR, HOSTS_DIR)

    with open(os.path.join(HOSTS_DIR, 'target'), 'w') as fp:
        fp.write('[test-targets]\n')
        fp.writelines(
            "%(name)s "
            "ansible_host=%(hostname)s "
            "ansible_port=%(port)s "
            "ansible_user=mitogen__has_sudo_nopw "
            "ansible_password=has_sudo_nopw_password"
            "\n"
            % container
            for container in containers
        )

    # Build the binaries.
    # run("make -C %s", TESTS_DIR)
    if not ci_lib.exists_in_path('sshpass'):
        run("sudo apt-get update")
        run("sudo apt-get install -y sshpass")


with ci_lib.Fold('ansible'):
    playbook = os.environ.get('PLAYBOOK', 'all.yml')
    run('/usr/bin/time ./run_ansible_playbook.py %s -i "%s" %s',
        playbook, HOSTS_DIR, ' '.join(sys.argv[1:]))
