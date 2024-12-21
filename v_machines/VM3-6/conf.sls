# some packages we needed
netcat-openbsd:
  pkg.installed:
    - refresh: True
    - allow_updates: True 

iperf3:
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
    - proto: none
    - enable_ipv4: False
    - ipv6proto: static
    - enable_ipv6: True
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:2::36
    - ipv6netmask: 64    

eth2:
  network.managed:
    - enabled: True
    - type: eth
    - proto: none
    - enable_ipv4: False
    - ipv6proto: static
    - enable_ipv6: True
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:4::36
    - ipv6netmask: 64

## route to LAN3-6 via VM3 Configuration
routes:
  network.routes:
    - name: eth2
    - routes:
      - name: LAN3-6
        ipaddr: fc00:1234:ffff::/64
        gateway: fc00:1234:4::3
      - name: LAN3-6
        ipaddr: fc00:1234:3::/64
        gateway: fc00:1234:4::3
