"""Class and Associated Templates to enable basic Bind9 Configuration"""
import ipaddress
import math
import os
import random
import subprocess

from datetime import datetime
from jinja2 import Template
class Bind:
    '''Class and methods for quickly configuring files for
    a basic local Bind Nameserver'''
    def __init__(self,ns_domain_name,ns_addr) -> None:
        Bind.addr_error_check(ns_addr)
        self.ns_domain_name = ns_domain_name
        self.ns_cidr_addr = ns_addr
        # Strips off network mask
        self.ns_addr = ns_addr.split('/')[0]
        # Removes NS hostname
        self.domain_name = ".".join(ns_domain_name.split('.')[1::])
        # Stores the NS hostname as an attribute
        self.ns_hostname = ns_domain_name.split('.')[0]
        self.rev_ns_addr = self.reverse_addr(ns_addr)
        # Generates a Serial Number with 'Today's' Date and a random 10-99 number appended on the end.
        self.serial = datetime.today().strftime('%y%m%d') + str(math.floor((random.random())*100))
        self.output_path = os.environ['HOME']
        self.bind_path = self.distro_file_path()

    def forward_zone_config(self) -> None:
        '''Configure the forward lookup zones and config
        files based on NS FQDN and Address'''
        output_conf = Template(CONF_FORWARD).render(domain_name=self.domain_name,
                                                    bind_path=self.bind_path)
        output_for_zone = Template(FORWARD_ZONE).render(domain_name=self.domain_name,
                                                        ns_addr=self.ns_addr,
                                                        ns_hostname=self.ns_hostname,
                                                        ser_num=self.serial)
        with open(f'{self.output_path}/named.conf.local',"w") as i:
            i.write(output_conf)
            i.close()
        print(f'\nSet forward lookup zone for {self.domain_name} in named.conf.local')
        with open(f"{self.output_path}/{self.domain_name}","w") as j:
            j.write(output_for_zone)
            j.close()
        print(f'Created forward lookup zone file {self.domain_name}')

    def reverse_zone_config(self,addr) -> None:
        '''Configure reverse lookup zones based on
        IP address and network mask supplied in CIDR Notation'''
        Bind.addr_error_check(addr)
        rev_zone_name = self.reverse_zone_name(addr)
        rev_zone_file_name = self.zone_file_name(addr)
        output_conf = Template(CONF_REV).render(rev_zone_name=rev_zone_name,
                                                rev_zone_file_name=rev_zone_file_name,
                                                bind_path=self.bind_path)
        output_rev_zone = Template(REV_ZONE).render(domain_name=self.domain_name,
                                                    ns_hostname=self.ns_hostname,
                                                    ns_addr=self.ns_addr,ser_num=self.serial,
                                                    rev_ns_addr=self.rev_ns_addr)
        rev_path = f'{self.output_path}/{rev_zone_file_name}'
        if os.path.exists(rev_path):
            raise ValueError
        with open(f"{self.output_path}/named.conf.local","a") as i:
            i.write("\n"+output_conf)
            i.close()
        print(f'\nAdded reverse lookup zone for {rev_zone_name} to named.conf.local')
        with open(f"{self.output_path}/{rev_zone_file_name}","w") as j:
            j.write(output_rev_zone)
            j.close()
        print(f'Reverse Lookup zone file {rev_zone_file_name} created\n')
        if self.zone_file_name(self.ns_cidr_addr) == rev_zone_name:
            self.add_ptr(self.ns_hostname,self.ns_cidr_addr)

    def add_a(self,hostname,addr) -> None:
        '''Appends an A record to the domain configuration file for the given Bind object'''
        Bind.addr_error_check(addr)
        host_addr = addr.split('/')[0] # Removes network mask
        output = Template(A_RECORD).render(hostname=hostname,host_addr=host_addr)
        with open(f'{self.output_path}/{self.domain_name}','a') as i:
            i.write('\n'+output)
            i.close()
        print(f'\n{output} was added to {self.domain_name}')

    def add_ptr(self,hostname,addr) -> None:
        '''Appends a pointer record to the appropriate zone file for the addr parameter'''
        Bind.addr_error_check(addr)
        rev_host_addr = self.reverse_addr(addr)
        file_name = self.zone_file_name(addr)
        output = Template(PTR_RECORD).render(domain_name=self.domain_name,
                                            hostname=hostname,
                                            rev_host_addr=rev_host_addr)
        file_path = f'{self.output_path}/{file_name}'
        if not os.path.exists(file_path):
            print(f'Reverse zone for {addr} does not exist\nPTR record for {hostname} not added')
            raise FileNotFoundError
        with open(f"{file_path}","a") as i:
            i.write("\n" + output)
            i.close()
        print(f'\n{output} was added to {file_name}\n')

    def add_txt(self,name,contents) -> None:
        '''Appends an Text record to the domain configuration file for the given Bind object.'''
        output=Template(TXT_RECORD).render(record_name=name,
                                           txt_contents=contents,
                                           domain_name=self.domain_name)
        with open(f"{self.output_path}/{self.domain_name}","a") as i:
            i.write('\n' + output)
            i.close()
        print(f'\n{output} was added to {self.domain_name}')

    def add_cname(self,cname,hostname) -> None:
        '''Appends a Cannonical Name record to the domain
        configuration file for the given Bind object.'''
        output=Template(CNAME_RECORD).render(cname=cname,
                                            hostname=hostname,
                                            domain_name=self.domain_name)
        with open(f"{self.output_path}/{self.domain_name}","a") as i:
            i.write('\n' + output)
            i.close()
        print(f'\n{output} was added to {self.domain_name}')

    def add_mx(self,hostname,preference_number='10',ttl='') -> None:
        '''Adds an Mail Exchanger record to the domain
        configuration file for the given Bind object.'''
        output_mx = Template(MX_RECORD).render(ttl=ttl,
                                               preference_number=preference_number,
                                               hostname=hostname,
                                               domain_name=self.domain_name)
        with open(f"{self.output_path}/{self.domain_name}","a") as i:
            i.write('\n' + output_mx)
            i.close()
        print(f'\n{output_mx} was added to {self.domain_name}')

    def zone_file_name(self,addr) -> str:
        '''Returns the name of the zone file,
        based on a common naming scheme that is not required,but I find useful\n
        Internal to this class error checking is done prior to this function,
        but is implemented here for use in other scenarios\n
        Example: 192.168.10.1/24 -> db.192.168.10'''
        Bind.addr_error_check(addr)
        if len(addr.split('/')) == 2: # Checks if user included network mask
            sub_mask_dict= {
                "24" : 3,
                "16" : 2,
                "8" : 1,
            }
            sub_mask = addr.split("/")[1]
            file_name = (f'db.{".".join(addr.split(".")[0:(sub_mask_dict[sub_mask])])}')
            return file_name
        else:
            print('\nNo network mask included, defaulting to /24')
            file_name = (f'db.{".".join(addr.split(".")[0:3])}')
            return file_name

    def reverse_zone_name(self,addr) -> str:
        '''Returns the reverse zone address\n
        Internal to this class error checking is done prior to this function,
        but is implemented here for use in other scenarios\n
        Used internally for configuring reverse lookup zones in named.conf.local\n
        Example: 192.168.10.1/24 -> 10.168.192.in-addr.arpa'''
        Bind.addr_error_check(addr)
        if len(addr.split('/')) == 2:
            sub_mask_dict= {
                "24" : 2,
                "16" : 1,
                "8" : 0
            }
            sub_mask = addr.split("/")[1]
            rev_zone_name =".".join(addr.split('.')[(sub_mask_dict[sub_mask])::-1]) +".in-addr.arpa"
            return rev_zone_name
        else:
            print('\nNo network mask included,defaulting to /24')
            rev_zone_name = ".".join(addr.split('.')[2::-1]) + ".in-addr.arpa"
            return rev_zone_name

    def reverse_addr(self,addr) -> str:
        '''Returns the significant octets in reverse order\n
        Internal to this class error checking is done prior to this function,
        but is implemented here for use in other scenarios\n
        Example: 192.168.10.1/8 -> 1.10.168 \n
        Utilized for PTR records'''
        Bind.addr_error_check(addr)
        if len(addr.split('/')) == 2:
            net_mask_dict= {
                "24" : 1,
                "16" : 2,
                "8" : 3
            }
            net_mask = addr.split("/")[1]
            rev_host_addr =".".join(((addr.split('/')[0]).split('.')[::-1])[0:net_mask_dict[net_mask]])
            return rev_host_addr
        print('\nNo network mask included, defaulting to /24')
        rev_host_addr = addr.split('.')[-1]
        return rev_host_addr

    def addr_error_check(addr) -> Exception:
        '''If address is not valid for this script, will raise an expection that is mildly verbose.
        \nThis script is only setup to handle /8, /16, /24 masks.'''
        try:
            net_mask = int(addr.split('/')[1])
            ipaddress.IPv4Interface(addr)
            acceptable_cidr = [8, 16, 24]
            if net_mask not in acceptable_cidr:
                raise ipaddress.NetmaskValueError
        except ipaddress.AddressValueError:
            print(f'\nInvalid IPv4 Address, {addr.split("/")[0]} is not a valid address')
            return False
        except ipaddress.NetmaskValueError:
            print(f'\nNetwork mask not valid for this script, /{net_mask} is not /8, /16, or /24')
            return False
        except IndexError:
            print('\nPlease input address in CIDR Notation\nExample: 192.168.1.1/24\n')
            return False
        else:
            return True

    def set_output_path(self,path) -> None:
        '''Checks if path exists, then modifies the given Bind objects output_path attribute'''
        if path == '':
            print(f'Output path left at the default {self.output_path}\n')
        elif os.path.exists(path):
            self.output_path = path
            print(f'\nSuccess: Output path set to {path}\n')
        else:
            print(f'\nFailed: {path} is not valid or does not exist\n')

    def distro_file_path(self) -> str:
            '''Performs a basic check to see if running CentOS, if not uses 
            the Debian/Ubuntu default bind file paths'''
            distro = subprocess.Popen(['lsb_release','-i'],stdout=subprocess.PIPE)
            distro = str(distro.communicate())
            if not distro.find('Cent') == -1:
                bind_base_path = '/etc/named'
                return bind_base_path
            # If not CentOS, default to 
            # Debian/Ubuntu default bind file path.
            bind_base_path = '/etc/bind'
            return bind_base_path

CONF_FORWARD = '''zone "{{domain_name}}" IN {
	type master;
	file "{{bind_path}}/{{domain_name}}";
	allow-update { None; };
};
'''
CONF_REV ='''zone "{{rev_zone_name}}" IN {
	type master;
	file "{{bind_path}}/{{rev_zone_file_name}}";
	allow-update { None; };
};'''
# Template of a Forward lookup zone file
FORWARD_ZONE='''$TTL	604800
@	IN	SOA	{{ns_hostname}}.{{domain_name}}. root.{{domain_name}}. (
		   {{ser_num}}		; Serial
			 604800		; Refresh
			  86400		; Retry
			2419200		; Expire
			 604800 )	; Negative Cache TTL
;

@	IN	NS	{{ns_hostname}}.{{domain_name}}.
{{ns_hostname}}	IN	A	{{ns_addr}}'''
# Template of a Reverse lookup zone file in NS's zone
REV_ZONE ='''$TTL	604800
@	IN	SOA	{{domain_name}}. root.{{domain_name}}. (
		   {{ser_num}}		; Serial
			 604800		; Refresh
			  86400		; Retry
			2419200		; Expire
			 604800 )	; Negative Cache TTL
;

@	IN	NS	{{ns_hostname}}.{{domain_name}}.
{{ns_hostname}}	IN	A	{{ns_addr}}'''

A_RECORD ='''{{hostname}}	IN	A	{{host_addr}}'''
PTR_RECORD='''{{rev_host_addr}}	IN	PTR	{{hostname}}.{{domain_name}}.'''
TXT_RECORD = '''{{record_name}}.{{domain_name}}.	IN	TXT	"{{txt_contents}}"'''
CNAME_RECORD='''{{cname}}	IN	CNAME	{{hostname}}.{{domain_name}}.'''
MX_RECORD='''{{ttl}}	IN	MX	{{preference_number}} {{hostname}}.{{domain_name}}.'''
