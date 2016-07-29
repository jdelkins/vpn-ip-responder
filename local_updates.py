#!/usr/bin/python

import sys
import subprocess
import urllib.parse, urllib.request
import json
import os

def get_forwarded_port(local_ip, cred_filename, client_id_filename):
    # read privateinternetaccess credentials
    print('reading PIA credentials from {}'.format(cred_filename))
    cred_file = open(cred_filename, 'r')
    [user_name, passwd] = [l.strip() for l in cred_file.readlines()]
    cred_file.close()

    # client id is an id number to identify this host within my account
    client_id_file = open(client_id_filename, 'r')
    client_id = client_id_file.readline().strip()
    print('got client_id {} from {}'.format(client_id, client_id_filename))
    client_id_file.close()

    # set up the port forward request to PIA
    print('requesting forwarding port from PIA')
    params = urllib.parse.urlencode({'user': user_name, 'pass': passwd,
        'client_id': client_id, 'local_ip': local_ip}).encode('ascii')
    request = urllib.request.Request('https://www.privateinternetaccess.com/vpninfo/port_forward_assignment', params)

    # read the response, hopefully it worked. The form is as follows:
    # {"port":37542}
    port = 0
    with urllib.request.urlopen(request) as response:
        j = response.read().decode('utf-8')
        port = int(json.loads(j)['port'])
        print('success: PIA gives us {:d}'.format(port))
    return port

port_filename_t = 'forwarded.port'
def vpn_port_changed(port, config_dir, deluged_port):
    # write the port to a file if it has changed.
    port_filename = os.path.join(config_dir, port_filename_t)
    oldport = 0
    try:
        port_file = open(port_filename, 'r')
        oldport = int(port_file.readline().strip())
        port_file.close()
    except Exception as e:
        print('Error: problem reading cached port file: {}'.format(e))
        print('Continuing anyway')

    if oldport == port:
        print('Note: port {} is unchanged from cached value.'.format(port))
    else:
        print('Note: new port {} is different from cached value of {}.'.format(port, oldport))
        try:
            port_file = open(port_filename, 'w')
            port_file.write('{}\n'.format(port))
            port_file.close()
        except Exception as e:
            print('Error: problem writing cached port file: {}'.format(e))
            print('Continuing anyway')

    # also  update deluged's port if it is running
    print('Updating deluge configuration')
    deluge_rc = subprocess.run(['deluge-console', '-c', config_dir, 'connect 127.0.0.1:{}'.format(deluged_port), 'config -s listen_ports ({:d}, {:d})'.format(port, port)])
    deluge_rc.check_returncode()

if __name__ == '__main__':
    vpn_ip_changed(sys.argv[1])

