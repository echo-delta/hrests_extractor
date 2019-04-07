#!/usr/bin/env python3

# Libraries
from bs4 import BeautifulSoup
import requests, sys, http.client, urllib

# Convert HTML to XHTML using html2xhtml API by Jesús Arias Fisteus
# http://www.it.uc3m.es/jaf/html2xhtml/web-api.html
def html2xhtml(hrests_url):
	headers = {"Content-type": "text/html",
           "Accept": "application/xhtml+xml"}
	params = urllib.parse.urlencode({'tablength': 4,
	                           'linelength': 100,
	                           'output-charset': 'UTF-8'})
	url = "/jaf/cgi-bin/html2xhtml.cgi?" + params
	conn = http.client.HTTPConnection("www.it.uc3m.es:80")
	try:
		conn.request("POST", url, requests.get(hrests_url).text, headers)
		response = conn.getresponse()

		if response.status == 200:
		    htmltext = response.read()
		    return htmltext.decode("utf-8")
		else:
		    return sys.stderr, response.status, response.reason

		conn.close()

	except Exception as e:
		print(e)
		sys.exit()

# Generate hRESTS dictionary using tags.ini
def generateDictionary():
	hrests_dict = {}

	try:
		f = open("tags.ini", "r")
		for line in f:
			if len(line) > 1 and line[0] != '[':
				k, v = line.split('=', 1)
				hrests_dict[k] = v.rstrip()
		f.close()
	except IOError:
		f = open("tags.ini", 'w')
		f.write("[TAGS]\n")
		f.write("\n")
		f.write("operation=operation\n")
		f.write("id=id\n")
		f.write("label=label\n")
		f.write("method=method\n")
		f.write("address=address\n")
		f.write("optional-input=optional-input\n")
		f.write("output=output\n")
		f.close()

		hrests_dict["operation"] = "operation"
		hrests_dict["id"] = "id"
		hrests_dict["label"] = "label"
		hrests_dict["method"] = "method"
		hrests_dict["address"] = "address"
		hrests_dict["optional-input"] = "optional-input"
		hrests_dict["output"] = "output"

	return hrests_dict

# Extract hRESTS resources using the dictionary
def xhtml2resources(xhtml, hrests_dict):
	soup = BeautifulSoup(xhtml, "lxml")
	try:
		for operation in soup.findAll('div', {'class': 'operation'}):
			print(operation.get('id'))
			print("label: " + operation.find('code', {'class':hrests_dict['label']}).text)
			print("method: " + operation.find('span', {'class':hrests_dict['method']}).text)
			print("address: " + operation.find('code', {'class':hrests_dict['address']}).text)
			if operation.find('span', {'class':hrests_dict['optional-input']}):
				print('optional input:')
				for code in operation.find('span', {'class':hrests_dict['optional-input']}).findAll('code'):
					print(code.text)
			print("output: " + operation.find('span', {'class':hrests_dict['output']}).find('code').text)
	except Exception as e:
		print(e)
		sys.exit()

# Main Program
if len(sys.argv) < 2:
  print('Usage: %s <hRESTS URL address>' % sys.argv[0])
  print('Press any key to exit.')
  input()
  sys.exit(1)
else:
	hrests_url = sys.argv[1]
	xhtml = html2xhtml(str(hrests_url).replace('"', ''))
	if isinstance (xhtml, tuple):
		print(xhtml[0])
		print('%s : %s' % (xhtml[1], xhtml[2]))
		sys.exit()
	else:
		xhtml2resources(xhtml, generateDictionary())
