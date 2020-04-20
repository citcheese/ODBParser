<table border =0 color=white>
    <tr>
        <td valign="top"><img src="./glassdb.png" width="100" height="100" /></td>
        <td valign="middle"><h1>ODBParser</h1></td>
    </tr>
</table>


TL;DR
-------------
ODBParser is a tool to search for PII being exposed in open databases. 

<b>ONLY to be used to identify exposed PII and warn server owners of irresponsible database maintenance 
    OR to query databases you have permission to access!

PLEASE USE RESPONSIBLY</b>


What is this?
-------------
Wrote this as wanted to create one-stop OSINT tool for searching, parsing and analyzing open databases in order to identify leakages of PII on third-party servers. Other tools seem to either only search for open databases or dump them once you've identified them and then will grab data indiscriminately. Grew from function or two into what's in this repo, so code isn't as clean and pretty as it could be.

Features
-------------
To identify open databases you can:
* query <b>Shodan</b> and <b>BinaryEdge</b> using all possible parameters (filter by country, port number, whatever)
* specify single IP address
* load up file that has list of IP addresses
* paste list of IP addresses from clipboard

Dumping options:
* parses all databases/collections to identify data you specify
* grab everything hosted on server
* grab just one index/collection

Post-Processing:
* convert JSON dumps to CSV
* remove useless columns from CSV

Other features:
* keeps track of all the IP addresses and databases you have queried along with info about each server.
* maintains stats file with number of IP's you've queried, number of databases you've parsed and number of records you've dumped
* convert JSON dumps you already have to CSV
* for every database that has total number of records above your limit, script will create an entry in a special file along with 5 sample records so you can review and decide whether the database is worth grabbing
* Output is JSON. You can convert the files to CSV on the fly or you can convert only certain files after run is complete (I recommend latter). Converted JSON files will be moved to folder called "JSON backups" in same directory. <b>NOTE:</b> When converting to CSV, script drops exact duplicate rows and drops columns and rows where all values are NaN, because that's what I wanted to do. Feel free to edit function if you'd rather have exact copy of JSON file.
* <b>Windows ONLY</b> If script pulls back huge number of indices that have field you care about, script will list names of the dbs, pause and give you ten seconds to decide whether you want to go ahead and pull all the data from every index as I've found if you get too many databases returned even after you've specified fields you want, there is a good chance data is fake or useless logs and you can usually tell from name whether either possibility is the case. If you don't act within 10 seconds, script will go ahead and dump every index.
* as you may have noticed, lot of people have been scanning for MongoDB databases and holding them hostage, often changing name to something like "TO_RESTORE_EMAIL_XXXRESTORE.COM." The MongoDb scraper will ignore all databases and collections that have been pwned by checking name of DB/collection against list of strings that indicate pwnage
* script is pretty verbose (maybe too verbose) but I like seeing what's going on. Feel free to silence print statements if you prefer.

Customization
-------------
See the odbconfig.py file to specify your parameters, because really name of the game is exposing the data YOU are interested in. I provided some examples in the config file. Play around with them!

You can:

* specify what index or collection names you want to collect by specifying substrings in config file. For example, if have the term "client", script will pull index called "clients" or "client_data." I recommend you keep these lists blank as you never know what databases you care about will be called and instead specify the fields you care about.
* specify what fields you care about: if you only want to grab ES indices that have  "email" in a field name, e.g."user_emails", you can do that. If you want to make sure the index has at least 2 fields you care about, you can do that too. Or if you just want to grab everything no matter what fields are in there, you can do that too.
* specify what indices you DON'T want e.g., system index names and others that are generally used for basic logging. Examples provided in config file.
* override config and grab everything on a server
* specify output (default is JSON, can choose CSV)
* set minimum and maximum size database script will dump by default and you can set flag to override max docs on case by case basis.


Installation and Requirements
-------------
* Clone or download to machine
* Get API keys for Shodan and/or BinaryEdge
* configure parameters in ODBconfig.py file
* install requirements from file

I suggest creating virtual environment for ODBParser so have no issues with incorrect module versions.
<b>Note:</b> Tested ONLY on Python 3.7.3 and on Windows 10.

<b>PLEASE USE RESPONSIBLY</b>


Next Steps and Known Issues
-------------
* clean up code a bit more
* multithread various processes.
* expand to other db types
* add other open directory search engines (Zoomeye, etc.)
* unable to scroll past first page for certain ES instances due to way ES <2.0 works. Appreciate any help! <b>Pretty sure fixed this. Open issue if get scrollid errors</b>

Usage
-------------
```
    Examples: python ODBParser.py -cn US -p 8080 -t users --elastic --shodan --csv --limit 100
              python ODBParser.py -ip 192.168.2:8080 --mongo --ignorelogs --nosizelimits

    Damage to-date: 0 servers parsed | 0 databases dumped | 0 records pulled
    _____________________________________________________________________________


optional arguments:
  -h, --help            show this help message and exit

Query Options:
  --shodan, -sh         Add this flag if using Shodan. Specify ES or MDB w/
                        flags.
  --binary, -be         Add this flag if using BinaryEdge. Specify ES or MDB
                        w/ flags.
  --ip , -ip            Query one server. Add port like so '192.165.2.1:8080'
                        or will use default ports for each db type. Add ES or
                        MDB flags to specify parser.
  --file , -f           Load line-separated IPs from file. Add port or will
                        assume default ports for each db type. Add ES or MDB
                        flags to specify parser.
  --paste, -v           Query line-separated IPs from clipboard. Add port or
                        will assume default ports for each db type, e.g. 9200
                        for ES. Add ES or MDB flags to specify parser.

Shodan/BinaryEdge Options:
  --limit , -l          Max number of results per query. Default is
                        500.
  --port , -p           Filter by port.
  --country , -cn       Filter by country (two-letter country code).
  --terms , -t          Enter any additional query terms you want here, e.g.
                        'users'

Dump Options:
  --mongo, -mdb         Use for IP, Shodan, BinaryEdge & Paste methods to
                        specify parser.
  --elastic, -es        Use for IP, Shodan, BinaryEdge & Paste methods to
                        specify parser.
  --database , -db      Specify database you want to grab. For MDB must be in
                        format format 'db:collection'. Use with IP arg & 'es'
                        or 'mdb' flag
  --getall, -g          Get all indices regardless of fields and
                        collection/index names (overrides selections in config
                        file).
  --ignorelogs          Connect to a server you've already checked out.
  --nosizelimits, -n    Dump index no matter how big it is. Default max doc
                        count is 800,000.
  --csv                 Convert JSON dumps into CSV format on the fly. (Puts
                        JSON files in backup folder in case there is issue
                        with conversion)

CSV/Post-processing Options:
  --convertToCSV , -c   Convert JSON file or folder of JSON dumps to CSVs
                        after the fact. Enter full path or folder name in
                        current working directory
  --dontflatten         Use if run into memory issues converting JSON files to
                        CSV during post-processing.
  --basic               Use with --convertToCSV flag if your JSON dumps are
                        not true JSON files, but rather line separated JSON
                        objects that you got from other sources.
  --dontclean, -dc      Choose if want to keep useless data when convert to
                        CSV. See docs for more info.
 ```
