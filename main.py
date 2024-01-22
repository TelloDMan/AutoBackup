#!/usr/bin/env python3
import re
import os
import sys
import git
import shutil
import calendar
import concurrent.futures
from pythonping import ping
from dotenv import load_dotenv
from netmiko import ConnectHandler
from datetime import datetime

#load enviroment variables
load_dotenv()

#take timestamp
date = datetime.now().strftime("#%Y-%m-%d# - %H.%M.%S")
date_day = datetime.now().strftime("%Y-%m-%d")
#import logging
#logging.basicConfig(level=logging.DEBUG)

#Cisco Devices in the network Seperated by a Comma and in Double Qoutes [ "0.0.0.0", "255.255.255.255" ]
#Put the Device Ip in the All_Devices.txt
all_devices = [  ]
with open("All_Devices.txt",'r') as f:
    all_devices = f.readlines()
    all_devices = list(map(lambda x: x.replace("\n",''), all_devices))

#Attention this is not a secure way to store passwords in a file!

#USERNAME-TacAcs+
username = str(os.getenv("DEVICE_USERNAME"))

#PASSWORD-TacAcs+
password = os.getenv("DEVICE_PASSWORD")

#SECRET-TacAcs+
enable_secret = os.getenv("DEVICE_ENABLE_PASSWORD")


#detect duplicates
duplicate = True

#sync with github repo
def GitSync():
    repo = git.Repo('../AutoBackup')
    repo.remotes.origin.fetch()
    repo.git.merge('origin/main')


#zip folder and upload it to the cloud on planetscale
def Backup_To_Cloud():
    pass


#checks for missing months and years in backup folder
def dir_tree(dir):
    os.chdir(dir)
    year = datetime.now().strftime("%Y")
    month = calendar.month_name[int(datetime.now().strftime("%m"))]
    years = os.listdir()
    if year not in years:
        os.mkdir(f'{year}/')
        os.chdir(f'{year}/')
        months = os.listdir()
        if month not in months:
            os.mkdir(f'{month}/')
            os.chdir(f'{month}/')
        else:
            os.chdir(f'{month}/')
    else:
        os.chdir(f'{year}/')
        months = os.listdir()
        if month not in months:
            os.mkdir(f'{month}/')
            os.chdir(f'{month}/')
        else:
            os.chdir(f'{month}/')


#checks for date inside month folder
def Record_Day():
    folders = os.listdir()
    if duplicate:
        if date_day in folders:
            sys.exit()
        else:
            os.mkdir("./"+date_day+"/")
            os.chdir("./"+date_day+"/")
    
    
#detects the connecting device
def detect_type(connection):
    try:
        version = connection.send_command("show version")
        if re.search("Invalid",version):
            assert LookupError
    except:
        return {'device_type':'cisco_ios'}
    if re.search("JUNOS",connection.send_command("show version")):
        connection.disconnect()
        return {'device_type':'juniper_junos'}
    else:#re.match("Cisco",version):
        connection.disconnect()
        return {'device_type':'cisco_ios'}


def check_all_present():
    #shows if an IP is missing in the folder from All_devices.txt that didint backed up and created a file
    files = os.listdir()
    not_listed = []
    present = list(map(lambda x:re.findall('\(.*\)',x)[0][1:-1],files))
    for ip in all_devices:
        if ip in present:
            continue
        else:
            not_listed.append(ip)
    return not_listed


##connect on recent connection
def get_backup(device,connection):
    output=''
    #if device type is still autodetect check device vendor

    if device["device_type"] == "autodetect":
        device_type = list(detect_type(connection).values())[0]
        device['device_type'] = device_type
        if device['device_type'] == 'cisco_ios':
            connection = ConnectHandler(**device)
        elif device['device_type'] == 'juniper_junos':
            del device['secret']
            connection = ConnectHandler(**device)
        

    if device['device_type'] == "cisco_ios" or device['device_type'] == "cisco_ios_telnet" :
        try:
            #Go into Privilage Exec Mode
            try:
                connection.enable()
                #check if device entered enable mode from ">" to "#"
                hostname = connection.find_prompt()
                if re.search(">$",hostname):
                    raise ReferenceError
            except:
                pass
            #run show running-config
            try:
                user = connection.find_prompt()
                user = hostname[:-1]
                output = connection.send_command("show running-config",read_timeout=25)
            except:
                output = connection.send_command("show running-config",read_timeout=25)
        except:
            print(device["ip"])
        
    elif device['device_type'] == "juniper_junos" or device['device_type'] == "juniper_junos_telnet":
        try:
            del device["secret"]
        except:
            pass
        try:
            #run show configuration
            hostname = connection.find_prompt()
            while hostname == "{master:0}":
                connection.disconnect()
                connection = ConnectHandler(**device)
                hostname = connection.find_prompt()
            user = hostname.replace(device['username'],"")    
            user = user[1:-1]    
            try:
                output = connection.send_command("show configuration | no-more | display set",read_timeout=25)
            except:
                output = connection.send_command("show configuration|display set",read_timeout=25)
        except:
            print(device["ip"])   
    try:
        #write the output into a file
        with open(f"{user} ({device['ip']}) {date}.txt",'w+') as f:
            f.write(output)
    except:
        print(device["ip"])
        pass

    connection.disconnect()


def Connect(username,password,enable_secret,ip):
    global duplicate
    try:
        device = {
            'device_type': 'autodetect',
            'ip': ip,
            'username': username,
            'password': password,
            'secret':enable_secret
        }

        try:
            net_connect_try = ConnectHandler(**device)
            get_backup(device, net_connect_try)


        except Exception as err:
            #this is for further debuging if ssh or telet is operating on different port
            if re.search("Wrong TCP port",str(err)) or re.search("Login Failed:",str(err)):
                try:
                    device["device_type"] = 'cisco_ios_telnet'
                    net_connect_try = ConnectHandler(**device)
                    get_backup(device, net_connect_try)
                except:
                    device["device_type"] = 'juniper_junos_telnet'
                    del device["secret"]
                    net_connect_try = ConnectHandler(**device)
                    get_backup(device, net_connect_try)
            

    except Exception as err:
        print(err)
        print(device['ip'])  
    

#Start program
def start():
    global all_devices
    global duplicate
    threads = []

    devices = []
    for ip in all_devices:
        devices.append([username,password,enable_secret,ip])
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda args: Connect(*args), devices)

    unlisted = check_all_present()
    print(unlisted)      
    if len(unlisted) > 0:
        # check if ping is available to device, because maybe the device could be down, so we skip the backup
        for ip in unlisted:
            available = ping(ip, count=1)
            if available.success():
                continue
            else:
                unlisted.remove(ip)
        all_devices = unlisted
        duplicate = False
        start()
    src = str(os.getcwd()).replace("\\",'/')
    ##############this is ths shared folder where the backups will be forwarded#########
    dir_tree('/path/to/backup')
    current = os.getcwd().replace('\\','/')
    shutil.copytree(src,current+f'/{date_day}')

#initiates the current Local Backup directory( /path/to/the/script )
dir_tree('./')
#saves the folder by month-day-year
Record_Day()
#starts the backup process
start()

