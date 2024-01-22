import netmiko
from netmiko import ConnectHandler
from datetime import datetime


#Cisco Devices in the network Seperated by a Comma and in Double Qoutes [ "0.0.0.0", "255.255.255.255" ]
all_cisco_devices = []

#Attention this is not a secure way to store passwords in a file!!#Mobi# only do this if you have read access

#USERNAME-TacAcs+
username = ''

#PASSWORD-TacAcs+
password = ''

#SECRET-TacAcs+
enable_secret = ''



def Connect_Cisco(username,password,enable_secret,all_devices):
    for ip in all_devices:
        device = {
            'device_type': 'autodetect',
            'ip': ip,
            'username': username,
            'password': password,
            'secret':enable_secret,
        }
        #try if device is using SSH
        try:
            #initiate SSH Connection and Authenticate
            net_connect = ConnectHandler(**device)
        #except try connecting with telnet
        except:
            #initiate Telnet Connection and Authenticate
            device['device_type']='cisco_ios_telnet'
            net_connect = ConnectHandler(**device)
        
        #Get Device Hostname
        hostname = net_connect.find_prompt()
        hostname = hostname[:-1]
        #Go into Privilage Exec Mode
        net_connect.enable()
        #run show running-config 
        output = net_connect.send_command("show running-config")
        #terminate session
        net_connect.disconnect()
        #write the output into a file
        date = datetime.now().strftime("#%Y-%m-%d# - %H.%M.%S")
        with open(f"{hostname} ({device['ip']}) {date}.txt",'w+') as f:
            f.write(output)  

#run 
#Connect_Cisco(username, password, enable_secret, all_cisco_devices)