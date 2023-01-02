import requests
import sys
from bs4 import BeautifulSoup as bs
import re

# If you have problems with device functions, the most likely cause is a different XML/SOAP schema in your Fetch
# box config than mine, resulting in a response from the device that does not match the expected content that is
# the basis of parsing here. See IN CASE OF ISSUES below (about line 60) for guidance.

# USER VARIABLES
# PATH_CTRL_URL: This is the URL for the specific service to receive requests. Get this in uPNP Device Spy by right-
# clicking the top level device, Get Device XML, and combine the <controlURL> for the service with HOST_URL (see below).
# HOST_URL: Network address & port. In uPNP Device Spy, this is Base URL in the device properties (exclude trailing /).
# SERVICE_TYPE: This is the <serviceType> for the service in Get Device XML (preserve the double quotes used here).
PATH_CTRL_URL = "http://192.168.1.5:49152/web/cds_control"  # include http://
HOST_URL = "http://192.168.1.5:49152"  # eg http://192.168.1.100:4000, exclude trailing /
SERVICE_TYPE = '"urn:schemas-upnp-org:service:ContentDirectory:1#Browse"'  # preserve double quoting eg '"data"'


def get_children(param):

    # Get result from browsing direct children of a given object ID, then assemble
    # child info as list and return. param is an int as string for a single ObjectID.

    # build SOAP request
    body = """<?xml version="1.0" encoding="utf-8"?>
     <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
        <s:Body>
          <u:Browse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
             <ObjectID>""" + param + """</ObjectID>
             <BrowseFlag>BrowseDirectChildren</BrowseFlag>
             <Filter />
             <StartingIndex>0</StartingIndex>
             <RequestedCount>0</RequestedCount>
             <SortCriteria />
          </u:Browse>
        </s:Body>
     </s:Envelope>"""
    bytes_in_body = str(sys.getsizeof(body))
    headers = {'HOST': HOST_URL, 'SOAPACTION': SERVICE_TYPE,
               'CONTENT-LENGTH': bytes_in_body, 'CONTENT-TYPE': 'text/xml; charset="utf-8"'}

    # Extract result from SOAP envelope and convert to XML fragment
    response = requests.post(PATH_CTRL_URL, data=body, headers=headers)
    bs_data = bs(response.text, 'xml')
    result = bs_data.find('Result')
    result = str(result)
    cleanup = {"<Result>": "", "</Result>": "", "&lt;": "<", "&gt;": ">"}
    for key, value in cleanup.items():
        result = result.replace(key, value)

    # For each <container> in result, get attribute values for id, parentID, childCount,
    # and contents of <dc.title>, clean up, and assemble into list; similar for <item>
    # but no childCount. Skip if neither of these (usually because the item has no children).
    bs_data = bs(result, 'xml')

    # ***** IN CASE OF ISSUES *****
    # print(bs_data)  # Start diagnosing by uncommenting this line to test if any XML response is making it in this far.
    #
    # If there is an XML response with the kind of data you expected, the problem lies in parsing the response below.
    #
    # If there is a meaningful XML response but not data you expected, the problem lies in the <s:body> of the SOAP
    # message within var body above. Start investigating with the XML schema for the Service (right-click the service
    # in uPNP Device Spy and Get Service XML).
    #
    # If there is a fault XML response, the problem is in var body above (eg message is not what the service expects).
    # If there is no connection, the problem is in var header above.
    #
    # Start diagnosing by getting an example of a working SOAP request in uPNP Device Spy. Right click the action you
    # want to access, Invoke Action, and experiment with object references (eg, 0) and other arguments until you
    # get a working result. Right-click the top of the window and toggle Show Packet Capture to see the body and
    # headers sent that yielded the result.
    # *******************************

    children = []

    containers = bs_data.find_all('container')
    items = bs_data.find_all('item')
    if containers != []:
        for ea in containers:
            # fetch
            id = re.search('id="\d*', str(ea))
            parentID = re.search('parentID="\d*', str(ea))
            childCount = re.search('childCount="\d*', str(ea))
            name = re.search('<dc:title>.*</dc:title>', str(ea))
            # clean up and add to list
            id = id.group().replace('id="', '')
            parentID = parentID.group().replace('parentID="', '')
            childCount = childCount.group().replace('childCount="', '')
            name = name.group().replace('<dc:title>', '')
            name = name.replace('</dc:title>', '')
            name = name.replace('ampaposs', 's')
            name = name.replace('ampamp', 'And')
            child = {"id": id, "parentID": parentID, "childCount": childCount, "name": name, "type": "container"}
            children.append(child)
    elif items != []:
        for ea in items:
            # fetch
            id = re.search('id="\d*', str(ea))
            parentID = re.search('parentID="\d*', str(ea))
            name = re.search('<dc:title>.*</dc:title>', str(ea))
            # clean up and add to list
            id = id.group().replace('id="', '')
            parentID = parentID.group().replace('parentID="', '')
            name = name.group().replace('<dc:title>', '')
            name = name.replace('</dc:title>', '')
            child = {"id": id, "parentID": parentID, "name": name, "type": "item"}
            children.append(child)
    else:
        # Usual scenario for triggering this is searching an empty container/no children found.
        # Could also happen with malformed data or custom schemas (consider this if no usable data obtained at all).
        pass

    return children

