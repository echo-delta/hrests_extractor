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
		print("Check your connection.")
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
		f.write("[ATTRIBUTE VALUES]\n")
		f.write("\n")
		f.write("service=service\n")
		f.write("operation=operation\n")
		f.write("id=id\n")
		f.write("method=method\n")
		f.write("endpoint=endpoint\n")
		f.write("input=input\n")
		f.write("output=output\n")
		f.write("[CUSTOM ATTRIBUTES")
		f.write("binding=data-binding")
		f.close()

		hrests_dict["service"] = "service"
		hrests_dict["operation"] = "operation"
		hrests_dict["id"] = "id"
		hrests_dict["method"] = "method"
		hrests_dict["endpoint"] = "endpoint"
		hrests_dict["input"] = "input"
		hrests_dict["output"] = "output"
		hrests_dict["binding"] = "data-binding"

	return hrests_dict

# Extract hRESTS resources using the dictionary
def xhtml2resources(xhtml, hrests_dict):
	resources = {}
	soup = BeautifulSoup(xhtml, "lxml")
	try:
		resources["service"] = soup.find(attrs={'class':hrests_dict['service']}).get('id')
		resources["operations"] = []
		for operation in soup.findAll(attrs={'class': 'operation'}):
			op = {}
			op["name"] = operation.get('id')
			op["method"] = operation.find(attrs={'class':hrests_dict['method']}).text
			op["endpoint"] = operation.find(attrs={'class':hrests_dict['endpoint']}).text
			if operation.find(attrs={'class':hrests_dict['endpoint']}).get(hrests_dict["binding"]):
				op["binding"] = operation.find(attrs={'class':hrests_dict['endpoint']}).get(hrests_dict["binding"])
			if operation.find(attrs={'class':hrests_dict['input']}):
				op["input"] = []
				for code in operation.find(attrs={'class':hrests_dict['input']}).findAll('code'):
					op["input"].append(code.text)
			op["output"] = operation.find(attrs={'class':hrests_dict['output']}).find('code').text
			resources["operations"].append(op)
		return resources
	except Exception as e:
		print(e)
		print("Make sure all tag attributes are used correctly.")
		sys.exit()

# Generate WSDL 2.0 document
def generateWSDL2(resources):
	resources["targetNamespace"] = "http://www.bookstore.org/booklist/wsdl"

	xml = """<wsdl:description xmlns:wsdl="http://www.w3.org/ns/wsdl"
	"""
	xml += "xmlns:tns=\"" + resources['targetNamespace'] + "\"\n"
	xml += """	xmlns:whttp="http://www.w3.org/ns/wsdl/http"
	xmlns:wsdlx="http://www.w3.org/ns/wsdl-extensions">

	"""

	xml += "<wsdl:interface name=\"" + resources["service"] + "Interface\">\n"
	for op in resources["operations"]:
		xml += "		<wsdl:operation name=\"" + op["name"] + "\"\n"
		xml += """			pattern="http://www.w3.org/ns/wsdl/in-out"
			style="http://www.w3.org/ns/wsdl/style/iri"
			wsdlx:safe="true">
			"""
		xml += "<wsdl:input element=\"msg:" + op["name"] + "-input\"/>\n"
		xml += "			<wsdl:output element=\"msg:" + op["name"] + "-output\"/>\n"
		xml += "		</wsdl:operation>\n"
	xml += """	</wsdl:interface>

	"""

	endpoints = set(op["endpoint"] for op in resources["operations"])
	counter = 0
	for endpoint in endpoints:
		opBinding = None
		try:
			opBinding = next (op for op in resources["operations"] if op["endpoint"] == endpoint and "binding" in op)
		except:
			opBinding = next (op for op in resources["operations"] if op["endpoint"] == endpoint)
		binding = ""
		httpEndpoint = ""
		if "binding" in opBinding:
			binding = opBinding["binding"] + "HTTPBinding"
			httpEndpoint = opBinding["binding"] + "HTTPEndpoint"
		else:
			binding = resources["service"] + "HTTPBinding" + str(counter)
			httpEndpoint = resources["service"] + "HTTPEndpoint" + str(counter)
			counter += 1
		xml += "<wsdl:binding name=\"" + binding + "\"\n"
		xml += """		type="http://www.w3.org/ns/wsdl/http"
    interface="tns:BookListInterface">
"""
		for op in resources["operations"]:
			if op["endpoint"] == endpoint:
				op["binding"] = binding
				op["httpEndpoint"] = httpEndpoint
				xml += "		<wsdl:operation ref=\"tns:" + op["name"] + "\" whttp:method=\"" + op["method"] + "\"/>\n"
		xml += """  </wsdl:binding>

  """

	xml += "<wsdl:service name=\"" + resources["service"] + "\" interface=\"tns:" + resources["service"] + "Interface\">\n"
	for endpoint in endpoints:
		opBinding = next (op for op in resources["operations"] if op["endpoint"] == endpoint)
		xml += "		<wsdl:endpoint name=\"" + opBinding["httpEndpoint"] + "\"\n"
		xml += "			binding=\"tns:" + opBinding["binding"] + "\"\n"  
		xml += "			address=\"" + endpoint + "\">\n"
		xml += "		</wsdl:endpoint>\n"
	xml += """	</wsdl:service>
</wsdl:description>"""

	f = open("res.xml", 'w')
	f.write(xml)
	f.close()

# Main Program
if len(sys.argv) < 2:
  print('Usage: %s <hRESTS URL address>' % sys.argv[0])
  print('Press any key to exit.')
  input()
  sys.exit(1)
else:
	hrests_url = sys.argv[1]
	# xhtml = html2xhtml(str(hrests_url).replace('"', ''))
	xhtml = requests.get(hrests_url).text
	if isinstance (xhtml, tuple):
		print(xhtml[0])
		print('%s : %s' % (xhtml[1], xhtml[2]))
		sys.exit()
	else:
		resources = xhtml2resources(xhtml, generateDictionary())
		generateWSDL2(resources)
		# print(resources)

