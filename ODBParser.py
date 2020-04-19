import ODBlib.mongoscraper as mongoscraper
import ODBlib.EsScanAndDump as EsScanAndDump
from ODBlib.ODBhelperfuncs import *
from colorama import Style

"""
To do:
1. multithread (at least initial check for ping or if error in case of MDB)
2. add rsync
"""

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

if __name__ == '__main__':
    import ODBconfig
    import argparse
    import sys
    from pathlib import Path


    class BlankLinesHelpFormatter(argparse.HelpFormatter):
        def _split_lines(self, text, width):
            return super()._split_lines(text, width) + ['']

    parsed,totalrecs,donedbs = getstats()

    description = f"""{Fore.CYAN}
        
                      ____  ___  ___  ___                      
                     / __ \/ _ \/ _ )/ _ \___ ________ ___ ____
                    / /_/ / // / _  / ___/ _ `/ __(_-</ -_) __/
                    \____/____/____/_/   \_,_/_/ /___/\__/_/   
                           
                           {Fore.RESET}by:{Fore.CYAN} Matteo Tomasini (citcheese) {Fore.RESET}
                                    Version: {Fore.CYAN}0.85{Fore.RESET}                                      
    
            {color.BOLD}ODBParser - Query open databases and grab only the data you care about!{Style.RESET_ALL}

    {Fore.LIGHTRED_EX}Examples:{Fore.RESET} python ODBParser.py -cn US -p 8080 -t users --elastic --shodan --csv --limit 100
              python ODBParser.py -ip 192.168.2:8080 --mongo --ignorelogs --nosizelimits
    {Fore.LIGHTRED_EX}{color.BOLD}\n    Damage to-date: {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}{parsed:,d}{Fore.RESET} servers parsed {Fore.RED}|{Fore.RESET} {Fore.LIGHTBLUE_EX}{donedbs:,d}{Fore.RESET} databases dumped {Fore.RED}|{Fore.RESET} {Fore.LIGHTBLUE_EX}{totalrecs:,d}{Fore.RESET} records pulled
    {Fore.CYAN}_____________________________________________________________________________{Fore.RESET}
    """
    print(description+"\n")

    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)#formatter_class=BlankLinesHelpFormatter
    group3 = parser.add_argument_group(f'{Fore.CYAN}Query Options{Fore.RESET}')

    group3.add_argument("--shodan","-sh",action='store_true',help='Add this flag if using Shodan. Specify ES or MDB w/ flags.')
    group3.add_argument("--binary","-be",action='store_true',help='Add this flag if using BinaryEdge. Specify ES or MDB w/ flags.')

    group3.add_argument("--ip", '-ip', help=f"Query one server. Add port like so '192.165.2.1:8080' or will use default ports for each db type. Add ES or MDB flags to specify parser. ",metavar="")
    group3.add_argument("--file","-f",help=f"Load line-separated IPs from file. Add port or will assume default ports for each db type. Add ES or MDB flags to specify parser.",metavar="")
    group3.add_argument("--paste","-v",action='store_true',help=f"Query line-separated IPs from clipboard. Add port or will assume default ports for each db type, e.g. 9200 for ES. Add ES or MDB flags to specify parser.")

    group2 = parser.add_argument_group(f'{Fore.CYAN}Shodan/BinaryEdge Options{Fore.RESET}')

    group2.add_argument("--limit","-l",help=f"Max number of results per query. Default is {Fore.LIGHTBLUE_EX}500.{Fore.RESET}",metavar="")
    group2.add_argument("--port","-p",help=f"Filter by port.",metavar="")
    group2.add_argument("--country","-cn",help=f"Filter by country (two-letter country code).",metavar="")
    group2.add_argument("--terms","-t",help=f"Enter any additional query terms you want here, e.g. 'users'",metavar="")

    group1 = parser.add_argument_group(f'{Fore.CYAN}Dump Options{Fore.RESET}')

    group1.add_argument("--mongo", "-mdb", action='store_true',
                        help="Use for IP, Shodan, BinaryEdge & Paste methods to specify parser.")
    group1.add_argument("--elastic", "-es", action='store_true',
                        help=f"Use for IP, Shodan, BinaryEdge & Paste methods to specify parser.")

    group1.add_argument("--database","-db",help=f"Specify database you want to grab. For MDB must be in format format 'db:collection'. Use with IP arg & 'es' or 'mdb' flag",metavar="")
    group1.add_argument("--getall","-g",action='store_true',help=f"Get all indices regardless of fields and collection/index names (overrides selections in config file).")

    group1.add_argument("--ignorelogs", action='store_true', help=f"Connect to a server you've already checked out.")
    group1.add_argument("--nosizelimits","-n",action='store_false',help=f"Dump index no matter how big it is. Default max doc count is {Fore.LIGHTBLUE_EX}800,000.{Fore.RESET}")
    group1.add_argument("--csv",action='store_true',help=f"Convert JSON dumps into CSV format on the fly. (Puts JSON files in backup folder in case there is issue with coversion)")

    group = parser.add_argument_group(f'{Fore.CYAN}CSV/Post-processing Options{Fore.RESET}')
    group.add_argument("--convertToCSV","-c",help=f"Convert JSON file or folder of JSON dumps to CSVs after the fact. Enter full path or folder name in current working directory",metavar="")
    group.add_argument("--dontflatten",action='store_false',help="Use if run into memory issues converting JSON files to CSV during post-processing.")
    group.add_argument("--basic",action='store_true',help="Use with --convertToCSV flag if your JSON dumps are not true JSON files, but rather line separated JSON objects that you got from other sources.")
    group.add_argument("--dontclean","-dc",action='store_false',help="Choose if want to keep useless data when convert to CSV. See docs for more info.")


    args = parser.parse_args()

    if len(sys.argv[1:])==0:
        parser.print_help()
        sys.exit()

    items = ([args.shodan,args.paste, args.ip, args.file,args.binary])
    if len([x for x in items if x and x is not None]) > 1:
        print(f"{Fore.RED}Error: {Fore.RESET}Can't pick more than one method at once!")
        sys.exit()

    if not any([args.ip,args.shodan,args.paste,args.convertToCSV,args.file,args.binary]):
        print(f"{Fore.RED}Error:{Fore.RESET}You need to specify whether want to run Shodan query, a single IP, get IPS from file, or paste from clipbard.")
        sys.exit()
    careboutsize = args.nosizelimits
    ignorelogs = args.ignorelogs

    if args.convertToCSV:
        if ".json" in args.convertToCSV: #check if file or folder of json files
            filename = Path(args.convertToCSV).name
            #filename = args.convertToCSV.rsplit('\\',1)[1]

            print(F"Converting: {Fore.LIGHTRED_EX}{filename}{Fore.RESET}" )
            res = convertjsondumptocsv(args.convertToCSV,flattennestedjson=args.dontflatten,olddumps=args.basic,getridofuselessdata=args.dontclean)
            if res:
                print(
                    F"{Fore.GREEN}    Error{Fore.RESET} flattening JSON so converted it to 'simple' CSV.")
            else:
                print(f"Successfully converted file {Fore.LIGHTBLUE_EX}{filename}{Fore.RESET}")
        else:
            if "/" in args.convertToCSV: #check if you gave me full path to folder or just folder name in CWD
                folder = args.convertToCSV
            else:
                folder = os.path.join(os.getcwd(), args.convertToCSV)
            jsonfoldert0mergedcsv(folder,flattennestedjson=args.dontflatten,olddumps=args.basic,getridofuselessdata=args.dontclean)
    else:
        if args.getall:
            GETALL = True
            careboutsize = False
        else:
            GETALL = False
        if not args.elastic and not args.mongo:
            print(F"You need to specify {Fore.RED}--elastic (-es){Fore.RESET} or {Fore.RED}--mongo (-mdb){Fore.RESET} for IP, Shodan and Paste methods so I know what parser to use.")
            sys.exit()
        if args.ip:
            port=""
            ip = args.ip
            ip = ip.strip("/https//:")
            if valid_ip(ip):
                if ":" in ip:#check if specify port
                    ip,port = ip.split(":")
                    port = int(port)

                if args.elastic:
                    if args.database:
                        indexname = args.database
                        ignorelogs = True

                    else:
                        indexname = ""

                    if port:
                        donecount, recordcount = EsScanAndDump.main(ip, portnumber=port, Icareaboutsize=careboutsize,
                                                      ignorelogs=ignorelogs, csvconvert=args.csv, index=indexname,getall=GETALL,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)

                    else:
                        donecount, recordcount = EsScanAndDump.main(ip, Icareaboutsize=careboutsize,
                                                                    ignorelogs=ignorelogs, csvconvert=args.csv,
                                                                    index=indexname, getall=GETALL,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)

                elif args.mongo:
                    if args.database:
                        ignorelogs = True
                        collection = args.database
                        if len(collection.split(":")) != 2:
                            print(
                                f"{Fore.RED}Error:{Fore.RESET} Need to specify collection in {Fore.CYAN}'DBname:CollectionName'{Fore.RESET} format")
                            sys.exit()
                    else:
                        collection = ""

                    if port:
                        mongoscraper.mongodbscraper(ip,portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL,getcollection=collection,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)
                    else:
                        mongoscraper.mongodbscraper(ip,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL,getcollection=collection,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)
            else:
                print(f"{Fore.RED}Error:{Fore.RESET} {ip} does not appear to be a valid IP address")
                sys.exit()
        elif args.paste or args.file:
            donedbs = 0
            totalrecords = 0
            badips=[]
            ips =[]

            if args.elastic:
                PRODUCT = "elastic"
            elif args.mongo:
                PRODUCT = "mongodb"
            if args.paste:
                ips,badips = ipsfromclipboard()

            if args.file:
                ips,badips = ipsfromfile(args.file)
            if badips:
                print(f"{Fore.RED}Error:{Fore.RESET} Following items you supplied don't appear to be valid IP addresses, so I'm skipping them:")
                for x in badips:
                    print(f"        \u2022 {x}")
            if not ips:
                print(f"{Fore.RED}Error:{Fore.RESET} No valid IP addresses found. Try again when have valid IPs. Exiting...")
                sys.exit()

            if ignorelogs:
                alreadyparsedips = []
            else:
                ipstoparse = [x.split(":")[0] for x in ips]
                alreadyparsedips = checkifIPalreadyparsed(ipstoparse, dbtype=PRODUCT, multi=True)
                if alreadyparsedips:
                    print(f"{Fore.GREEN}Skipping{Fore.RESET} {Fore.LIGHTBLUE_EX}{len(alreadyparsedips)}{Fore.RESET} of the servers as you've already parsed them (set --ignorelogs flag if you want them)")
            countip=0
            for x in ips:
                countip+=1
                if ":" in x:
                    ip, port = x.split(":")
                else:
                    ip,port = x,""
                if ip not in alreadyparsedips:
                    print(f"[{color.BOLD}{Fore.LIGHTBLUE_EX}{countip}{Fore.RESET}/{len(ips) - len(alreadyparsedips)}{Style.RESET_ALL}]")

                    if args.elastic:
                        if not port:
                            port = 9200
                        donecount, recordcount = EsScanAndDump.main(ip,portnumber=port,ignorelogs=ignorelogs,csvconvert=args.csv,Icareaboutsize=careboutsize,getall=GETALL,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)
                        donedbs += donecount
                        totalrecords += recordcount
                    elif args.mongo:
                        if not port:
                            port = 27017
                        donecount, recordcount = mongoscraper.mongodbscraper(ip, portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)
                        donedbs += donecount
                        totalrecords += recordcount
            printsummary(donedbs,totalrecords)


        elif args.shodan or args.binary: #do both binaryedge and shodan here
            if args.shodan:
                if not ODBconfig.SHODAN_API_KEY:
                    print(f"{Fore.RED}Error!{Fore.RESET}You need to enter your Shodan API key in ODBconfig.py")
                    sys.exit()
            if args.binary:
                if not ODBconfig.BINARY_API_KEY:
                    print(f"{Fore.RED}Error!{Fore.RESET}You need to enter your BinaryEdge API key in ODBconfig.py. If need key, go here: https://app.binaryedge.io/sign-up")
                    sys.exit()

            if args.limit:
                limit = args.limit
            else:
                limit = 500
            other = ""

            if args.elastic:
                PRODUCT = "elastic"
                TYPE = "elasticsearch"

                #other = ' all:"elastic indices”'
            elif args.mongo:
                PRODUCT="mongodb"
                TYPE = "mongodb"
                other = " all:'mongodb server information' all:'metrics'" #make sure only getting open dbs that dont req auth
            addterms =""
            country=""
            shodanport=""
            if args.country:
                country = f' country:{args.country}'
            if args.port:
                shodanport = f' port:{args.port}'
            if args.terms:
                addterms = f" {args.terms}"

            if args.shodan:
                QUERY = f'product:{PRODUCT}{shodanport}{country}{other}{addterms}'
                service="Shodan"
            if args.binary:
                if TYPE =="mongodb":
                    QUERY = f'type:{TYPE}{shodanport}{country} mongodb.names:{addterms.replace(" ","")}'
                elif TYPE == "elasticsearch":
                    QUERY = f'type:{TYPE}{shodanport}{country}{addterms}'

                service = "BinaryEdge"

            print(f"Your {Fore.CYAN}{service} {Fore.RESET}Query: {Fore.CYAN}'{QUERY}'{Fore.RESET} with max results of {Fore.LIGHTBLUE_EX}{limit}{Fore.RESET}")
            if args.shodan:
                listres = shodan_query(query=QUERY,limit=limit)

            if args.binary:
                listres = binaryedgeQuery(query=QUERY,limit=limit)
            totalshodanres = len(listres)

            if len(listres) ==0:
                print(f"{Fore.RED}\nNO RESULTS!{Fore.RESET} (If Shodan search possible server overloaded and you should try again in minute).")
                sys.exit()
            else:
                print(f"    Found {Fore.CYAN}{str(totalshodanres)}{Fore.RESET} results!")
            donedbs = 0
            totalrecords = 0
            counts=0
            if ignorelogs:
                alreadyparsedips = []
            else:
                shodanips = [x[0] for x in listres]
                alreadyparsedips = checkifIPalreadyparsed(shodanips,dbtype=PRODUCT,multi=True)
                if alreadyparsedips:
                    print(f"{Fore.GREEN}Skipping{Fore.RESET} {Fore.LIGHTBLUE_EX}{len(alreadyparsedips)}{Fore.RESET} of the servers as you've already parsed them (set --ignorelogs flag if you want them)")
            for x in listres:
                ipaddress,product,port = x
                if ipaddress not in alreadyparsedips:
                    try:
                        counts+=1

                        print(f"[{Fore.LIGHTBLUE_EX}{counts}{Fore.RESET}/{totalshodanres-len(alreadyparsedips)}]")

                        if "elastic" in product.lower():
                            donecount, recordcount = EsScanAndDump.main(ipaddress,portnumber=port,csvconvert=args.csv,ignorelogs=ignorelogs,Icareaboutsize=careboutsize,getall=GETALL,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)
                            donedbs += donecount
                            totalrecords += recordcount

                        elif "mongodb" in product.lower():
                            donecount, recordcount = mongoscraper.mongodbscraper(ipaddress,portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL,flattennestedjson=args.dontflatten,getridofuselessdata=args.dontclean)
                            donedbs += donecount
                            totalrecords += recordcount
                    except KeyboardInterrupt:
                        print("\n    Ok, skipping server...")
                        print(f'{Fore.RED}{"-" * 45}\n{Fore.RESET}')

                        pass
            printsummary(donedbs, totalrecords)

