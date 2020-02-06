import mongoscraper
import EsScanAndDump
import shodan
from colorama import Fore
import os


"""
To do:
1. multithread
2. single collection dump for MongoDB
"""
def ipsfromclipboard():
    import pyperclip
    ips = pyperclip.paste().splitlines()
    ips = list(filter(None,ips))
    ips = [x.strip("/https//:") for x in ips if x[0].isdigit()]
    return ips

def shodan_query(query,limit=1000):
    import ODBconfig
    counter =0
    limit = int(limit) #convert to int as passed as string from cli.
    try:
        api = shodan.Shodan(ODBconfig.SHODAN_API_KEY)
        result = api.search_cursor(query)
        #result = api.search(query, page=page)
        shodanres = []
        for x in result:
            shodanres.append((x["ip_str"],x["product"],x["port"])) #lets only grab these fields to lower memory overhead
            counter+=1
            if counter>=limit: #so we don't go over limit you set. Helps to avoid runnign through all your credits
                break
        return shodanres

    except shodan.APIError as e:
        print(Fore.RED + e.value + Fore.RESET)
        return False

if __name__ == '__main__':
    import ODBconfig
    import argparse
    import warnings
    import sys


    class BlankLinesHelpFormatter(argparse.HelpFormatter):
        def _split_lines(self, text, width):
            return super()._split_lines(text, width) + ['']


    description = f"""{Fore.CYAN}
         _____ ______ ______  _____               _      _                 
        |  _  ||  _  \| ___ \|  __ \             | |    | |                
        | | | || | | || |_/ /| |  \/ _ __   __ _ | |__  | |__    ___  _ __ 
        | | | || | | || ___ \| | __ | '__| / _` || '_ \ | '_ \  / _ \| '__|
        \ \_/ /| |/ / | |_/ /| |_\ \| |   | (_| || |_) || |_) ||  __/| |   
         \___/ |___/  \____/  \____/|_|    \__,_||_.__/ |_.__/  \___||_|   
                           
                           by: Matteo Tomasini                                        
    {Fore.RESET}
    ODBgrabber - Query open databases and grab only the data you care about!
    
    {Fore.RED}Examples:{Fore.RESET} python ODBgrabber.py -cn US -p 8080 -t users --elastic --shodanquery --csv --limit 100
              python ODBgrabber.py -ip 192.168.2:8080 --mongo --ignorelogs --nosizelimits
    {Fore.CYAN}_____________________________________________________________________________{Fore.RESET}
    """

    print(description+"\n")

    parser = argparse.ArgumentParser()#formatter_class=BlankLinesHelpFormatter
    parser.add_argument("--ip", '-ip', help=f"{Fore.LIGHTRED_EX}Query one server. Add port, e.g. {Fore.LIGHTBLUE_EX}'192.165.2.1:8080'{Fore.LIGHTRED_EX}, or will assume default ports for each db type, e.g. 9200 for ES. Add ES or MDB flags to specify parser. {Fore.RESET}",metavar="")
    parser.add_argument("--index","-i",help=f"You know exactly what ES index you want? Go for it. Use this with IP arg and don't forget to add '--elastic' flag",metavar="")

    parser.add_argument("--shodanquery",action='store_true',help='Add this flag if using Shodan and also specify whether want ES or MDB w/ flags.')
    parser.add_argument("--limit","-l",help=f"{Fore.LIGHTRED_EX}Specify max number of Shodan results per query. Default is {Fore.LIGHTBLUE_EX}1000.{Fore.RESET}",metavar="")
    parser.add_argument("--port","-p",help=f"Specify if want to filter by port in Shodan query.",metavar="")
    parser.add_argument("--country","-cn",help=f"{Fore.LIGHTRED_EX}Specify country filter in Shodan query with two-letter country code.{Fore.RESET}",metavar="")
    parser.add_argument("--terms","-t",help=f"Enter any additional Shodan query terms you want here, e.g. users or maybe add additional filters?",metavar="")
    parser.add_argument("--paste",action='store_true',help=f"{Fore.LIGHTRED_EX}Query DBs hosted on line-separated IPs from clipboard. Add port otherwise will assume default ports for each db type, e.g. 9200 for ES. Add ES or MDB flags to specify parser.{Fore.RESET}")
    parser.add_argument("--mongo",action='store_true',help="Use for IP, Shodan and Paste methods to specify parser.")
    parser.add_argument("--elastic",action='store_true',help=f"{Fore.LIGHTRED_EX}Use for IP, Shodan and Paste methods to specify parser.{Fore.RESET}")
    parser.add_argument("--ignorelogs", action='store_true', help=f"add this flag to connect to a server you've already checked out.{Fore.RESET}")
    parser.add_argument("--nosizelimits",action='store_false',help=f"{Fore.LIGHTRED_EX}Add if you want to dump index no matter how big it is. {Fore.LIGHTGREEN_EX}Careful!{Fore.RESET} Current max doc count is set to {Fore.LIGHTBLUE_EX}800,000.{Fore.RESET}")
    parser.add_argument("--csv",action='store_true',help=f"Add this flag if want to convert JSON dumps from ES into CSV format on the fly. Would{Fore.LIGHTRED_EX} NOT {Fore.RESET}use in conjunction with nosizelimit flag as may kill your memory")
    parser.add_argument("--convertES","-c",help=f"{Fore.LIGHTRED_EX}Convert JSON file or folder of JSON dumps to CSVs after the fact. Enter full path or folder name in current working directory{Fore.RESET}",metavar="")
    parser.add_argument("--dontflatten",action='store_false',help="Add this flag if run into memory issues converting JSON files to CSV during post-processing.")
    parser.add_argument("--basic",action='store_true',help="Add this flag with CSV flag if your JSON dumps are just line separated full records that you got from other sources.")


    args = parser.parse_args()
    if len(sys.argv[1:])==0:
        parser.print_help()
        sys.exit()
    if not any([args.ip,args.shodanquery,args.paste,args.convertES]):
        print(f"{Fore.RED}Error:{Fore.RESET}You need to specify whether want to run Shodan query, a single IP, or paste from clipbard.")
        sys.exit()
    careboutsize = args.nosizelimits
    ignorelogs = args.ignorelogs

    #print(careboutsize)


    if args.convertES:
        if ".json" in args.convertES: #check if file or folder of json files
            #print (args.convertES)
            EsScanAndDump.convertjsondumptocsv(args.convertES,flattennestedjson=args.dontflatten,olddumps=args.basic)
            filename = args.convertES.rsplit('\\',1)[1]
            print(f"Successfully converted file {Fore.LIGHTBLUE_EX}{filename}{Fore.RESET}")
        else:
            if "/" in args.convertES: #check if you gave me full path to folder or just folder name in CWD
                folder = args.convertES
            else:
                folder = os.path.join(os.getcwd(), args.convertES)
            EsScanAndDump.jsonfoldert0mergedcsv(folder,flattennestedjson=args.dontflatten,olddumps=args.basic)
    else:
        if not args.elastic and not args.mongo:
            print(F"You need to specify {Fore.RED}--elastic or --mongo {Fore.RESET} for IP, Shodan and Paste methods so I know what parser to use.")
            sys.exit()
        if args.ip:
            port=""
            ip = args.ip
            ip = ip.strip("/https//:")
            if ":" in ip:#check if specify port
                ip,port = ip.split(":")
                port = int(port)
            if args.index:
                indexname=args.index
            else:
                indexname=""
            if args.elastic:
                if port:
                    EsScanAndDump.singleclustergrab(ip,portnumber=port,careaboutsize=careboutsize,ignorelogs=ignorelogs,convertTOcsv=args.csv,index=indexname)
                else:
                    EsScanAndDump.singleclustergrab(ip,careaboutsize=careboutsize,ignorelogs=ignorelogs,convertTOcsv=args.csv,index=indexname)
                #print("es")
            elif args.mongo:
                if port:
                    mongoscraper.mongodbscraper(ip,portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize)
                else:
                    mongoscraper.mongodbscraper(ip,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize)
        else:
            if args.paste:
                ips = ipsfromclipboard()
                donedbs = 0
                totalrecords = 0
                for x in ips:

                    if ":" in x:
                        ip, port = x.split(":")
                    else:
                        ip,port = x,""
                    if args.elastic:
                        if not port:
                            port = 9200
                        #print(port)
                        donecount, recordcount = EsScanAndDump.main(ip,portnumber=port,ignorelogs=ignorelogs,csvconvert=args.csv,Icareaboutsize=careboutsize)
                        donedbs += donecount
                        totalrecords += recordcount

                    elif args.mongo:
                        if not port:
                            port = 27017
                        donecount, recordcount = mongoscraper.mongodbscraper(ip, portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize)
                        donedbs += donecount
                        totalrecords += recordcount
                print('###########-----\033[91mFull Run Summary\x1b[0m-----################\n')
                print(F"      Succesfully dumped \033[94m{str(donedbs)}\x1b[0m databases with a total of \033[94m{totalrecords:,d}\x1b[0m records. \n        YOU ARE WELCOME.")

            elif args.shodanquery:
                if not ODBconfig.SHODAN_API_KEY:
                    print(Fore.RED + "You need to enter your Shodan API key in ODBconfig.py" + Fore.RESET)
                else:
                    if args.limit:
                        limit = args.limit
                    else:
                        limit = 100000

                    if args.elastic:
                        PRODUCT = "elastic"
                    elif args.mongo:
                        PRODUCT="mongodb"
                    addterms =""
                    country=""
                    shodanport=""
                    if args.country:
                        country = f' country:{args.country}'
                    if args.port:
                        shodanport = f' port:{args.port}'
                    if args.terms:
                        addterms = f" {args.terms}"
                    QUERY = f'product:{PRODUCT}{shodanport}{country}{addterms}'
                    print(f"Your Shodan Query: {Fore.CYAN}'{QUERY}'{Fore.RESET}")
                    #sys.exit()
                    listres = shodan_query(query=QUERY,limit=limit)
                    totalshodanres = str(len(listres))
                    if len(listres) ==0:
                        print(f"{Fore.RED} No results{Fore.RESET}. Shodan server overloaded or actually no results.")
                    else:
                        print(f"Found {Fore.CYAN}{str(totalshodanres)}{Fore.RESET} results!")
                    donedbs = 0
                    totalrecords = 0
                    counts=0
                    for x in listres:
                        counts+=1
                        print(f"{Fore.LIGHTBLUE_EX}{counts}{Fore.RESET}/{totalshodanres}")
                        ipaddress,product,port = x
                        if product.lower() =="elastic":
                            donecount, recordcount = EsScanAndDump.main(ipaddress,portnumber=port,csvconvert=args.csv,ignorelogs=ignorelogs,Icareaboutsize=careboutsize)
                            donedbs += donecount
                            totalrecords += recordcount

                        elif product.lower() =="mongodb":
                            donecount, recordcount = mongoscraper.mongodbscraper(ipaddress,portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize)
                            donedbs += donecount
                            totalrecords += recordcount
                    print(F'\n{Fore.CYAN}################{Fore.RESET}-----{Fore.CYAN}RUN SUMMARY{Fore.RESET}----{Fore.CYAN}################{Fore.RESET}\n')
                    print(F"Succesfully dumped {Fore.LIGHTRED_EX}{str(donedbs)}{Fore.RESET} databases with a total of \033[94m{totalrecords:,d}\x1b[0m records. \n        {Fore.LIGHTGREEN_EX}YOU ARE WELCOME!!!{Fore.RESET}")

