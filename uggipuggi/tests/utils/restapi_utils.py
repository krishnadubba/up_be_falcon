
def curl_request(url, method, headers, payloads=None):
    # construct the curl command from request
    command = "curl -v -H {headers} {data} -X {method} {uri}"
    data = "" 
    if payloads:
        payload_list = ['"{0}":"{1}"'.format(k,v) for k,v in payloads.items()]
        data = " -d '{" + ", ".join(payload_list) + "}'"
    header_list = ['"{0}: {1}"'.format(k, v) for k, v in headers.items()]
    header = " -H ".join(header_list)
    print(command.format(method=method, headers=header, data=data, uri=url))