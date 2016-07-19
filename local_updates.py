#!/usr/bin/python

import sys
import subprocess
import urllib.parse, urllib.request
import json

def vpn_ip_changed(local_ip):
    print('reading PIA credentials')
    # read privateinternetaccess credentials
    cred_file = open('/etc/openvpn/pia.cred', 'r')
    [user_name, passwd] = [l.strip() for l in cred_file.readlines()]
    # client id is an id number to identify this host within my account
    client_id_file = open('/etc/openvpn/pia.client_id', 'r')
    client_id = client_id_file.readline().strip()
    print('using client_id: {}'.format(client_id))

    # set up the port forward request to PIA
    print('requesting forwarding port from PIA')
    params = urllib.parse.urlencode({'user': user_name, 'pass': passwd,
        'client_id': client_id, 'local_ip': local_ip}).encode('ascii')
    request = urllib.request.Request('https://www.privateinternetaccess.com/vpninfo/port_forward_assignment', params)

    # read the response, hopefully it worked. The form is as follows:
    # {"port":37542}
    port = 6112
    with urllib.request.urlopen(request) as response:
        j = response.read().decode('utf-8')
        port = int(json.loads(j)['port'])
        print('success: PIA gives us {:d}'.format(port))
    port_change(port)

def port_change(port):
    # write the port to a file if it has changed.
    port_file = open('/etc/openvpn/portforward', 'r')
    oldport = 0
    try:
        oldport = int(port_file.readline().strip())
    except:
        pass
    port_file.close()

    if oldport == port:
        print('port {} is unchanged from cached value. stopping'.format(port))
        return

    print('port changed from cached value ({}). updating cache'.format(oldport))
    port_file = open('/etc/openvpn/portforward', 'w')
    port_file.write('{}\n'.format(port))
    port_file.close()

    # also  update deluged's port if it is running
    rc = subprocess.run(['systemctl', 'is-active', 'deluged.service'], stdout=subprocess.PIPE, universal_newlines=True)
    if rc.stdout.strip() == 'active':
        print('updating deluge configuration')
        deluge_rc = subprocess.run(['deluge-console', '-c', '/srv/mediad/.config/deluge', 'config -s listen_ports ({:d}, {:d})'.format(port, port)])
        deluge_rc.check_returncode()

if __name__ == '__main__':
    vpn_ip_changed(sys.argv[1])

