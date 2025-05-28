import argparse
import subprocess
import re
import json
from os import waitid
from wsgiref.util import request_uri
from django.contrib.gis.geos.prototypes.prepared import prepared_intersects
from psycopg.types.json import set_json_dumps
from zapv2 import wappalyzer
import time
from pprint import pprint
from zapv2 import ZAPv2
from collections import defaultdict
from urllib.parse import urlparse

# Execute a command using the shell
# command = "ls -l"
# result = subprocess.run(command, shell=True, capture_output=True, text=True)
#print(result.stdout)
ZapApiKey= "a16jpq95fjfrnsm7ai09k0nsle"
mainHook="http://localhost:5678/webhook-test/539a4b30-240b-4e2f-a116-0b0aa6d55792"

# Define functions for each module/task
def nmapFullScan(a):
    command = "sudo nmap -sSCV -O -AT5 -oX nmap/nmap.xml "+a+" > nmap/nmapResult.txt"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
def nmapQuickScan(a):
    print("hello")
def readNmap():
    f = open("nmap/nmapResult.txt", "r")
    ans=""
    for i in f:
        ans+=i
    f.close()
    return ans
def validateNmap():
    o = open("nmap/nmapResult.txt", "r")
    te = ""
    for i in o:
        te += i.replace('''\\\\n''', '\n')
    ls = te.split("\n")
    ans = []
    for i in ls:
        if (re.match(r'^\d', i)):
            ans.append(i)
        if (i.__contains__("TRACEROUTE")):
            break
    fans = ""
    for i in ans:
        fans += i
        fans += "\n"
    o.close()
    return(fans)
def validateNmapService():
    f = validateNmap()
    f=f.strip()
    lst = []
    ans = []
    for i in f.split("\n"):
        lst.append(i.split(" "))
    for i in lst:
        cleaned_data = list(filter(None, i))
        ans.append(cleaned_data)
    for i in ans:
        for j in i[3:]:
            print(j,end=" ")
        print()
def metasploitGenerate():
    f = open("ApacheWebDocker/website/searchsploitNmap.txt","r")
    ans = ""
    for i in f:
        if(i.__contains__("Metasploit")):
            ans+=i
    print(ans)

def normalExecute(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return(result.stdout)

def searchSploitEx(type):
    if(type=="nmap"):
        result = normalExecute("searchsploit -j --nmap nmap/nmap.xml > nmap/searchSploitNmap.txt")
        searchSploitNmapValidate()
    elif(type=="webanalyzer"):
        searchSploitWebanalyzer()
def searchSploitNmapValidate():
    f = open("nmap/searchSploitNmap.txt", "r")
    s = ""
    for i in f:
        s = s + str(i)
    s = s.split("\n\n\n")
    f.close()
    for i in s[0:len(s)-1]:
        temp = json.loads(i)
        print(temp['SEARCH'])
        if (len(temp['RESULTS_EXPLOIT']) == 0):
            print("NONE\n")
            continue
        for i in temp['RESULTS_EXPLOIT']:
            if (str(i['Title']).__contains__("PoC") or str(i['Title']).__contains__("Metasploit") or str(i['Title']).__contains__("metasploit") or str(i['Source']).__contains__("PoC") or str(i['Source']).__contains__("poc")):
                print(i['Title'] + "\t|\t" + i['Codes'] + "\t|\t" + i['Source'])
        print("")
def searchSploitWebanalyzer():
    t = normalExecute("cat webanalyzer/output.txt")
    lst = []
    for i in t.split("\n"):
        lst.append(i)
    if(len(lst)>0):
        lst=lst[0:len(lst)-1]
    normalExecute("echo \"\" > searchsploit/webanalyzerTemp.txt")
    for i in lst:
        temp = json.loads(normalExecute("searchsploit -j "+i))
        print(temp['SEARCH'])
        ans = []
        for i in temp['RESULTS_EXPLOIT']:
            if (str(i['Title']).__contains__("PoC") or str(i['Source']).__contains__("PoC") or str(i['Source']).__contains__("poc")):
                ans.append(i['Title'] + "\t|\t" + i['Codes'] + "\t|\t" + i['Source'])
        if (len(ans) == 0):
            print("NONE\n")
            continue
        for i in ans:
            print(i)
        print("")

def domainAdd(str):
    if(len(str.split(" "))<3):
        return
    add=[]
    add.append(str.split(" ")[2])
    add.append(str.split(" ")[1])

    f = open("/etc/hosts", "r")
    lst = []
    for i in f:
        lst.append(i.split())
    f.close()
    if (add not in lst):
        lst.append(add)
        f = open("/etc/hosts", "w")
        for i in lst:
            f.write(i[0] + "\t" + i[1] + "\n")
        f.close()
def webanalyzer(a):
    i=a.split(" ")
    target = i[0] + "://" + i[1]
    command = "wappy -b " + target
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    temp = result.stdout

    ans = ""
    for i in temp.split("\n"):
        for j in i.split()[1:]:
            ans += j + " "
        ans += "\n"
    print(ans)
    normalExecute("echo \"" + ans.strip() + "\" > webanalyzer/output.txt")

def zapFullScan(target):
    c = str(target.split()[0] + "://" + target.split()[1])
    ZapSpider(c)
    ZapAspider(c)
    ZapActive(c)
    return

def ZapSpider(a):
    zap = ZAPv2(apikey=ZapApiKey)
    # Use the line below if ZAP is not listening on port 8080, for example, if listening on port 8090
    # zap = ZAPv2(apikey=apiKey, proxies={'http': 'http://127.0.0.1:8090', 'https': 'http://127.0.0.1:8090'})

    print('Spidering target {}'.format(a))
    # The scan returns a scan id to support concurrent scanning
    scanID = zap.spider.scan(a)
    while int(zap.spider.status(scanID)) < 100:
        # Poll the status until it completes
        print('Spider progress %: {}'.format(zap.spider.status(scanID)))
        time.sleep(1)

    print('Spider has completed!')
    # Prints the URLs the spider has crawled

    output=('\n'.join(map(str, zap.spider.results(scanID))))
    f = open("zap/spider.txt","w")
    f.write(output)
    f.close()

def buildSpiderTree():
    urls = []

    f = open("zap/spider.txt", "r")
    for i in f:
        urls.append(str(i).replace('\n', ''))

    tree = build_tree(urls)
    #print(f"http://{list(tree.keys())[0]}/")
    print_tree(tree[list(tree.keys())[0]])
def build_tree(urls):
    tree = defaultdict(dict)

    # Parse each URL and build the nested dictionary structure
    for url in urls:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        subtree = tree[parsed_url.netloc]

        for part in path_parts:
            subtree = subtree.setdefault(part, {})

    return tree
def print_tree(tree, prefix=""):
    for key, value in tree.items():
        print(f"{prefix}├── {key}")
        if isinstance(value, dict) and value:
            print_tree(value, prefix + "│   ")
def txt_to_html(txt_path, html_path):
    with open(txt_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # HTML structure with added CSS styling for better presentation
    html_content = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<title>Directory Structure</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; }",
        ".directory { margin: 20px; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }",
        ".directory pre { font-family: monospace; color: #4A5568; line-height: 1; font-size: 14px; margin: 0; padding: 0;}",
        ".folder { color: #2b6cb0; font-weight: bold; }",
        ".file { color: #6b7280; }",
        ".pipe { color: #CBD5E0; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class='directory'><pre>"
    ]

    for line in lines:
        # Replace the tree characters with HTML-safe equivalents
        formatted_line = line.replace("├──", "<span class='pipe'>|--</span>") \
            .replace("└──", "<span class='pipe'>`--</span>")
        # Add classes for folders and files to color them differently
        if re.search(r"\.[a-zA-Z0-9]+$", line):  # Simple check for file extensions
            formatted_line = f"<span class='file'>{formatted_line}</span>"
        else:
            formatted_line = f"<span class='folder'>{formatted_line}</span>"

        # Replace leading spaces with non-breaking spaces for indentation
        formatted_line = re.sub(r"^(\s+)", lambda m: "&nbsp;" * len(m.group(1)), formatted_line)

        html_content.append(formatted_line)

    # Close HTML tags
    html_content.extend(["</pre></div>", "</body>", "</html>"])

    # Write the HTML content to the output file
    with open(html_path, 'w', encoding='utf-8') as html_file:
        html_file.write("\n".join(html_content))

def printTarget():
    f = open("zap/target.txt","r")
    ans = ""
    for i in f:
        ans += i
    ans = ans.split()
    print(str(ans[0]+"://"+ans[1].strip()))

def ZapAspider(a):
    zap = ZAPv2(apikey=ZapApiKey)
    # Use the line below if ZAP is not listening on port 8080, for example, if listening on port 8090
    # zap = ZAPv2(apikey=apiKey, proxies={'http': 'http://127.0.0.1:8090', 'https': 'http://127.0.0.1:8090'})

    print('Ajax Spider target {}'.format(a))
    scanID = zap.ajaxSpider.scan(a)

    timeout = time.time() + 60 * 2  # 2 minutes from now
    # Loop until the ajax spider has finished or the timeout has exceeded
    while zap.ajaxSpider.status == 'running':
        if time.time() > timeout:
            break
        print('Ajax Spider status ' + zap.ajaxSpider.status)
        time.sleep(2)

    print('Ajax Spider completed')
    ajaxResults = zap.ajaxSpider.results(start=0, count=10)

def ZapActive(a):
    zap = ZAPv2(apikey=ZapApiKey, proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'})

    # TODO : explore the app (Spider, etc) before using the Active Scan API, Refer the explore section
    print('Active Scanning target {}'.format(a))
    scanID = zap.ascan.scan(a)
    while int(zap.ascan.status(scanID)) < 100:
        # Loop until the scanner has finished
        print('Scan progress %: {}'.format(zap.ascan.status(scanID)))
        time.sleep(5)

    print('Active Scan completed')
    # Print vulnerabilities found by the scanning

def printMetasploit():
    f = open("ApacheWebDocker/website/searchsploitNmap.txt","r")
    for i in f:
        if i.__contains__("Metasploit"):
            print(i,end="")

def main():
    parser = argparse.ArgumentParser(description="Modular Python CLI Tool")

    # Add flags/arguments
    parser.add_argument("--nmapFull", type=str, help=" --nmapFUll [IP]")
    parser.add_argument("--nmapQuick", type=str, help="--nmapQuick [IP]")
    parser.add_argument("--readNmap", action="store_true", help="Return Nmap result of closest scan")
    parser.add_argument("--readValidatedNmap", action="store_true", help="Return Shortened Nmap result")
    parser.add_argument("--readValidatedNmapServices", action="store_true", help="Return Shortened Nmap result")
    parser.add_argument("--metasploitSort", action="store_true", help="Return Shortened Nmap result")
    parser.add_argument("--searchSploit", type=str, help="searchsploit")
    parser.add_argument("--addDomain", type=str, help="Automate add domain")
    parser.add_argument("--webanalyzer", type=str, help="Analyze Webtechnology")
    parser.add_argument("--ZapFullScan", type=str, help="Scan web [URL]")
    parser.add_argument("--buildZapSpiderTree", action="store_true", help="Print out directory tree")
    parser.add_argument("--printTarget", action="store_true", help="Print out Target string")
    parser.add_argument("--printMetasploit", action="store_true", help="Print out metasploit Result")


    args = parser.parse_args()

    if args.nmapFull:
        nmapFullScan(args.nmapFull)

    if args.nmapQuick:
        nmapQuickScan(args.nmapQuick)

    if args.readNmap:
        print(readNmap())

    if args.readValidatedNmapServices:
        print(validateNmapService())

    if args.metasploitSort:
        metasploitGenerate()

    if args.readValidatedNmap:
        print(validateNmap())

    if args.searchSploit:
        searchSploitEx(args.searchSploit)

    if args.addDomain:
        domainAdd(args.addDomain)

    if args.webanalyzer:
        webanalyzer(args.webanalyzer)

    if args.ZapFullScan:
        zapFullScan(args.ZapFullScan)

    if args.buildZapSpiderTree:
        buildSpiderTree()

    if args.printTarget:
        printTarget()

    if args.printMetasploit:
        printMetasploit()




if __name__ == "__main__":
    #zapScan()
    main()
    #searchSploitWebanalyzer()
    #zapFullScan("http 192.168.31.139:3000")
    #buildSpiderTree()
    #printMetasploit()
    #validateNmapService()
    #metasploitGenerate()
