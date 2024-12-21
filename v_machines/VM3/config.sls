# some packages we needed
radvd:
  pkg.installed:
    - refresh: True
    - allow_updates: True 

iptables:
  pkg.installed:
    - refresh: True
    - allow_updates: True
    
## Delete default gateway
ip route del default:
  cmd:
    - run

## eth1 and eth2 interface Configuration 
eth1:
  network.managed:
    - enabled: True
    - type: eth
    - proto: static
    - ipaddr: 172.16.2.163
    - netmask: 28

eth2:
  network.managed:
    - enabled: True
    - type: eth
    - proto: static
    - enable_ipv4: false
    - ipv6proto: static
    - enable_ipv6: true
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:4::3
    - ipv6netmask: 64

## route to LAN1 via VM2 Configuration
routes:
  network.routes:
    - name: eth1
    - routes:
      - name: LAN1
        ipaddr: 172.16.2.128/28
        gateway: 172.16.2.162
    
## Enable ipv6 forwarding
net.ipv6.conf.all.forwarding:
  sysctl:
    - present
    - value: 1
    
net.ipv6.conf.all.disable_ipv6:
  sysctl:
    - present
    - value: 0

## Enable ipv4 forwarding
net.ipv4.ip_forward:
  sysctl:
    - present
    - value: 1

net.ipv6.conf.eth2.accept_ra:
  sysctl:
    - present
    - value: 1
    
