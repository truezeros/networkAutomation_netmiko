#Author: Jaie-Ross-Mandeep-Yasin

'''
---------
NETW3100 - LAB 3 -
This application will configure EIGRP on devices.
11/26/2021
----------
'''

import time
from netmiko import ConnectHandler
import re
import getpass
import datetime

now = datetime.datetime.now()
currentTime = (now.strftime("%Y-%m-%d %H-%M-%S"))

with open('devices.txt') as f:
  devices_list = f.read().splitlines()

ssh_username = input('Enter your SSH username: ')
ssh_password = getpass.getpass(prompt="Enter your SSH password: ")
enable_password = getpass.getpass(prompt="Enter your privileged-exec mode password: ")

# define a list to aggreagate devices that sucessfully processed the devices that failed
failed_devices = []
success_devices = []

for device_ip in devices_list:

  print ("\n ---------------------------- Attempting SSH connection to " + device_ip +". ---------------------------- \n")

  # handle error if the below steps are not sucessful 
  try:


    ios_device = {
    'device_type': 'cisco_ios',
    'ip': device_ip,
    'username': ssh_username,
    'password': ssh_password,
    'secret': enable_password
    }
    
    # establish a SSH connection to the each active host
    try:

        net_connect = ConnectHandler(**ios_device)
        print ("\t >>> SSH connection has been established to " + device_ip +". \n")
        time.sleep(1.5)
    except:
        print ("\n\t--- ERROR ---: Unable to SSH to " + device_ip + ".\n")
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

    # get outout of show ip int bri command
    output = net_connect.send_command('show ip int bri')

    # format the output to retrieve interface id, ip address, status
    intRows = str(output).splitlines()
    intRows.pop(0)
    
    # define empty variables for interface ids, ip address ('networks' when issued under a dynamic routing configuration)
    activeInts = ""
    networks = ""
    activeIntIDs = ""
    
    # start a loop to iterate each interface
    for row in intRows:

        ## assign int status, id, ipaddress to variables
        intStatus = (row.split()[5])
        intID = (row.split()[0])
        intAddress = (row.split()[1])

        ## determine only physical interfaces that are in 'up' state and assigned with an IP address
        if intStatus == "up" and 'Vlan' not in intID and 'unassigned' not in intAddress:
          
          #append retained data to variables
          activeIntIDs += intID + "\n"
          activeInts += " > " + intID + " - " + intAddress + "\n"
          networks += intAddress + "\n"

    # list active interfaces that the program will consider
    print  (" - The active interfaces with an assigned IP address on " + deviceHostname + " are: \n" + activeInts)

    print (" - Configuring EIGRP on " + deviceHostname + "...\n")
    
    # define wildcard to be used when advertising (enabling eigrp on ints) networks
    wildCard = '0.0.0.3'
    
    # start a loop to iterate each network (ip address obtained above will default to network address in iOS)
    for network in networks.splitlines():
      #configure eigrp 44, disable auto-summary, enable eigrp (advertise networks) on specified ints
      configure_Eigrp = ['router eigrp 44', 'no auto-summary', 'network ' + network + " " + wildCard]
      net_connect.send_config_set(configure_Eigrp)
    
    # get output of eigrp configuration on the device
    eigrpOutput = net_connect.send_command('show run | section router eigrp 44')
    
    # display the configuration applied by the program
    print ("\n>>> EIGRP has been configured on " + deviceHostname + " with below: \n- - - " + eigrpOutput + "\n - - -")
    
    # append each device the program was able to configure routing on
    success_devices.append(device_ip + ":" + deviceHostname)
    
    time.sleep(2.0)
    
    # this is just to fix a peculiar issue with the network simulation environment
    for interface in activeIntIDs.splitlines():
      converganceFix = ['interface ' + interface , 'shutdown ' , 'no shutdown']
      net_connect.send_config_set(converganceFix)
      

    
  # indicate an error for any other error than handled above
  except :
    print ("\t --- ERROR ---: Unable to configure EIGRP on " + device_ip + "\n") 
    #if failed to configure routing, append the device 
    failed_devices.append(device_ip + ":" + deviceHostname)
  
  # if all active devices' configs saved, indicate there is no error
  if not failed_devices :
      failed_device = ">> No devices returned error"
  else:
      failed_device = " -- Failed to back up configs for " + str(failed_devices)
    
# remove brackets when printing devices
failed_devices = (', '.join(failed_devices))
success_devices = (', '.join(success_devices))

# log the results each time the program is run
eigrpResult =  ("\n Day and time: " + currentTime +
    "\n Configuring EIGRP process has been completed: " + 
    "\n >> EIGRP has been configured on  " + str (success_devices))
saveResult =  open(r".\\LAB3\\Logs\\" + "eigrp-routing_" + currentTime + ".txt", "w")
saveResult.write (eigrpResult)
saveResult.write("\n")
saveResult.close
print (eigrpResult + "\n > Results have been saved to eigrp-routing" + currentTime + ".txt")
