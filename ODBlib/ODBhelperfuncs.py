import os
import json
import pandas as pd
from tqdm import tqdm
from colorama import Fore

def jsonappendfile(filepath,items):
    prevExists = True
    if not os.path.exists(filepath):
        prevExists = False
        with open(filepath, "ab+") as f:
            f.write("[]".encode())
    with open(filepath, "ab+") as newZ:  # so dont have to store whole json in memory
        newZ.seek(-1, 2)
        newZ.truncate()
        if prevExists:
            newZ.write(",".encode())
        for y in items[:-1]:
            newZ.write(json.dumps(y).encode())
            newZ.write(",".encode())
        newZ.write(json.dumps(items[-1]).encode())
        newZ.write(']'.encode())

def convertjsondumptocsv(jsonfile,flattennestedjson=False,olddumps=False):
    import pathlib
    from pandas.io.json import json_normalize
    import numpy as np
    p = pathlib.Path(jsonfile)
    foldername = p.parent.name
    issuesflattening = False
    if not os.path.exists(os.path.join(p.parent,"JSON_backups")):
        os.makedirs(os.path.join(p.parent,"JSON_backups"))
    try:
        if olddumps:#use this to convert generic ES dumps where entire record is on each line
            with open(jsonfile) as f:
                content = f.readlines()
            con2 = [json.loads(x) for x in content]

            con2 =[x["_source"] for x in con2 if x['_source']] #get rid of empty values
            outfile = os.path.join(p.parent,f"{foldername}_{p.parts[-1].replace('.json','.csv')}")
        else:
            with open(jsonfile) as f:
                con2 = json.load(f)
            outfile = jsonfile.replace('.json','.csv')
        if flattennestedjson:
            try:
                df = json_normalize(con2,errors="ignore")
            except Exception as e:
                #print("    Error flattening JSON. It's an issue with Pandas. Not going to flatten, but I'm sure will be ok")
                df = pd.DataFrame(con2)
                issuesflattening = True
        else:
            df = pd.DataFrame(con2)
        df.dropna(axis=1, how='all',inplace=True)
        df.replace(np.nan, '', regex=True,inplace=True)
        cols = df.columns
        dropcols = ["_id", '__v']  # id columns I don't want
        cols1 = [x for x in cols if x in dropcols]  # check to see if column is in my df
        df.drop(cols1, axis=1, inplace=True)  #
        df = df.applymap(str)
        df.drop_duplicates(keep=False, inplace=True)
        df = df.replace({'\n': '<br>',"\r":"<br>"}, regex=True)
        df.to_csv(outfile,index=False,escapechar='\n') #ignore newline character inside strings
        os.rename(jsonfile,os.path.join(p.parent,"JSON_backups",p.name)) #move json file to jsonbackups folder to keep things tidy
        try:
            os.rename(jsonfile.replace(".json","_mapping.json"), os.path.join(p.parent, "JSON_backups",
                                             p.name.replace(".json","_mapping.json")))  # move json file to jsonbackups folder to keep things tidy
        except:
            pass
    except Exception as e:
        print(f"{jsonfile}: {str(e)}")
    return issuesflattening

def jsonfoldert0mergedcsv(folder,flattennestedjson=False,olddumps=False):
    files = [x for x in os.listdir(folder) if x.endswith(".json") and "_mapping.json" not in x]
    t = tqdm(files,desc="Now Converting",leave=True)
    issues = []
    for x in t:
        t.set_description(F"Converting: {Fore.LIGHTRED_EX}{x}{Fore.RESET}")
        t.refresh()
        res = convertjsondumptocsv(os.path.join(folder,x),flattennestedjson=flattennestedjson,olddumps=olddumps)
        if res:
            issues.append(x)
    if issues:
        print(F"    {Fore.LIGHTGREEN_EX}Error{Fore.RESET} flattening JSON for following files so converted 'em to 'simple' CSV:")
        for y in issues:
            print(f"        {y}")

def megajsonconvert(directory,flattennestedjson=False,olddumps=False):
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory,folder)):
            jsonfoldert0mergedcsv(os.path.join(directory,folder),flattennestedjson=flattennestedjson,olddumps=olddumps)

def convert_timestamp(item_date_object):
    import datetime
    if isinstance(item_date_object, (datetime.date, datetime.datetime)):
        return item_date_object.timestamp()

def iterate_all(iterable, returned="key"):
    """Returns an iterator that returns all keys or values
       of a (nested) iterable.

       Arguments:
           - iterable: <list> or <dictionary>
           - returned: <string> "key" or "value"

       Returns:
           - <iterator>
    """

    if isinstance(iterable, dict):
        for key, value in iterable.items():
            if returned == "key":
                yield key
            elif returned == "value":
                if not (isinstance(value, dict) or isinstance(value, list)):
                    yield value
            else:
                raise ValueError("'returned' keyword only accepts 'key' or 'value'.")
            for ret in iterate_all(value, returned=returned):
                yield ret
    elif isinstance(iterable, list):
        for el in iterable:
            for ret in iterate_all(el, returned=returned):
                yield ret


def shodan_query(query,limit=1000):
    import ODBconfig
    import shodan
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

def valid_ip(address):
    if ":" in address:
        address = address.split(":",1)[0]

    try:
        host_bytes = address.split('.')
        valid = [int(b) for b in host_bytes]
        valid = [b for b in valid if b >= 0 and b<=255]
        return len(host_bytes) == 4 and len(valid) == 4
    except:
        return False

def ipsfromfile(filepath):
    with open(filepath,encoding="utf8",errors="ignore") as f:
        ips = f.readlines()
    ips = [x.replace("\n", "").strip("/https//:") if not x[0].isdigit() else x.replace("\n", "") for x in ips]
    ips = list(set((filter(None,ips))))
    goodips = [x for x in ips if valid_ip(x)]
    badips = (set(ips).difference(goodips))
    return goodips,badips

def ipsfromclipboard():
    import pyperclip
    ips = pyperclip.paste().splitlines()
    ips = list(set((filter(None, ips))))
    ips = [x.strip("/https//:") if not x[0].isdigit() else x for x in ips]
    goodips = [x for x in ips if valid_ip(x)]
    badips = (set(ips).difference(goodips))
    return goodips,badips

def printsummary(donedbs,totalrecords):
    from colorama import Fore
    summ = [f"{Fore.RED}RUN SUMMARY{Fore.CYAN}", F"{Fore.RESET}Dumped {Fore.LIGHTBLUE_EX}{str(donedbs)}{Fore.RESET} databases with a total of {Fore.LIGHTBLUE_EX}{totalrecords:,d}{Fore.RESET} records.{Fore.CYAN}", f"{Fore.RESET}{Fore.RED}Have a nice day!{Fore.CYAN}"]

    maxlen = max(len(s) for s in summ)
    colwidth = maxlen - 12
    border = colwidth + 2
    print(f"{Fore.CYAN}{'#' * border}")
    print(f'#{summ[0]:^{colwidth + 10}}#')
    print(f'#{summ[1]:^{colwidth + 30}}#')
    print(f'#{summ[2]:^{colwidth + 15}}#')
    print('#' * border)

def updatestatsfile(donedbs=0,totalrecords=0,parsedservers=0,type="ElasticSearch"):
    fpath = os.path.join(os.getcwd(),"ODBlib","ODBstats.json")
    if not os.path.exists(fpath):
        prevExists = False
        item = {}
        elastic ={}
        mongo={}
        elastic["databases dumped"]=0
        elastic["total records dumped"] =0
        elastic["parsed servers"] = 0
        mongo["databases dumped"]=0
        mongo["total records dumped"] =0
        mongo["parsed servers"] = 0
        item["ElasticSearch"] = elastic
        item["MongoDB"] = mongo


        with open(fpath, "w") as f:
            json.dump(item,f)
    with open(fpath) as f:
        con = json.load(f)
    con[type]["total records dumped"]=con[type]["total records dumped"]+totalrecords
    con[type]["databases dumped"]=con[type]["databases dumped"]+donedbs
    con[type]["parsed servers"]=con[type]["parsed servers"]+parsedservers
    with open(fpath, "w") as f:
        json.dump(con, f)

def getstats():
    #import pandas as pd
    fpath = os.path.join(os.getcwd(),"ODBlib","ODBstats.json")
    with open(fpath) as f:
        con = json.load(f)
    donedbs = 0
    parsed =0
    totalrecs = 0
    for x in con.keys():
        parsed += con[x]["parsed servers"]
        totalrecs += con[x]["total records dumped"]
        donedbs += con[x]["databases dumped"]
    return parsed,totalrecs,donedbs

    #print(f"{Fore.CYAN}ODB Stats{Fore.RESET}")
    #for x in con:
     #   print(f"{Fore.LIGHTRED_EX}{x}| \n{Fore.RESET}    " + '\n    '.join(
      #      [f"{y}: {Fore.LIGHTBLUE_EX}{con[x][y]:,d}{Fore.RESET}" for y in con[x]]))
    #df = pd.DataFrame(con)
    #df = df.T
    #for x in con:
     #   print(f"\n{Fore.LIGHTRED_EX}{x}{Fore.RESET}")
      #  for y in con[x]:
       #     print(f"\t{y}: {Fore.LIGHTBLUE_EX}{con[x][y]:,d}{Fore.RESET}")
    #print(df)