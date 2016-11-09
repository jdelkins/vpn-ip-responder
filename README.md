`VPN_IP_RESPONDER`
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
configured, plus the login credentials of the account, and a user-supplied
"client id", which can be (I think) any hex string. I use a random 32-digit hex
string, which gets re-ranomized periodically.

PIA deallocates the forwarding port after a while, so you have to refresh it
hourly or so with the knock procedure. If the client id changes, you will get
a new port. If the client id stays the same, but the client ip changes, you
tend to get the same port.

Finally, I run deluge on the VM. Deluge needs to know the dynamically forwarded
port because bittorrent reports the reception port in layer 7. Luckly, Deluge
has a command line client which accepts configuration change instructions, so,
once the port is known locally on the VM, it is easy to tell Deluge to use it.

There are a number of scripts to do all of this mess:

* `vpn_ip_rpcserver` This server is the only script that should be run on
  the seedbox VM and not on the pfsense router. It creates an rpc responder
  that listens on the VM for a message that tells it that the vpn ip has
  changed. It simply calls the `deluge-console` to effectuate the port
  configuration change. This is complicated by the need to authenticate
  with the deluge server, and to do that it needs some additional
  parameters.

* `vpn_ip_rpcclient` This python script runs on the pfsense box. It executes
  the knock procedure to establish a forwarding port, and then communicates
  this port to the VM's `vpn_ip_rpcserver` process with an RPC call. There
  are a number of required parameters; run with `--help` for more info.

* `vpn-client-id-generate.sh` This uses `openssl` to generate a 32-digit hex
  number to use as a client id, and saves this to
  `/usr/local/vpn-ip-responder/pia.client_id`. Edit the script if the directory
  should be different.

* `vpn-ip-transmit.sh` This small script invokes `vpn_port_rpcclient`. It can
  be run in two contexts: from cron on a schedule, and from a `route-up`
  script in the openvpn client configuration. If run from `route-up`, it will
  save the local ip address in `/usr/local/vpn-ip-responder/pia.ip`. Then
  it will invoke `vpn_ip_rpcclient` with the chosen arguments. Edit this
  simple script to adapt to local configuraitons.

These scripts make various dumb assumptions about the locations of various
configuration information (e.g. location of the PIA credentitals, the file used
to cache the current port forwarding assignment, etc.), so *caveat emptor*, and
RTFS.

# Author

Joel D. Elkins <joel@elkins.com>
