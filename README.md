VPN_IP_RESPONDER
================

This is some hackery to solve a small problem with my home netowrk:

I have a pfsense router as my home perimeter firewall. I have a VPN
client connection configured on that box to a vpn service provider. The
connection goes up and down as vpn's tend to do, and I also change the
server ip occasionally for various reasons.

I have a virtual machine which bascially serves as my "home seedbox". It has
the media NAS shadow mounted. I configured pfsense to route all traffic from
this VM's ip through the OpenVPN gateway (or block it if the gw is down).

The particular vpn service provider I use (PIA) gives a private network address
and NATs its VPN clients, blocking (by default) all incoming connections. You
can, however, set up dynamic port forwarding through an http POST request knock
procedure. The knock procedure requires knowing the local private ip
configured, plus the login credentials of the account.

The allocated forwarding port expires after a while, so you have to refresh it
hourly or so.

I run deluge on the VM. Deluge needs to know the dynamically forwarded port
because bittorrent reports the reception port in layer 7. Luckly, Deluge has
a command line client which accepts configuration change instructions, so, once
the port is known locally on the VM, it is easy to tell Deluge to use it.

There are 3 scripts to do all of this mess:

* `pull_vpn_ip` I set up a small openvpn script (`route-up`) on the pfsense
  firewall that saves the assigned private ip into a file. The webAdmin service
  serves that plain file just fine to anyone on the LAN. So this script reads
  that file from pfsense, executes the knock procedure with PIA to get a port
  forwarding assignment, and finally updates Deluge with the port. This script
  should be run at startup and also hourly through cron.

* `vpn_ip_rpcserver` creates an rpc responder that listens on the VM for
  a message that the vpn ip has changed. It then executes the knock procedure
  to get a new port forwarding assignment, and updates deluge with that
  information if the port is actually changed from the last time we did this.

* `vpn_ip_rpcclient` actually runs on the pfsense box, triggered by the
  `route-up` script, to advertise to the VM that we have a new private ip
  address.

These scripts make various dumb assumptions about the locations of various
configuration information (e.g. location of the PIA credentitals, the file used
to cache the current port forwarding assignment, etc.), so *caveat emptor*.

# Author

Joel D. Elkins <joel@elkins.com>
