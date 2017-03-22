#!/bin/sh

export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/root/bin

exec >> /var/log/vpn-ip-responder.log
exec 2>&1

# are we being called from openvpn's route-up? (if not, it's from cron)
if [ -n "$ifconfig_local" ]; then
	echo "Called from openvpn"
	# dump environment for debugging purposes
	#env

	# stash local ip address
	echo "$ifconfig_local" >/usr/local/vpn-ip-responder/pia.ip
else
	echo "Called from cron"
fi

/usr/local/bin/python2.7 /usr/local/vpn-ip-responder/vpn_port_rpcclient \
	--client-id      /usr/local/vpn-ip-responder/pia.client_id \
	--local-ip-url   /usr/local/vpn-ip-responder/pia.ip \
	--credentials-file /var/etc/openvpn/client3.up \
	--server-ip 10.2.1.13 --server-port 8108 \
	--logging /var/log/vpn-ip-responder.log \
	--sleep 15
