#!/usr/bin/env python3
# coding=utf-8

# hextract.py

# Libraries
import requests

# Generate save dictionary using save.ini
def generateSave(filename):
	save_dict = {}

	try:
		f = open("../config/save.ini", "r")
		current_dict = save_dict
		for line in f:
			if len(line) > 1 and line[0] != '[':
				k, v = line.split('=', 1)
				if v.rstrip() == "{filename}":
					current_dict[k] = filename
				else:
					current_dict[k] = v.rstrip()
			elif "HEADERS" in line:
				save_dict["headers"] = {}
				current_dict = save_dict["headers"]
			elif "DATA" in line:
				save_dict["data"] = {}
				current_dict = save_dict["data"]
			else:
				current_dict = save_dict
			
		f.close()
	except IOError:
		print("No configuration file found. Generating default configuration file at ../config/save.ini.")
		print("Please set your save parameters and try again.")
		f = open("../config/save.ini", 'w')
		f.write("[API]\n")
		f.write("endpoint=\n")
		f.write("\n")
		f.write("[HEADERS]\n")
		f.write("\n")
		f.write("[DATA]\n")
		f.write("\n")
		f.close()

		sys.exit(1)

	return save_dict

# Save the generated WSDL 2.0 to WSO2 Governance Registry
def saveToRepository(resources, hrests_dict):
	filename = hrests_dict["serviceName"] + ".wsdl"
	save_dict = generateSave(filename)
	url = save_dict["endpoint"]

	if "schemaLocation" not in resources: 
		files = {'wsdl_file': open("../wsdl/" + hrests_dict["serviceName"] + ".wsdl", 'rb')}
	else:
		files = {'wsdl_file': open("../wsdl/" + hrests_dict["serviceName"] + "/" + hrests_dict["serviceName"] + ".zip", 'rb')}
	r2 = requests.post(url, data=save_dict["data"], verify=False, headers=save_dict["headers"], files=files)
	print(r2)
	if (r2.status_code != 200):
		print(str(r2.json()['code']) + " " + r2.json()['description'] + ": " + r2.json()['message'])
	else:
		print("File succesfully uploaded.")

# Save the generated WSDL 2.0 to WSO2 Governance Registry
def saveToRepository2(resources, hrests_dict, save_dict):
	print("Authenticating to WSO2 Governance Registry as " + hrests_dict["username"] + " ...")
	print()
	url = hrests_dict["context"] + '/publisher/apis/authenticate'
	data={'username': hrests_dict["username"], 'password': hrests_dict["password"]}
	r = requests.post(url, data=data, verify=False)
	print()
	if (r.status_code == 200):
		version = input("Authentication success. Please enter the version of the WSDL 2.0 document: ")
		
		if "schemaLocation" not in resources: 
			print("Adding " + resources["service"] + ".wsdl version " + version + " to WSO2 Governance Registry ...")
		else:
			print("Adding " + resources["service"] + ".zip version " + version + " to WSO2 Governance Registry ...")
		
		print()
		filename = resources["service"] + ".wsdl"
		url = hrests_dict["context"] + '/publisher/assets/wsdl/apis/wsdls?type=wsdl'
		data={'wsdl': 'wsdl', 'wsdl_file': filename, 'filename': filename, 'wsdl_file_name': filename, 'file_version': version, 'addNewWsdlFileAssetButton': 'Create'}
		headers={'Cookie':'JSESSIONID=' + r.json()['data']['sessionId']}

		if "schemaLocation" not in resources: 
			files = {'wsdl_file': open("../wsdl/" + resources["service"] + ".wsdl", 'rb')}
		else:
			files = {'wsdl_file': open("../wsdl/" + resources["service"] + "/" + resources["service"] + ".zip", 'rb')}
		r2 = requests.post(url, data=data, verify=False, headers=headers, files=files)
		print()
		if (r2.status_code != 200):
			print(str(r2.json()['code']) + " " + r2.json()['description'] + ": " + r2.json()['message'])
		else:
			print("File succesfully uploaded.")

	else:
		print("Authentication failed. Consider uploading the file manually.")