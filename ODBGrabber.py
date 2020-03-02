import ODBlib.mongoscraper as mongoscraper
import ODBlib.EsScanAndDump as EsScanAndDump
from colorama import Fore
import os
from ODBlib.ODBhelperfuncs import shodan_query,ipsfromclipboard,jsonfoldert0mergedcsv,valid_ip,ipsfromfile,printsummary,getstats,checkifIPalreadyparsed


"""
To do:
1. multithread
2. alt method for ES instances that don't allow scrolling or fix issue
3. 
4.check for done ips on frontend and skip w/o writing individua messages

"""

if __name__ == '__main__':
    import ODBconfig
    import argparse
    import sys


    class BlankLinesHelpFormatter(argparse.HelpFormatter):
        def _split_lines(self, text, width):
            return super()._split_lines(text, width) + ['']

    parsed,totalrecs,donedbs = getstats()

    description = f"""{Fore.CYAN}
         _____ ______ ______  _____               _      _                 
        |  _  ||  _  \| ___ \|  __ \             | |    | |                
        | | | || | | || |_/ /| |  \/ _ __   __ _ | |__  | |__    ___  _ __ 
        | | | || | | || ___ \| | __ | '__| / _` || '_ \ | '_ \  / _ \| '__|
        \ \_/ /| |/ / | |_/ /| |_\ \| |   | (_| || |_) || |_) ||  __/| |   
         \___/ |___/  \____/  \____/|_|    \__,_||_.__/ |_.__/  \___||_|   
                           
                           {Fore.RESET}by:{Fore.CYAN} Matteo Tomasini (citcheese) {Fore.RESET}
                                    Version: {Fore.CYAN}0.6{Fore.RESET}                                      
    
    ODBgrabber - Query open databases and grab only the data you care about!
    {Fore.RED}Examples:{Fore.RESET} python ODBgrabber.py -cn US -p 8080 -t users --elastic --shodan --csv --limit 100
              python ODBgrabber.py -ip 192.168.2:8080 --mongo --ignorelogs --nosizelimits
    {Fore.RED}\n    Damage to-date: {Fore.LIGHTBLUE_EX}{parsed:,d}{Fore.RESET} servers parsed {Fore.RED}|{Fore.RESET} {Fore.LIGHTBLUE_EX}{donedbs:,d}{Fore.RESET} databases dumped {Fore.RED}|{Fore.RESET} {Fore.LIGHTBLUE_EX}{totalrecs:,d}{Fore.RESET} records pulled
    {Fore.CYAN}_____________________________________________________________________________{Fore.RESET}
    """
    print(description+"\n")

    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)#formatter_class=BlankLinesHelpFormatter
    group3 = parser.add_argument_group(f'{Fore.CYAN}Query Options{Fore.RESET}')

    group3.add_argument("--shodan","-s",action='store_true',help='Add this flag if using Shodan. Specify ES or MDB w/ flags.')
    group3.add_argument("--ip", '-ip', help=f"Query one server. Add port like so '192.165.2.1:8080' or will use default ports for each db type. Add ES or MDB flags to specify parser. ",metavar="")
    group3.add_argument("--file","-f",help=f"Load line-separated IPs from file. Add port or will assume default ports for each db type. Add ES or MDB flags to specify parser.",metavar="")
    group3.add_argument("--paste","-v",action='store_true',help=f"Query line-separated IPs from clipboard. Add port or will assume default ports for each db type, e.g. 9200 for ES. Add ES or MDB flags to specify parser.")

    group2 = parser.add_argument_group(f'{Fore.CYAN}Shodan Options{Fore.RESET}')

    group2.add_argument("--limit","-l",help=f"Max number of results per query. Default is {Fore.LIGHTBLUE_EX}1000.{Fore.RESET}",metavar="")
    group2.add_argument("--port","-p",help=f"Filter by port.",metavar="")
    group2.add_argument("--country","-cn",help=f"Filter by country with two-letter country code.",metavar="")
    group2.add_argument("--terms","-t",help=f"Enter any additional query terms you want here, e.g. 'users' or maybe add additional filters?",metavar="")

    group1 = parser.add_argument_group(f'{Fore.CYAN}Dump Options{Fore.RESET}')

    group1.add_argument("--index","-i",help=f"Specify index (ES ONLY). Use with IP arg & 'elastic' flag",metavar="")
    group1.add_argument("--collection","-co",help=f"Specify collection (MDB ONLY). In format 'db:collection'. Use with IP arg & 'mongo' flag",metavar="")

    group1.add_argument("--getall","-g",action='store_true',help=f"Get all indices regardless of fields and collection/index names (overrides selections in config file).")

    group1.add_argument("--mongo","-mdb",action='store_true',help="Use for IP, Shodan & Paste methods to specify parser.")
    group1.add_argument("--elastic","-es",action='store_true',help=f"Use for IP, Shodan & Paste methods to specify parser.")
    group1.add_argument("--ignorelogs", action='store_true', help=f"Connect to a server you've already checked out.")
    group1.add_argument("--nosizelimits","-n",action='store_false',help=f"Dump index no matter how big it is. Default max doc count is {Fore.LIGHTBLUE_EX}800,000.{Fore.RESET}")
    group1.add_argument("--csv",action='store_true',help=f"Convert JSON dumps into CSV format on the fly. (Puts JSON files in backup folder in case there is issue with coversion)")

    group = parser.add_argument_group(f'{Fore.CYAN}Post-processing{Fore.RESET}')
    group.add_argument("--convertToCSV","-c",help=f"Convert JSON file or folder of JSON dumps to CSVs after the fact. Enter full path or folder name in current working directory",metavar="")
    group.add_argument("--dontflatten",action='store_false',help="Use if run into memory issues converting JSON files to CSV during post-processing.")
    group.add_argument("--basic",action='store_true',help="Use with CSV flag if your JSON dumps are just line separated full records that you got from other sources.")

    args = parser.parse_args()

    if len(sys.argv[1:])==0:
        parser.print_help()
        sys.exit()

    items = ([args.shodan,args.paste, args.ip, args.file])
    if len([x for x in items if x and x is not None]) > 1:
        print(f"{Fore.RED}Error: {Fore.RESET}Can't pick more than one method at once!")
        sys.exit()

    if not any([args.ip,args.shodan,args.paste,args.convertToCSV,args.file]):
        print(f"{Fore.RED}Error:{Fore.RESET}You need to specify whether want to run Shodan query, a single IP, get IPS from file, or paste from clipbard.")
        sys.exit()
    careboutsize = args.nosizelimits
    ignorelogs = args.ignorelogs


    if args.convertToCSV:
        if ".json" in args.convertToCSV: #check if file or folder of json files
            filename = args.convertToCSV.rsplit('\\',1)[1]

            print(F"Converting: {Fore.LIGHTRED_EX}{filename}{Fore.RESET}" )
            res = EsScanAndDump.convertjsondumptocsv(args.convertToCSV,flattennestedjson=args.dontflatten,olddumps=args.basic)
            if res:
                print(
                    F"{Fore.LIGHTGREEN_EX}    Error{Fore.RESET} flattening JSON so converted it to 'simple' CSV.")
            else:
                print(f"Successfully converted file {Fore.LIGHTBLUE_EX}{filename}{Fore.RESET}")
        else:
            if "/" in args.convertToCSV: #check if you gave me full path to folder or just folder name in CWD
                folder = args.convertToCSV
            else:
                folder = os.path.join(os.getcwd(), args.convertToCSV)
            jsonfoldert0mergedcsv(folder,flattennestedjson=args.dontflatten,olddumps=args.basic)
    else:
        if args.getall:
            GETALL = True
            careboutsize = False
        else:
            GETALL = False
        if not args.elastic and not args.mongo:
            print(F"You need to specify {Fore.RED}--elastic{Fore.RESET} or {Fore.RED}--mongo {Fore.RESET} for IP, Shodan and Paste methods so I know what parser to use.")
            sys.exit()
        if args.ip:
            port=""
            ip = args.ip
            ip = ip.strip("/https//:")


            if valid_ip(ip):
                if ":" in ip:#check if specify port
                    ip,port = ip.split(":")
                    port = int(port)
                if args.index:
                    indexname=args.index
                else:
                    indexname=""
                if args.collection:
                    collection = args.collection
                    if len(collection.split(":")) !=2:
                        print(f"{Fore.RED}Error:{Fore.RESET} Need to specify collection in 'DBname:CollectionName' format")
                        sys.exit()
                else:
                    collection = ""
                if args.elastic:
                    if port:
                        donecount, recordcount = EsScanAndDump.main(ip, portnumber=port, Icareaboutsize=careboutsize,
                                                      ignorelogs=ignorelogs, csvconvert=args.csv, index=indexname,getall=GETALL)

                    else:
                        donecount, recordcount = EsScanAndDump.main(ip, Icareaboutsize=careboutsize,
                                                                    ignorelogs=ignorelogs, csvconvert=args.csv,
                                                                    index=indexname, getall=GETALL)

                elif args.mongo:
                    if port:
                        mongoscraper.mongodbscraper(ip,portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL,getcollection=collection)
                    else:
                        mongoscraper.mongodbscraper(ip,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL,getcollection=collection)
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

                # other = ' all:"elastic indices”'
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
                    print(f"{Fore.LIGHTGREEN_EX}Skipping{Fore.RESET} {Fore.LIGHTBLUE_EX}{len(alreadyparsedips)}{Fore.RESET} of the servers as you've already parsed them (set --ignorelogs flag if you want them)")
            countip=0
            for x in ips:
                countip+=1
                if ":" in x:
                    ip, port = x.split(":")
                else:
                    ip,port = x,""
                if ip not in alreadyparsedips:
                    print(f"{Fore.LIGHTBLUE_EX}{countip}{Fore.RESET}/{len(ips) - len(alreadyparsedips)}")

                    if args.elastic:
                        if not port:
                            port = 9200
                        donecount, recordcount = EsScanAndDump.main(ip,portnumber=port,ignorelogs=ignorelogs,csvconvert=args.csv,Icareaboutsize=careboutsize,getall=GETALL)
                        donedbs += donecount
                        totalrecords += recordcount
                    elif args.mongo:
                        if not port:
                            port = 27017
                        donecount, recordcount = mongoscraper.mongodbscraper(ip, portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL)
                        donedbs += donecount
                        totalrecords += recordcount
            printsummary(donedbs,totalrecords)


        elif args.shodan:
            if not ODBconfig.SHODAN_API_KEY:
                print(Fore.RED + "You need to enter your Shodan API key in ODBconfig.py" + Fore.RESET)
            else:
                if args.limit:
                    limit = args.limit
                else:
                    limit = 100
                other = ""

                if args.elastic:
                    PRODUCT = "elastic"

                    #other = ' all:"elastic indices”'
                elif args.mongo:
                    PRODUCT="mongodb"
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
                QUERY = f'product:{PRODUCT}{shodanport}{country}{other}{addterms}'
                print(f"Your Shodan Query: {Fore.CYAN}'{QUERY}'{Fore.RESET} with max results of {Fore.LIGHTBLUE_EX}{limit}{Fore.RESET}")
                listres = shodan_query(query=QUERY,limit=limit)
                totalshodanres = len(listres)
                if len(listres) ==0:
                    print(f"{Fore.RED}\nNo results{Fore.RESET}. Shodan server either overloaded or actually no results (server doesn't specify, which is annoying).")
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
                        print(f"{Fore.LIGHTGREEN_EX}Skipping{Fore.RESET} {Fore.LIGHTBLUE_EX}{len(alreadyparsedips)}{Fore.RESET} of the servers as you've already parsed them (set --ignorelogs flag if you want them)")
                for x in listres:
                    ipaddress,product,port = x
                    if ipaddress not in alreadyparsedips:
                        counts+=1

                        print(f"{Fore.LIGHTBLUE_EX}{counts}{Fore.RESET}/{totalshodanres-len(alreadyparsedips)}")

                        if product.lower() =="elastic":
                            donecount, recordcount = EsScanAndDump.main(ipaddress,portnumber=port,csvconvert=args.csv,ignorelogs=ignorelogs,Icareaboutsize=careboutsize,getall=GETALL)
                            donedbs += donecount
                            totalrecords += recordcount

                        elif product.lower() =="mongodb":
                            donecount, recordcount = mongoscraper.mongodbscraper(ipaddress,portnumber=port,ignorelogfile=ignorelogs,Icareaboutsize=careboutsize,convertTOcsv=args.csv,getall=GETALL)
                            donedbs += donecount
                            totalrecords += recordcount
                printsummary(donedbs, totalrecords)

