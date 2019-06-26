#!/usr/bin/env python3
# coding=utf-8

# Libraries
from bs4 import BeautifulSoup
from lxml import etree
from lxml import html
from lxml.etree import tostring
from lxml.builder import E
from urllib.parse import urlparse
from io import StringIO
import requests, sys, http.client, urllib

# Generate hRESTS dictionary using config.ini
def generateDictionary():
	hrests_dict = {}

	try:
		f = open("../config/config.ini", "r")
		for line in f:
			if len(line) > 1 and line[0] != '[':
				k, v = line.split('=', 1)
				hrests_dict[k] = v.rstrip().lower()
		f.close()
	except IOError:
		f = open("../config/config.ini", 'w')
		f.write("[XPATH QUERIES]\n")
		f.write("service=service\n")
		f.write("operation=operation\n")
		f.write("method=method\n")
		f.write("endpoint=endpoint\n")
		f.write("input=input\n")
		f.write("output=output\n")
		f.write("param=param\n")
		f.write("\n")
		f.write("[CUSTOM ATTRIBUTES]\n")
		f.write("serviceName=id\n")
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
		hrests_dict["method"] = "method"
		hrests_dict["endpoint"] = "endpoint"
		hrests_dict["input"] = "input"
		hrests_dict["output"] = "output"
		hrests_dict["param"] = "param"
		hrests_dict["serviceName"] = "id"
		hrests_dict["binding"] = "data-binding"
		hrests_dict["type"] = "data-type"
		hrests_dict["minOccurs"] = "data-minoccurs"
		hrests_dict["maxOccurs"] = "data-maxoccurs"
		hrests_dict["targetNamespace"] = "data-targetnamespace"
		hrests_dict["xsdnamespace"] = "data-xsdnamespace"
		hrests_dict["schemaLocation"] = "data-schemalocation"
		hrests_dict["message"] = "data-message"

	return hrests_dict

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
			print("Warning: no binding name specified for " + op["name"] + ", resolved using default name " + binding)
			counter += 1
		xml += "<wsdl:binding name=\"" + binding + "\"\n"
		xml += "		type=\"http://www.w3.org/ns/wsdl/http\"\n"
		xml += "		interface=\"tns:" + resources["service"] + "Interface\">\n"

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

	f = open("../wsdl/" + resources["service"] + ".wsdl", 'w')
	f.write(xml)
	f.close()

# Extract html document micorformats to resources using the xpath
def html2resourcesxpath(html_text, hrests_dict):
	root = html.document_fromstring(html_text)

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

	try:
		service = root.xpath(hrests_dict["service"])[0]
		resources["service"] = service.get(hrests_dict["serviceName"]).replace(" ", "")
		if len(resources["service"]) == 0:
			raise Exception("Error while extracting resources: service name can\'t be empty.")
		resources["targetNamespace"] = service.get(hrests_dict["targetNamespace"]).replace(" ", "")
		if len(resources["targetNamespace"]) == 0:
			raise Exception("Error while extracting resources: targetNamespace can\'t be empty.")
		if urlparse(resources["targetNamespace"]).scheme == "":
			raise Exception("Error while extracting resources: target namespace must be a valid URI.")
		if hrests_dict["xsdnamespace"] in service.attrib:
			print("Warning: XSD Namespace found. Only 1 XSD can be imported.")
			resources["xsdnamespace"] = service.get(hrests_dict["xsdnamespace"]).replace(" ", "")
			if urlparse(resources["xsdnamespace"]).scheme == "":
				raise Exception("Error while extracting resources: xsd namespace must be a valid URI.")
			resources["schemaLocation"] = service.get(hrests_dict["schemaLocation"]).replace(" ","")
			if not resources["schemaLocation"].endswith(".xsd") and urlparse(resources["schemaLocation"]).scheme == "":
				print("Warning: schemaLocation is not of xsd format or valid URI")
		resources["operations"] = []
		for operation in service.xpath(hrests_dict["operation"]):
			op = {}
			op["name"] = operation.get('id').replace(" ", "")
			op["method"] = operation.xpath(hrests_dict["method"])[0].text_content().replace(" ", "").upper()
			if op["method"] not in methods:
				raise Exception("Error while parsing operation " + op["name"] + ": invalid REST method.")
			endpoint = operation.xpath(hrests_dict["endpoint"])[0]
			op["endpoint"] = endpoint.text_content().replace(" ", "")
			if urlparse(op["endpoint"]).scheme == "":
				raise Exception("Error while parsing operation " + op["name"] + ": endpoint must be a valid URI.")
			if endpoint.get(hrests_dict["binding"]):
				if len(endpoint.get(hrests_dict["binding"]).replace(" ", "")) > 0:
					op["binding"] = endpoint.get(hrests_dict["binding"]).replace(" ", "")
			op["input"] = {}
			inpObj = {}
			inpObj["params"] = []
			inputs = operation.xpath(hrests_dict["input"])[0]
			if inputs is not None:
				if hrests_dict["message"] in inputs.attrib:
					if len(inputs.get(hrests_dict["message"]).replace(" ", "")) > 0:
						inpObj["message"] = inputs.get(hrests_dict["message"]).replace(" ", "")
					else:
						inpObj["message"] = op["name"] + "Request"
						print("Warning: no message name specified for " + op["name"] + ", resolved using default name " + inpObj["message"])
				else:
					inpObj["message"] = op["name"] + "Request"
					print("Warning: no message name specified for " + op["name"] + ", resolved using default name " + inpObj["message"])
				for input in inputs.xpath(hrests_dict["param"]):
					inp ={}
					inp["name"] = input.text_content().replace(" ", "")
					if len(inp["name"]) == 0:
						raise Exception("Error while extracting resources: input parameter name can\'t be empty.")
					if hrests_dict["type"] in input.attrib:
						inp["type"] = input.get(hrests_dict["type"])
					else:
						inp["type"] = "string"
						print("Warning: no message name specified for " + inp["name"] + " of " + op["name"] + ", resolved using default type string")
					if inp["type"] not in xsdTypes:
						raise Exception("Error while parsing operation " + op["name"] + ": invalid datatype for param " + inp["name"] + ".")
					if hrests_dict["minOccurs"] in input.attrib:
						inp["minOccurs"] = input.get(hrests_dict["minOccurs"])
						if not inp["minOccurs"].isdigit() and not inp["minOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": minOccurs for param " + inp["name"] + " must be a positive integer.")
					if hrests_dict["maxOccurs"] in input.attrib:
						inp["maxOccurs"] = input.get(hrests_dict["maxOccurs"])
						if not inp["maxOccurs"].isdigit() and not inp["maxOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": maxOccurs for param " + inp["name"] + " must be a positive integer.")
					inpObj["params"].append(inp)
			else:
				inpObj["message"] = op["name"] + "Request"
				print("Warning: no message name specified for " + op["name"] + ", resolved using default name " + inpObj["message"])
			op["input"] = inpObj

			op["output"] = {}
			outObj = {}
			outObj["params"] = []
			outputs = operation.xpath(hrests_dict["output"])[0]
			if outputs is not None:
				if hrests_dict["message"] in outputs.attrib:
					if len(outputs.get(hrests_dict["message"]).replace(" ", "")) > 0:
						outObj["message"] = outputs.get(hrests_dict["message"]).replace(" ", "")
					else:
						outObj["message"] = op["name"] + "Response"
						print("Warning: no message name specified for " + op["name"] + ", resolved using default name " + outObj["message"])
				else:
					outObj["message"] = op["name"] + "Response"
					print("Warning: no message name specified for " + op["name"] + ", resolved using default name " + outObj["message"])
				for output in outputs.xpath(hrests_dict["param"]):
					out ={}
					out["name"] = output.text_content().replace(" ", "")
					if len(out["name"]) == 0:
						raise Exception("Error while extracting resources: output parameter name can\'t be empty.")
					if hrests_dict["type"] in output.attrib:
						out["type"] = output.get(hrests_dict["type"])
					else:
						out["type"] = "string"
						print("Warning: no message name specified for " + out["name"] + " of " + op["name"] + ", resolved using default type string")
					if out["type"] not in xsdTypes:
						raise Exception("Error while parsing operation " + op["name"] + ": invalid datatype for param " + out["name"] + ".")
					if hrests_dict["minOccurs"] in output.attrib:
						out["minOccurs"] = output.get(hrests_dict["minOccurs"])
						if not out["minOccurs"].isdigit() and not out["minOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": minOccurs for param " + out["name"] + " must be a positive integer.")
					if hrests_dict["maxOccurs"] in output.attrib:
						out["maxOccurs"] = output.get(hrests_dict["maxOccurs"])
						if not out["maxOccurs"].isdigit() and not out["maxOccurs"] == "unbounded":
							raise Exception("Error while parsing operation " + op["name"] + ": maxOccurs for param " + out["name"] + " must be a positive integer.")
					outObj["params"].append(out)
			else:
				outObj["message"] = op["name"] + "Response"
				print("Warning: no message name specified for " + op["name"] + ", resolved using default name " + outObj["message"])
			op["output"] = outObj

			resources["operations"].append(op)
		return resources

	except Exception as e:
		print(e)
		print("Check your HTML document.")
		sys.exit()

# Main Program
if len(sys.argv) < 2:
  print('Usage: %s <hRESTS URL address>' % sys.argv[0])
  print('Press Enter to exit.')
  input()
  sys.exit(1)
else:
	hrests_url = sys.argv[1]
	try:
		html_text = requests.get(hrests_url).text
	except:
		print("Could not retrieve source page, check your connection.")
		sys.exit(1)
	if isinstance (html_text, tuple):
		print(html_text[0])
		print('%s : %s' % (html_text[1], html_text[2]))
		sys.exit()
	else:
		resources = html2resourcesxpath(html_text, generateDictionary())
		generateWSDL2(resources)
		print()
		print(resources)
