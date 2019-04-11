#!/usr/bin/env python3
# coding=utf-8

# Libraries
from bs4 import BeautifulSoup
from urllib.parse import urlparse
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
				hrests_dict[k] = v.rstrip().lower()
		f.close()
	except IOError:
		f = open("tags.ini", 'w')
		f.write("[ATTRIBUTE VALUES]\n")
		f.write("service=service\n")
		f.write("operation=operation\n")
		f.write("id=id\n")
		f.write("method=method\n")
		f.write("endpoint=endpoint\n")
		f.write("input=input\n")
		f.write("output=output\n")
		f.write("param=param\n")
		f.write("\n")
		f.write("[CUSTOM ATTRIBUTES]\n")
		f.write("binding=data-binding\n")
		f.write("type=data-type\n")
		f.write("minOccurs=data-minoccurs\n")
		f.write("maxOccurs=data-maxoccurs\n")
		f.write("targetNamespace=data-targetnamespace\n")
		f.write("xsdnamespace=data-xsdnamespace\n")
		f.write("schemaLocation=data-schemalocation\n")
		f.write("message=data-message\n")
		f.close()

		hrests_dict["service"] = "service"
		hrests_dict["operation"] = "operation"
		hrests_dict["id"] = "id"
		hrests_dict["method"] = "method"
		hrests_dict["endpoint"] = "endpoint"
		hrests_dict["input"] = "input"
		hrests_dict["output"] = "output"
		hrests_dict["param"] = "param"
		hrests_dict["binding"] = "data-binding"
		hrests_dict["type"] = "data-type"
		hrests_dict["minOccurs"] = "data-minoccurs"
		hrests_dict["maxOccurs"] = "data-maxoccurs"
		hrests_dict["targetNamespace"] = "data-targetnamespace"
		hrests_dict["xsdnamespace"] = "data-xsdnamespace"
		hrests_dict["schemaLocation"] = "data-schemalocation"
		hrests_dict["message"] = "data-message"

	return hrests_dict

# Extract hRESTS resources using the dictionary
def html2resources(xhtml, hrests_dict):
	methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
	xsdTypes = ['anyUri',
							'base64Binary',
							'boolean',
							'byte',
							'date',
							'dateTime',
							'dateTimeStamp',
							'dayTimeDuration',
							'decimal',
							'double',
							'float',
							'gDay',
							'gMonth',
							'gMonthDay',
							'gYear',
							'gYearMonth',
							'hexBinary',
							'int',
							'integer',
							'language',
							'long',
							'Name',
							'NCName',
							'NMTOKEN',
							'negativeInteger',
							'nonNegativeInteger',
							'nonPositiveInteger',
							'normalizedString',
							'positiveInteger',
							'short',
							'string',
							'time',
							'token',
							'unsignedByte',
							'unsignedInt',
							'unsignedLong',
							'unsignedShort',
							'yearMonthDuration',
							'precisionDecimal',
							'duration',
							'QName',
							'ENTITY',
							'ID',
							'IDREF',
							'NOTATION',
							'IDREFS',
							'ENTITIES',
							'NMTOKENS']
	resources = {}
	soup = BeautifulSoup(xhtml, "lxml")
	try:
		service = soup.find(attrs={'class':hrests_dict['service']})
		resources["service"] = service.get('id').replace(" ", "")
		resources["targetNamespace"] = service.get(hrests_dict["targetNamespace"]).replace(" ", "")
		if urlparse(resources["targetNamespace"]).scheme == "":
			raise Exception("Error while extracting resources: target namespace must be a valid URI.")
		if service.has_attr(hrests_dict["xsdnamespace"]):
			resources["xsdnamespace"] = service.get(hrests_dict["xsdnamespace"]).replace(" ", "")
			if urlparse(resources["xsdnamespace"]).scheme == "":
				raise Exception("Error while extracting resources: xsd namespace must be a valid URI.")
			resources["schemaLocation"] = service.get(hrests_dict["schemaLocation"]).replace(" ","")
			if not resources["schemaLocation"].endswith(".xsd"):
				raise Exception("Error while extracting resources: schema location must be of xsd format.")
		resources["operations"] = []
		for operation in soup.findAll(attrs={'class': 'operation'}):
			op = {}
			op["name"] = operation.get('id').replace(" ", "")
			op["method"] = operation.find(attrs={'class':hrests_dict['method']}).text.replace(" ", "")
			if op["method"] not in methods:
				raise Exception("Error while parsing operation " + op["name"] + ": invalid REST method.")
			op["endpoint"] = operation.find(attrs={'class':hrests_dict['endpoint']}).text.replace(" ", "")
			if urlparse(op["endpoint"]).scheme == "":
				raise Exception("Error while parsing operation " + op["name"] + ": endpoint must be a valid URI.")
			if operation.find(attrs={'class':hrests_dict['endpoint']}).get(hrests_dict["binding"]):
				op["binding"] = operation.find(attrs={'class':hrests_dict['endpoint']}).get(hrests_dict["binding"]).replace(" ", "")
			op["input"] = {}
			inpObj = {}
			inpObj["params"] = []
			inputs = operation.find(attrs={'class':hrests_dict['input']})
			if inputs:
				if inputs.has_attr(hrests_dict["message"]):
					inpObj["message"] = inputs.get(hrests_dict["message"]).replace(" ", "")
				else:
					inpObj["message"] = op["name"] + "Request"
				for input in inputs.findAll(attrs={'class':hrests_dict['param']}):
					inp ={}
					inp["name"] = input.text.replace(" ", "")
					if input.has_attr(hrests_dict["type"]):
						inp["type"] = input.get(hrests_dict["type"])
					else:
						inp["type"] = "string"
					if inp["type"] not in xsdTypes:
						raise Exception("Error while parsing operation " + op["name"] + ": invalid datatype for param " + inp["name"] + ".")
					if input.has_attr(hrests_dict["minOccurs"]):
						inp["minOccurs"] = input.get(hrests_dict["minOccurs"])
						if not inp["minOccurs"].isdigit() and not inp["minOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": minOccurs for param " + inp["name"] + " must be a positive integer.")
					if input.has_attr(hrests_dict["maxOccurs"]):
						inp["maxOccurs"] = input.get(hrests_dict["maxOccurs"])
						if not inp["maxOccurs"].isdigit() and not inp["maxOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": maxOccurs for param " + inp["name"] + " must be a positive integer.")
					inpObj["params"].append(inp)
				op["input"] = inpObj
			op["output"] = {}
			outObj = {}
			outObj["params"] = []
			outputs = operation.find(attrs={'class':hrests_dict['output']})
			if outputs:
				if outputs.has_attr(hrests_dict["message"]):
					outObj["message"] = outputs.get(hrests_dict["message"]).replace(" ", "")
				else:
					outObj["message"] = op["name"] + "Response"
				for output in outputs.findAll(attrs={'class':hrests_dict['param']}):
					out ={}
					out["name"] = output.text.replace(" ", "")
					if output.has_attr(hrests_dict["type"]):
						out["type"] = output.get(hrests_dict["type"])
					else:
						out["type"] = "string"
					if inp["type"] not in xsdTypes:
						raise Exception("Error while parsing operation " + op["name"] + ": invalid datatype for param " + inp["name"] + ".")
					if output.has_attr(hrests_dict["minOccurs"]):
						out["minOccurs"] = out.get(hrests_dict["minOccurs"])
						if not inp["minOccurs"].isdigit() and not inp["minOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": minOccurs for param " + inp["name"] + " must be a positive integer.")
					if output.has_attr(hrests_dict["maxOccurs"]):
						out["maxOccurs"] = output.get(hrests_dict["maxOccurs"])
						if not inp["maxOccurs"].isdigit() and not inp["maxOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": maxOccurs for param " + inp["name"] + " must be a positive integer.")
					outObj["params"].append(out)
				op["output"] = outObj
			resources["operations"].append(op)
		return resources
	except Exception as e:
		print(e)
		print("Check your HTML document.")
		sys.exit()

# Generate WSDL 2.0 document
def generateWSDL2(resources):
	xml = """<?xml version="1.0"?> 
<wsdl:description xmlns:wsdl="http://www.w3.org/ns/wsdl"
	"""
	xml += "targetNamespace=\"" + resources["targetNamespace"] + "\"\n"
	xml += "	xmlns:tns=\"" + resources['targetNamespace'] + "\"\n"
	xml += "	xmlns:msg=\"" + resources['targetNamespace'] + "\"\n"
	xml += """	xmlns:whttp="http://www.w3.org/ns/wsdl/http"
	xmlns:wsdlx="http://www.w3.org/ns/wsdl-extensions">

	"""

	xml += """<wsdl:types>
    """
	if "xsdnamespace" in resources:
		xml += "<xsd:import xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"\n"
		xml += "			namespace=\"" + resources["xsdnamespace"] + "\"\n"
		xml += "			schemaLocation=\"" + resources["schemaLocation"] + "\"/>\n"
	else:		
		xml += "<xsd:schema xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"\n"
		xml += "			targetNamespace=\"" + resources["targetNamespace"] + "\">\n"
		for op in resources["operations"]:
			xml += "			<xsd:element name=\"" + op["input"]["message"] + "\">\n"
			xml += "				<xsd:complexType>\n"
			xml += "					<xsd:sequence>\n"
			for inp in op["input"]["params"]:
				xml += "						<xsd:element name=\"" + inp["name"] + "\" type=\"xsd:" + inp["type"] + "\""
				if "minOccurs" in inp:
					xml += " minOccurs=\"" + inp["minOccurs"] + "\""
				if "maxOccurs" in inp:
					xml += " maxOccurs=\"" + inp["maxOccurs"] + "\""
				xml += "/>\n"
			xml += """					</xsd:sequence>		
				</xsd:complexType>
	  	</xsd:element>
"""
			xml += "			<xsd:element name=\"" + op["output"]["message"] + "\">\n"
			xml += "				<xsd:complexType>\n"
			xml += "					<xsd:sequence>\n"
			for out in op["output"]["params"]:
				xml += "						<xsd:element name=\"" + out["name"] + "\" type=\"xsd:" + out["type"] + "\""
				if "minOccurs" in out:
					xml += " minOccurs=\"" + out["minOccurs"] + "\""
				if "maxOccurs" in inp:
					xml += " maxOccurs=\"" + out["maxOccurs"] + "\""
				xml += "/>\n"
			xml += """					</xsd:sequence>		
				</xsd:complexType>
	  	</xsd:element>
	  """
		xml += """</xsd:schema>
"""
	xml += """	</wsdl:types>

  """

	xml += "<wsdl:interface name=\"" + resources["service"] + "Interface\">\n"
	for op in resources["operations"]:
		xml += "		<wsdl:operation name=\"" + op["name"] + "\"\n"
		xml += """			pattern="http://www.w3.org/ns/wsdl/in-out"
			"""
		if op["method"] == "GET":
			xml += """wsdlx:safe="true"
			"""
		xml += """style="http://www.w3.org/ns/wsdl/style/iri">
			"""
		xml += "<wsdl:input element=\"msg:" + op["input"]["message"] + "\"/>\n"
		xml += "			<wsdl:output element=\"msg:" + op["output"]["message"] + "\"/>\n"
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

	f = open(resources["service"] + ".wsdl", 'w')
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
	try:
		html = requests.get(hrests_url).text
	except:
		print("Could not retrieve source page, check your connection.")
		sys.exit(1)
	if isinstance (html, tuple):
		print(html[0])
		print('%s : %s' % (html[1], html[2]))
		sys.exit()
	else:
		resources = html2resources(html, generateDictionary())
		generateWSDL2(resources)
		print(resources)

