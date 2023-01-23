from bind import Bind
import sys

def menu():
    for key in menu_options.keys():
        print (key, '--', menu_options[key] )

menu_options= {
    0: 'Initialize object for editing.  Creates/Edits No Config Files.',
    1: 'Set output path, default is user home directory',
    2: 'Forward zone config',
    3: 'New Reverse zone config',
    4: 'Add A record',
    5: 'Add ptr record',
    6: 'Add txt record',
    7: 'Add cname Record',
    8: 'Add mx record',
    9: 'Exit',
}

if __name__=='__main__':
        while(True):
            menu()
            option = ''
            try:
                option = int(input('Enter your choice: '))
            except KeyboardInterrupt:
                sys.exit('\nThanks for trying')
            except:
                print('Please enter a number ...')
            if option == 0: 
                try:
                    ns_domain_name = input('\nEnter the FQDN of the nameserver\nExample: ns.example.local\n> ')
                    ns_addr = input('\nEnter the address of the name server\nExample: 192.168.1.1/24\n> ')
                    Bind.addr_error_check(ns_addr)
                    a = Bind(ns_domain_name,ns_addr)
                    print(f'\nInitialized for editing {ns_domain_name}\n')
                except Exception as error:
                    print(error + '\n')
                    continue
            elif option == 1:
                try:
                    path = input('\nEnter the path of where to save ALL config files to.\nDefault is user home directory\n> ') or ''
                    if(path == ''):
                        continue
                    else:
                        a.set_output_path(path)
                except Exception as error:
                    print(error)
                    continue
            elif option == 2:
                try:
                    a.forward_zone_config()
                    a.reverse_zone_config(a.ns_cidr_addr)
                except Exception as error:
                    print(error)
                    continue
            elif option == 3:
                try:
                    zone_addr = input('\nEnter an address in the new zone\nExample: 10.20.20.0/24\n> ')
                    a.reverse_zone_config(zone_addr)
                except Exception as error:
                    print(error)
                    continue
            elif option == 4:
                try:
                    hostname = input('\nEnter Hostname\nExample: for minecraft.example.local input minecraft \n>  ')
                    host_addr = input('\nEnter host address\nExample: 10.20.20.20/24\n> ')
                    choice = input('\nDo you want to add an PTR record for this Record ? Y/n\n> ') or 'Y'
                    if(choice.lower() == ('y' or 'yes')):
                        a.add_ptr(hostname,host_addr)
                    a.add_a(hostname,host_addr)
                    continue
                except Exception as error:
                    print(error)
                    continue
            elif option == 5:
                try:
                    hostname = input('\nEnter Hostname\nExample: for minecraft.example.local input minecraft \n>  ')
                    host_addr = input('\nEnter host address\nExample: 10.20.20.20/24\n> ')
                    a.add_ptr(hostname,host_addr)
                except Exception as error:
                    print(error)
                    continue
            elif option == 6:
                try:
                    name = input('\nEnter Text record Name:\nExample: _example\n> ')
                    contents = input('\nEnter contents of the text record:\n> ')
                    a.add_txt(name,contents)
                except Exception as error:
                    print(error)
                    continue
            elif option == 7:
                try:
                    name = input('\nEnter Host to link:\nexample: For ftp.example.local linked to files.example.local input ftp\n> ')
                    hostname = input('\nEnter Host being linekd to:\nexample: For ftp.example.local linked to files.example.local input files\n> ')
                    a.add_cname(name,hostname)
                except Exception as error:
                    print(error)
                    continue
            elif option == 8:
                try:
                    mail_hostname = input('\nEnter the hostname of the mail server.\nExample: for mail.example.local input mail\n>  ')
                    preference_number = input('\nEnter preference number("priority") Default: 10(Highest Priority)\n> ') or '10'
                    ttl = input('\nEnter time to live value, Default is an empty string\n> ') or ''
                    choice = input('\nDo you want to add an A record for the mail server? Y/n\n> ') or 'Y'
                    if(choice.lower() == ('y' or 'yes')):
                        mail_addr = input('\nEnter mail server address\nExample: 10.20.20.20/24\n> ')
                        a.add_a(mail_hostname,mail_addr)
                    a.add_mx(mail_hostname,preference_number,ttl)
                    continue
                except Exception as error:
                    print(error)
                    continue
            elif option == 9:
                exit('Thanks! Bye')
            else:
                print('Enter an option or select exit')