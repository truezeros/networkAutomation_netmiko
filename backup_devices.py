#Author: truezeros
'''
---------
This script will backup device configurations on the devices listed in devices.txt.
----------
'''

import time
from netmiko import ConnectHandler
import re
import getpass
import os
import datetime


# create a directory for saving device configurations
pathConfigs = (r".\\SavedConfigs\\")
try:
  print ("\n Creating directory 'LAB3\SavedConfigs for storing config files.")
  os.mkdir(pathConfigs)
  print ("\t The directory has been created.")
except OSError:
    print ("Creation of the directory %s failed or the directory alrady exists." % pathConfigs)

# create a directory for logging results
pathLogs = (r".\\Logs\\")
try:
  print ("\n Creating directory 'LAB3\Logs for storing logs.")
  os.mkdir(pathLogs)
  print ("\tThe directory has been created.")
except OSError:
    print ("Creation of the directory %s failed or the directory alrady exists." % pathLogs)

# get current date&time
now = datetime.datetime.now()
currentTime = (now.strftime("%Y-%m-%d %H-%M-%S"))

# open devices.txt and read IP addresses that were discovered to be active earlier
with open('devices.txt') as f:
    devicesList = f.read().splitlines()

# prommpt user for ssh login credentials and enable mode password
sshUsername = input('Enter your SSH username: ')
sshPassword = getpass.getpass(prompt="Enter your SSH password: ")
enablePassword = getpass.getpass(prompt="Enter your privileged-exec mode password: ")

# define a list to aggreagate devices for each sucessfully backed up devices and the devices that failed
failedDevices = []
successDevices = []

# start a loop to iterate each live host on the network
for deviceIp in devicesList:

    print ("\n ---------------------------- Attempting SSH connection to " + deviceIp +". ---------------------------- \n")

    # handle error with try/except if the below steps are not sucessful 
    try:

        ios_device = {
        'device_type': 'cisco_ios',
        'ip': deviceIp,
        'username': sshUsername,
        'password': sshPassword,
        'secret': enablePassword
    }
        
        ## establish a SSH connection to the each active host
        try:

            net_connect = ConnectHandler(**ios_device)
            print ("\t >>> SSH connection has been established to " + deviceIp +". \n")
            time.sleep(1.5)
        except:
            failedDevices.append(deviceIp)
            print ("Unable to SSH to " + deviceIp + ".\n")
            continue

        ## get to enable mode
        try:
            net_connect.enable()
        except:
            print ("\t --- ERROR ---: Unable to escelate to privileged-exec mode. Check your enable password.")
            continue

        ## capture hostname from the output of the show run | section hostname command
        hostnameOutput = net_connect.send_command('show run | section hostname')
        deviceHostname = (re.sub('hostname ','', hostnameOutput).replace('\n', ''))

        print ("\t - The hostname on " + deviceIp + " is " + deviceHostname + ". \n")
        time.sleep(1.5)

        ## assign the running config to a variable
        deviceConfig = net_connect.send_command('show run')
        
        ## try saving the file running config to a file called <device-name>.txt
        try:
            saveoutput =  open(r".\\SavedConfigs\\" + deviceHostname + ".txt", "w")
            saveoutput.write (deviceConfig)
            saveoutput.write("\n")
            saveoutput.close
            
            ### append device IP and hostname for all that succesfully backed up
            successDevices.append(deviceIp + ":" + deviceHostname)
            print ("\t >>> Configuration on " + deviceIp + " has been saved in " + (deviceHostname + ".txt"))
    
            time.sleep(2.0)
            
        ## indicate error if unable to save the file due to a permission error,etc
        except:
            print ("\t --- ERROR ---: Unable to save" + (deviceHostname + ".txt"))
            failedDevices.append(deviceIp + ":" + deviceHostname)
            continue
            
    # handle error if the process failed due to any error other than the errors indicated above
    except :
        ## append each device that the program could not back up the config for
        failedDevices.append(deviceIp + ":" + deviceHostname)
        print ("\t --- ERROR ---: Could not backup device configuration for " + deviceIp + "\n") 
        
    
    #if all active devices' configs saved, indicate there is no error
    if not failedDevices :
        failedDevicesResult = ">> No devices returned error"
    else:
        failedDevicesResult = failedDevices

# remove brackets when printing devices
failedDevices = (', '.join(failedDevices))
successDevices = (', '.join(successDevices))

# log the results each time the program is run
backupResult =  ("\n Day and time: " + currentTime +
        "\n Backup process has been completed: " + 
        "\n >> Device configurations have been backed up for " + str(successDevices) +
        "\n -- Failed to copy device configurations for " + str(failedDevices))

print (backupResult + "\n > Results have been saved to device-configs_" + currentTime + ".txt")
save_result =  open(r".\\Logs\\" + "backup-configs_" + currentTime + ".txt", "w")
save_result.write(backupResult)
save_result.write("\n")
save_result.close


