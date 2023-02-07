#!/usr/bin/env python3

# Import directories
import subprocess
import xml.etree.ElementTree as ET

# Scan the IP in the local network to find iHP device
def scan_ip_address(ip_range, MAC):
    xml = scan_for_hosts(ip_range)
    return find_ip_address_for_mac_address(xml, MAC)
    
def scan_for_hosts(ip_range):
    """Scan the given IP address range using Nmap and return the result
    in XML format.
    """
    nmap_args = ['nmap', '-n', '-sP', '-oX', '-', ip_range]
    return subprocess.check_output(nmap_args)

def find_ip_address_for_mac_address(xml, mac_address):
    """Parse Nmap's XML output, find the host element with the given
    MAC address, and return that host's IP address (or `None` if no
    match was found).
    """
    host_elems = ET.fromstring(xml).iter('host')
    host_elem = find_host_with_mac_address(host_elems, mac_address)
    if host_elem is not None:
        return find_ip_address(host_elem)

def find_host_with_mac_address(host_elems, mac_address):
    """Return the first host element that contains the MAC address."""
    for host_elem in host_elems:
        if host_has_mac_address(host_elem, mac_address):
            return host_elem

def host_has_mac_address(host_elem, wanted_mac_address):
    """Return true if the host has the given MAC address."""
    found_mac_address = find_mac_address(host_elem)
    return (
        found_mac_address is not None and
        found_mac_address.lower() == wanted_mac_address.lower()
    )

def find_mac_address(host_elem):
    """Return the host's MAC address."""
    return find_address_of_type(host_elem, 'mac')

def find_ip_address(host_elem):
    """Return the host's IP address."""
    return find_address_of_type(host_elem, 'ipv4')

def find_address_of_type(host_elem, type_):
    """Return the host's address of the given type, or `None` if there
    is no address element of that type.
    """
    address_elem = host_elem.find('./address[@addrtype="{}"]'.format(type_))
    if address_elem is not None:
        return address_elem.get('addr')