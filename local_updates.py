#!/usr/bin/python

import sys
import subprocess
import urllib
import json
import os
import re
import logging

try:
    from xmlrpclib import ServerProxy
except:
    from xmlrpc.client import ServerProxy

def send_port(dest_ip, dest_port, forwarding_port):
    s = ServerProxy('http://{}:{}'.format(dest_ip, dest_port))
    try:
        s.update_vpn_port(forwarding_port)
    except Exception as e:
        logging.critical('RPC call failed to http://{}:{} - {}'.format(dest_ip, dest_port, e))

def get_forwarded_port(local_ip_url, cred_url, client_id):
    logging.info('reading VPN local IP from {}'.format(local_ip_url))
    local_ip_file = urllib.urlopen(local_ip_url)
    local_ip = local_ip_file.readline().strip()
    local_ip_file.close()

    logging.info('reading PIA credentials from {}'.format(cred_url))
    cred_file = urllib.urlopen(cred_url)
    [user_name, passwd] = [l.strip() for l in cred_file.readlines()]
    cred_file.close()

    # set up the port forward request to PIA
    logging.info('requesting forwarding port from PIA')
    # note: i use curl rather than urllib because it has the crucial
    # --interface option, allowing us to source-route the request over the vpn
    response = subprocess.check_output(['curl', '-s', '--interface', local_ip,
        '-d', 'client_id={}'.format(client_id),
        '-d', 'user={}'.format(user_name),
        '-d', 'pass={}'.format(passwd),
        '-d', 'local_ip={}'.format(local_ip),
        'https://www.privateinternetaccess.com/vpninfo/port_forward_assignment'])

    # read the response, hopefully it worked. The form is as follows:
    # {"port":37542}
    port = int(json.loads(response)['port'])
    logging.info('success: PIA gives us {:d}'.format(port))
    return port

port_filename_t = 'forwarded.port'
def vpn_port_changed(port, config_dir):
    assert(port > 0)

    core_conf_file = open(os.path.join(config_dir, 'core.conf'))
    # skip over initial turd
    logging.info('parsing deluge core.conf')
    while core_conf_file.read(1) != '}':
        pass
    core_conf_json = json.loads(core_conf_file.read())
    core_conf_file.close()
    deluged_port = core_conf_json['daemon_port']
    logging.debug('found daemon_port = {}'.format(deluged_port))

    logging.info('reading deluged user/pass from auth file')
    auth_file = open(os.path.join(config_dir, 'auth'))
    (username, password) = re.match('^([^:]+):([^:]+):', auth_file.readline()).group(1, 2)
    logging.debug('username = {} : pass = {}'.format(username, password))
    auth_file.close()

    logging.info('writing the port to a file if it has changed')
    port_filename = os.path.join(config_dir, port_filename_t)
    oldport = 0
    try:
        port_file = open(port_filename, 'r')
        oldport = int(port_file.readline().strip())
        port_file.close()
    except Exception as e:
        logging.error('problem reading cached port file: {}'.format(e))
        logging.warning('continuing anyway')

    if oldport == port:
        logging.info('Note: port {} is unchanged from cached value.'.format(port))
    else:
        logging.info('Note: new port {} is different from cached value of {}.'.format(port, oldport))
        try:
            logging.debug('writing the port cache file')
            port_file = open(port_filename, 'w')
            port_file.write('{}\n'.format(port))
            port_file.close()
        except Exception as e:
            logging.error('problem writing cached port file: {}'.format(e))
            logging.warning('continuing anyway')

    # also  update deluged's port if it is running
    logging.info('updating deluge configuration')
    deluge_cmd = ['deluge-console', '-c', config_dir, 'connect 127.0.0.1:{} {} {}; config -s listen_ports ({:d}, {:d})'.format(deluged_port, username, password, port, port)]
    logging.debug('> "{}"'.format('" "'.join(deluge_cmd)))
    deluge_rc = subprocess.run(deluge_cmd)
    try:
        deluge_rc.check_returncode()
    except subprocess.CalledProcessError as e:
        logging.critical('attempt failed to update deluge config: deluge-console returned {}: {}'.format(rc.returncode, rc.output))
        raise

if __name__ == '__main__':
    vpn_ip_changed(sys.argv[1])

