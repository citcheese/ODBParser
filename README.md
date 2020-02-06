# ODBgrabber
search, parse and dump open ES and MongoDB directories and grab only the data you care about

![](odbdemo2.gif)

Wrote this as wanted to create one-stop shop for searching for, parsing and analyzing open databases in order to get the data I care about.
Other tools seem to either only query open databases or dump them once you've identified them. This tool is one-stop shop for querying and dumping.

In terms of identifying databases you can:
* query Shodan using all possible paramters
* specify single database or single database and index
* paste from list of IP addresses you have

This will also keep track of all the IP addresses and databases you have queried and will check to make sure you haven't already queried the IP. But if you want to connect to server you have already connected to, you have that option.

See the odbconfig.py file to specify your parameters, because really name of the game is getting data YOU care about. I provided some examples in the config file. Play around with them!

Some options you have:
* specify what index or collection names you want to collect by specifying substrings in config file. For example, if have the term "client", script will pull index called "clients" or "client_data." I recommend you keep these lists blank as you never know what databases you care about will be called and instead specify the fields you care about.
* specify what fields you care about: if you only want to grab ES indicdes that have  "email" in a field name, e.g."user_emails", you can do that. If you want to make sure the index has at least 2 fields you care about, you can do that too. Or if you just want to grab everything no matter what fields are in there, you can do that too.

The minimum size database script will dump is 40 documents and max is 800000, but you can set flag to grab database with unlimited number of documents if you like. Just be careful. If you don't set "nolimit" flag, script will create file with indices/collections that were too big along with a sample entry from the index so you can take a look and see if want to grab them later.

Default output of MongoDB is CSV and default for ES is JSON. You can convert ES files to CSV on the fly or you can run script after you dump ES instance to only convert files you care about to JSON. Whatever you want.


Couple of other features:
As you may have noticed, lot of people have been scanning for MongoDB databases and holding them hostage, often changing name to something like "TO_RESTORE_EMAIL_XXX@RESTORE.COM." My MongoDb scraper will ignore all databases and collections that have been pwned by checking name of DB/collection against list of strings that indicate pwnage (check it in mongodbscraper function if want to add your own terms)
Also have scripts set to ignore index names that are generally used for basic logging, e.g. index names with ".kibana" in them. These are coded within functions, so if want to change these, will need to dig into code
Script is pretty verbose, maybe too verbose, but I like seeing what's going on. Feel free to silence print statements if you don't care.
If you already have JSON files that you have dumped from other sources, you can convert them to CSV with the script

Next steps are to clean up code a bit more and multithread processes.
At the moment the tool only works with Elastic and MongoDB, but have plans to expand in time.
