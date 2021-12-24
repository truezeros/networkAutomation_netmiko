#Author: Jaie-Ross-Mandeep-Yasin

'''
---------
This application will save routing tables as CSV files.
11/26/2021
----------
'''

import time
from netmiko import ConnectHandler
import re
import getpass
import datetime
import csv
import os


now = datetime.datetime.now()
currentTime = (now.strftime("%Y-%m-%d %H-%M-%S"))

with open('devices.txt') as f:
  devicesList = f.read().splitlines()

# create a directory for saving routing tables as CSV files
path = (r".\\LAB3\\RoutingTables")
try:
  print ("\n Creating directory 'LAB3\RoutingTables for storing config files.")
  os.mkdir(path)
  print ("\t The directory has been created.")
except OSError:
    print ("Creation of the directory %s failed or the directory alrady exists." % path)

#define a list to aggreagate devices that sucessfully processed the devices that failed
failedDevices = []
successDevices = []

ssh_username = input('Enter your SSH username: ')
ssh_password = getpass.getpass(prompt="Enter your SSH password: ")
enable_password = getpass.getpass(prompt="Enter your privileged-exec mode password: ")

try:

  for deviceIp in devicesList:

    print ("\n ---------------------------- Attempting SSH connection to " + deviceIp +". ---------------------------- \n")


    ios_device = {
    'device_type': 'cisco_ios',
    'ip': deviceIp,
    'username': ssh_username,
    'password': ssh_password,
    'secret': enable_password
      }

    # establish a SSH connection to the each active host
    try:

        net_connect = ConnectHandler(**ios_device)
        print ("\t >>> SSH connection has been established to " + deviceIp +". \n")
        time.sleep(1.5)
    except:
        print ("\n\t--- ERROR ---: Unable to SSH to " + deviceIp + ".\n")
        continue
    # get to enable mode
    try:
        net_connect.enable()
    except:
        print ("\t --- ERROR ---: Unable to escelate to privileged-exec mode. Check your enable password.")
        continue

    # capture hostname from the output of show run | section hostname command
    hostnameOutput = net_connect.send_command('show run | section hostname')
    deviceHostname = (re.sub('hostname ','', hostnameOutput).replace('\n', ''))

    # get structured data using textfsm for 'show ip route'
    routingTable = net_connect.send_command('show ip route', use_textfsm=True)


    # save the dictionary objects(routing table) in the output to a CSV file
    print ("\t >>> Saving Routing table for " + deviceHostname + "... \n")
    keys = routingTable[0].keys()
    CSVFileName = deviceHostname + "_route-table.csv"
    a_file = open(r".\\LAB3\\RoutingTables\\" + CSVFileName , 'w')
    dict_writer = csv.DictWriter(a_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(routingTable)
    a_file.close()
    print ("\t >>> Routing table has been saved for " + deviceHostname + " as "+ CSVFileName +". \n")
    successDevices.append(deviceIp + ":" + deviceHostname)
    
except:
  print ("\n \t --- ERROR --- : Unable to save routing table for" + deviceHostname)
  #append each device the program was able to configure routing on
  failedDevices.append(deviceIp)

#if all routing tables are saved, indicate there is no error
if not failedDevices :
    failed_device = ">> No devices returned error"
else:
    failed_device = " -- Failed to back up configs for " + str(failedDevices)

#remove brackets when printing devices
failedDevices = (', '.join(failedDevices))
successDevices = (', '.join(successDevices))

#log the results and save to a new file each time the program is run
saveRoutes =  ("\n Day and time: " + currentTime +
        "\n Saving routing tables process has been completed: " + 
        "\n >> Routing tables have been saved for " + str(successDevices))

#save the logs in a file
save_Result =  open(r".\\LAB3\\Logs\\" + deviceHostname + "_route-table.txt", "w")
save_Result.write (saveRoutes)
save_Result.write("\n")
save_Result.close
print (saveRoutes + "\n > Results have been saved to " + deviceHostname + "_route-table.txt." )
