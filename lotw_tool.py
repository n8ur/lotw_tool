#! /usr/bin/env python3

#############################  N8UR lotw_tool.py  ##############################
#
#       Copyright 2019 by John Ackermann, N8UR jra@febo.com
#       https://febo.com -- https://github.com/n8ur
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
###############################################################################

version = "2019-10-18.1"

import sys
import string
import time
import requests
from requests.exceptions import HTTPError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pathlib import Path
import argparse

###############################################################################
# Fields contained in LOTW download
###############################################################################
field_keys = [
    'APP_LoTW_2xQSL','APP_LoTW_CQZ_Inferred','APP_LoTW_CQZ_Invalid',
    'APP_LoTW_CREDIT_GRANTED','APP_LoTW_DXCC_ENTITY_STATUS',
    'APP_LoTW_GRIDSQUARE_Invalid','APP_LoTW_ITUZ_Inferred',
    'APP_LoTW_ITUZ_Invalid','APP_LoTW_LASTQSORX','APP_LoTW_MODEGROUP',
    'APP_LoTW_MY_CQ_ZONE_Inferre','APP_LoTW_MY_DXCC_ENTITY_STATUS,',
    'APP_LoTW_MY_GRIDSQUARE_Invalid','APP_LoTW_MY_ITU_ZONE_Inferred',
    'APP_LoTW_NUMREC','APP_LoTW_OWNCALL','APP_LoTW_QSLMODE','BAND',
    'CALL','CNTY','COUNTRY','CQZ','CREDIT_GRANTED','DXCC','FREQ',
    'GRIDSQUARE','IOTA','ITUZ','MODE','MY_CNTY','MY_COUNTRY','MY_CQ_ZONE',
    'MY_DXCC','MY_GRIDSQUARE','MY_ITU_ZONE','MY_STATE','PFX','PROGRAMID',
    'QSL_RCVD','QSLRDATE','QSO_DATE','STATE','STATION_CALLSIGN','TIME_ON'
    ]

###############################################################################
# getargs -- get command line arguments and supply defaults
###############################################################################
def getargs():
    parser = argparse.ArgumentParser(description=
            'Tool to download/parse ARRL Log of the World ADI files')

    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    # login and file parametersp
    parser.add_argument('--adifile',type=str,
                      help='read this ADI file (if blank, download from LoTW')

    # note: --login, --password, --logcall, --mygrid
    # are all ignored if --adifile is specified
    parser.add_argument("--login", help='LOtW user name')
    parser.add_argument("--password", help='LOtW user password')

    # these options help select log call or location since LoTW
    # doesn't allow you to sort by the location defined in tQSL.
    parser.add_argument('--logcall',type=str,
                      help='Select QSOs where my call is this')
    parser.add_argument('--mygrid',type=str.upper,
                      help='Select QSOs where my grid is this')

    # selection parameters
    qso_status = parser.add_mutually_exclusive_group()
    qso_status.add_argument('--qsl', action='store_true',
                      help='Download only QSOs with QSL (default download all)')
    qso_status.add_argument('--noqsl', action='store_true',
                      help='Output only QSOs without QSL)')

    # this causes a QRZ lookup for QSOs without grid information.
    # output goes to a separate file with de-duped call and QRZ
    # grid
    parser.add_argument('--match_missing_grids', action='store_true',
                      help='Merge QRZ grid data to QSOs with missing grid')
    parser.add_argument("--qrz_login", help='QRZ user name')
    parser.add_argument("--qrz_password", help='QRZ user password')

    
    parser.add_argument('--startdate',type=str,
                      help='Output QSOs after this date (YYYY-MM-DD)')
    parser.add_argument('--enddate',type=str,
                      help='Output QSOs before this date (YYYY-MM-DD)')
    parser.add_argument('--call',type=str.upper,
                      help='Output QSOs with this call')
    parser.add_argument('--band',type=str.upper,
                      help='Select QSOs where the band is this (e.g., \'6M\')')
    parser.add_argument('--mode',type=str.upper,
                      help='Select QSOs where the mode is this (e.g., \'CW\')')

    # LoTW allows you to select QSOs by numbered DXCC entity, which isn't
    # all that useful if you have to map the country name to the number
    # (and I'm way too lazy to build a lookup, and even if I did, you
    # wouldn't enter the name exactly the same way_.  But it might be
    # useful to see only DX (being U.S.-centric, that means anything
    # that's not U.S.A.).  Selecting this doesn't affect the adifile
    # contents as the filter is applied only at the output stage.
    parser.add_argument('--dx_only',action='store_true',
                      help='Select QSOs where country is not U.S.A.')

    # LoTW doesn't allow you to specify grid in the download, so
    # if you specify --grid it won't affect the contents of the
    # downloaded adifile.  However, the log output will be filtered
    # to include only the selected grid.  If you want to find records
    # where the grid is blank, use this option with "None" as the argument.
    parser.add_argument('--grid',type=str.upper,
                      help='Select QSOs from this grid; \'None\' for missing')

    # sort parameters.  To keep things sane, you can
    # only sort by one of these (plus QSO date/time).  Input will be
    # changed to upper case.
    choices=['CALL','GRIDSQUARE', 'STATE', 'COUNTRY', 'BAND', 'MODE']
    parser.add_argument('--sortby',type=str.upper,default=None,choices=choices)

    # output file parameters
    parser.add_argument('--logfile',type=str,
                      help='Log file name (if not given, autogenerate it')
    parser.add_argument('--separator',type=str,default='\t',
                      help='Log file field separator (default is tab)')

    args = parser.parse_args()

    if not args.adifile:
        if not args.login or not args.password or not args.logcall:
            parser.error("Error: either login/password/logcall or "\
                              "adifile required")

#    if args.match_missing_grids:
#        if not args.qrz_login or not argz.qrz_password:
#            parser.error("Error: --qso_nogrid requires QRZ login and password")

    if args.adifile and (args.login or args.password or args.logcall):
        print("NOTE: adifile specified, login/password/logcall/"\
                "mygrid ignored")
    if args.grid in ['none','None','NONE']:
        args.grid = '----'

    if args.qsl:
        args.qsl = 'yes'
    else:
        args.qsl = 'no'

    if args.noqsl:
        args.noqsl = 'yes'
    else:
        args.noqsl = 'no'

    if args.dx_only:
        args.dx_only = 'yes'
    else:
        args.dx_only = 'no'

    return args
###############################################################################
# http_get_request -- send data to URL and return response
###############################################################################
def http_get_request(url,data,ssl=False):
    s = requests.Session()
    retries = Retry(total=6, backoff_factor=0,
        status_forcelist=[ 502, 503, 504 ])
    if ssl:
        s.mount('https://', HTTPAdapter(max_retries=retries))
    else:
        s.mount('http://', HTTPAdapter(max_retries=retries))

    r = s.get(url,params=data)
    return r.text

###############################################################################
# extract_fields -- take input record and split on "<" to separate
# fields, then do a bit of processing and write to dict
###############################################################################
def extract_fields(record):
    d = dict.fromkeys(field_keys, None)  # make empty dict

    # need to give a default value for sortable fields to
    # avoid breaking python3 sort
    d['GRIDSQUARE'] = '----'
    d['STATE'] = '--'   # Field is only two columns

    fields = record.split('<')
    for f in fields:
        f = str(f.strip())
        for k in field_keys:
            if f.startswith(k):
                   d[k] = str(f.split('>')[1])
    return d
                
###############################################################################
# format_qso -- format and output QSO record
###############################################################################
def format_qso(rec):
    def make_month(argument):
        months = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec"
        }   
        return months.get(argument, "Invalid month")

    year = rec['QSO_DATE'][:4]
    month = make_month(int(rec['QSO_DATE'][4:6]))
    day = rec['QSO_DATE'][6:8]
    date = year + "-" + month + "-" + day

    time = rec['TIME_ON'][:2] + ":" + rec['TIME_ON'][2:4] \
        + ":" + rec['TIME_ON'][4:6]

    sep = args.separator
    outrec = "{}T{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}".format(
            date, time, sep, rec['CALL'], sep, rec['BAND'], 
            sep, rec['MODE'], sep, rec['QSL_RCVD'], sep, rec['GRIDSQUARE'],
            sep, rec['STATE'][:2], sep, rec['COUNTRY'])
    return outrec

###############################################################################
# dedupe_list -- sort and remove duplicates from input list
###############################################################################
def dedupe_list(in_list):
    work = sorted(in_list)
    seen = set()
    work = [x for x in work if x not in seen and not seen.add(x)]
    return work

###############################################################################
# get_adifile -- download from lotw based on criteria and save as file
###############################################################################
def get_adifile(args, adifile):
    print("Sending data request to LoTW...")
    print("Saving adif data as",adifile,"(this may take a while)...")

    data = { 'login':args.login,'password':args.password,
       'qso_query':'yes','qso_detail':'yes','qso_mydetail':'yes',
       'qso_qsldetail':'yes', 'qso_withown':'yes',
       'qso_logcall':args.logcall}

    # add selection criteria if set
    # note: we can't specify QSO grid here, so we filter
    # for that in the output routine below
    if args.startdate:
        data['qso_startdate'] = args.startdate
    if args.enddate:
        data['qso_enddate'] = args.startdate
    if args.qsl:
        data['qso_call'] = args.call
    if args.band:
        data['qso_band'] = args.band
    if args.mode:
        data['qso_mode'] = args.mode
    if args.qsl:
        data['qso_qsl'] = args.qsl

    base_url = 'https://lotw.arrl.org/lotwuser/lotwreport.adi'

    # not using http_get_request() because we want to stream
    r = requests.get(base_url,params=data, stream=True)

    with open(adifile,'wb') as f:
        for data in r.iter_content(4096):
            f.write(data)

###############################################################################
# make_logfile -- process adifile to logfile format
###############################################################################
def make_logfile(args,adifile,logfile):
    with open(adifile,encoding='latin1') as f:
        qso_list = []   # this will be the list of QSOs logged
        record_delimiter = "<eo" # could be '<eoh>' or '<eor>'
    
        buf = f.read()
        buf = buf.split(record_delimiter)
        for q in buf:
            d = extract_fields(q)
            while d['CALL']:    # without a call, it's not real

                # can't select for these fields in the LoTW request,
                # so filter for them here

                # print only if my grid matches
                if args.mygrid:
                    if args.mygrid not in d['MY_GRIDSQUARE']:
                        break

                # if --dx_only, exclude records where country is U.S.A.
                if args.dx_only == 'yes' and \
                    d['COUNTRY'] == "UNITED STATES OF AMERICA":
                        break

                # print only if QSO grid matches, or if specified
                # "None" then only if there is no grid in record
                if args.grid:
                    if args.grid == "----" and not d['GRIDSQUARE']:
                        qso_list.append(d)
                    elif d['GRIDSQUARE'] and args.grid in d['GRIDSQUARE']:
                        qso_list.append(d)
                    break
                    
                # if noqsl, exclude records where QSL_RCVD is Y
                if args.noqsl:
                    if args.noqsl == 'yes' and d['QSL_RCVD'] == 'Y':
                        break
    
                qso_list.append(d)
                break
    
    # sort by 'CALL','GRIDSQUARE', 'STATE', 'COUNTRY', 'BAND', or 'MODE'
    # first, then by date and time

    if args.sortby:
        sorted_by = sorted(qso_list, key = lambda i: (i[args.sortby],
        i['QSO_DATE'], i['TIME_ON']))
    else:
        sorted_by = sorted(qso_list, key = lambda i: (i['QSO_DATE'], i['TIME_ON']))

    # write output file
    print("Writing processed log file to",logfile)

    # create file header showing params
    options = vars(args)
    optstring = ""
    for k,v in sorted(vars(args).items()):
        if v:
            if k == 'password':
                v = "****"
            if k == 'qrz_password':
                v = "****"
            if k == 'separator':
                v = repr(v)

            optstring += "--{0}: {1}; ".format(k,v)

    words = iter(optstring.split(';'))
    lines, current = [], next(words)
    for word in words:
        if len(current) + 1 + len(word) > 70:
            lines.append(current)
            current = word
        else:
            current += " " + word
    lines.append(current)

    # logfile is the logfile created from the adifile
    with open(logfile,'w') as f:
        string = "# Log file created by lotw_tool.py v" + version + \
                " from " + adifile + "\n"
        f.write(string)
        for l in lines:
            if len(l) > 1:
                l = '# ' +l + '\n'
                f.write(l)
        string = \
            "# Fields: Date, Call, Band, Mode, QSL, Grid, State, Country\n"
        f.write(string)

        for rec in sorted_by:
            string = format_qso(rec) + '\n'
            f.write(string)

###############################################################################
# get_confirmed_grids -- reads logfile writes a sorted,
# deduped list of confirmed grids
###############################################################################
def get_confirmed_grids(args,logfile):
    # this list will hold all the grids from the logfile, sorted and deduped
    log_grids = []

    # get list of confirmed grids from logfile
    with open(logfile,encoding='latin1') as f:
        for line in f:
            if line.startswith('#'):
                continue
            fields = line.split(args.separator)  
            if fields[5][:4] != '----':
                # add to the list of confirmed grids
                log_grids.append(fields[5][:4])

    # sort and remove duplicates
    log_grids = dedupe_list(log_grids)

    p = Path(logfile)
    confirmed_grids_file = str(p.parent.joinpath(p.stem +
        "_confirmed_grids.txt"))

    print("Writing", len(log_grids),"confirmed grids to ",end="")
    print(confirmed_grids_file)

    with open(confirmed_grids_file,"w") as f:
        string = "# List of " + str(len(log_grids)) + \
                " confirmed grids created by lotw_tool.py\n"
        f.write(string)
        string = "# v" + version + " from " + logfile + "\n"
        f.write(string)
        for x in log_grids:
            string = x + '\n'
            f.write(string)

###############################################################################
# get_qrz_grids -- read logfile, extract calls without grid, send list to
# qrz.com to fetch what they think the grid is
###############################################################################
def get_qrz_grids(args,logfile,outfile):

    # this list will hold all the calls from the logfile, sorted and deduped
    log_calls = []
    # this list will hold all the grids from the logfile, sorted and deduped
    log_grids = []

    # this list will hold the list of calls and grids returned from qrz.com
    qrz_grids = []

    # get list of ungridded calls from logfile
    with open(logfile,encoding='latin1') as f:
        for line in f:
            if line.startswith('#'):
                continue
            fields = line.split(args.separator)  
            if fields[5][:4] == '----':
                # need to look up this call in qrz
                log_calls.append(fields[1])

    # sort and remove duplicates
    log_calls = dedupe_list(log_calls)

    print("Querying QRZ.com for",len(log_calls),"calls.",end=" ")

    # login to QRZ.com and get session key
    qrz_https_url = "https://xmldata.qrz.com/xml/current/"
    qrz_http_url = "http://xmldata.qrz.com/xml/current/"
    agent = "lotw_tool_v" + version
    data = { 'username':args.qrz_login,'password':args.qrz_password,
            'agent':agent }
    r = http_get_request(qrz_https_url,data,ssl=True)
    key = ""
    fields = r.split()
    for rec in fields:
        # poor man's xml parser
        if '<Key>' in rec:
            key = rec.replace('>','<').split('<')[2]

    # now fetch grid from QRZ.com using session key for each call
    qrz_list = []
    start_time = time.time()
    for call in log_calls:
        data = { 's':key,'callsign':call }
        r = http_get_request(qrz_http_url,data,ssl=False)
        fields = r.split()

        # if qrz doesn't know the grid, it stays as '----'
        grid = "----"
        for rec in fields:
            # poor man's xml parser
            if '<grid>' in rec:
                grid = rec.replace('>','<').split('<')[2]

        qrz_list.append([grid[:4],call])
        print('.',end='',flush=True)

    qrz_list = sorted(qrz_list)
    num  = len(qrz_list)

    # write the qrz results to file
    with open(outfile,'w') as f:
        string = "# Call/grid match from QRZ.com created by lotw_tool.py\n"
        f.write(string)
        string = str("# v" + version + " from " + outfile + "\n")
        f.write(string)
        for l in qrz_list:
            string = l[0] + '\t' + l[1] + '\n'
            f.write(string)
    print()
    print("Finished getting QRZ.com matches for", num, "calls in", \
    "{:.0f}".format(time.time() - start_time))
    print("seconds, and wrote data to",outfile)

##############################################################################
# get_gridless -- create list of calls/qsos for which we haven't
# been able to find a grid
##############################################################################
def get_gridless(logfile,qso_list,qrz_grids):
    # this file will hold the QSOs for which we still don't have a grid
    p = Path(logfile)
    gridless_file = str(p.parent.joinpath(p.stem + '_gridless.txt'))
    gridless = []   # list of calls with no matching grid
    gridless_qsos = []  # list of qsos with those calls

    for x in qrz_grids:
        if len(x) == 2 and x[0][:4] == '----':
            gridless.append(x[1])
    gridless = dedupe_list(gridless)

    for x in gridless:
        for y in qso_list:
            if x.strip() in y and y[5][:4] == '----':
                gridless_qsos.append(y)    

    # sort by call, then date
    gridless_qsos.sort(key=lambda x: (x[1],x[0]))

    with open(gridless_file,'w') as f:
        string = "# " + str(len(gridless_qsos)) + \
                " QSOs whose grids cannot be found, created by lotw_tool.py\n"
        f.write(string)
        string = "# v" + version + " from " + qrzfile + "\n"
        f.write(string)
        string = "#\n"
        f.write(string)
        string = "# Rovers:\n"
        f.write(string)
        for x in gridless_qsos:
            if '/R' in x[1]:
                string = "{}{}{}{}{}{}{}{}{}{}{}{}{}{}\n".format(
                    x[0],sep,x[1],sep,x[2],sep,x[3],sep,x[4],
                    sep,x[5],sep,x[6],sep,x[7])
                f.write(string)
        string = "#\n"
        f.write(string)
        string = "# Others:\n"
        f.write(string)
        for x in gridless_qsos:
            if '/R' not in x[1]:
                string = "{}{}{}{}{}{}{}{}{}{}{}{}{}{}\n".format(
                    x[0],sep,x[1],sep,x[2],sep,x[3],sep,x[4],
                    sep,x[5],sep,x[6],sep,x[7])
                f.write(string)

    print("Wrote {} QSOs ({} unique calls) with no grid\n\tto {}...".format(
        len(gridless_qsos),len(gridless),gridless_file))

##############################################################################
# get_unconfirmed_grids -- build list of grids/qsos that we think we
# have worked that we think might be unconfirmed
##############################################################################
def get_unconfirmed_grids(logfile,qso_list,confirmed_grid_list,qrz):
    # this file will hold calls and qrz grids for possibly unconfirmed grids
    p = Path(logfile)
    unconfirmed_file = str(p.parent.joinpath(p.stem + '_unconfirmed.txt'))
    new_grid_file = str(p.parent.joinpath(p.stem + '_new_grid_list.txt'))

    # remove calls from qrz_grids where we still don't have a grid
    qrz[:] = [x for x in qrz if x[0][:4] != '----']
    # remove calls with a grid we've already confirmed
    qrz[:] = [x for x in qrz if x[0][:4] not in confirmed_grid_list]

    # we might have worked this station another time and gotten
    # a grid then.  Exclude that call, at the slight risk
    # they might have moved to another grid.
    def check_qso_list(call,qso_list):
        q_with_grid = False
        for x in qso_list:
            if x[1] == call and x[5][:4] != '----':
                q_with_grid = True
        return q_with_grid       

    qrz[:] = [x for x in qrz if not check_qso_list(x[1],qso_list)]

    # generate and write list of possibly new grids to file
    new_grids = []
    for x in qrz:
        new_grids.append(x[0][:4])
    new_grids.sort()
    new_grids = dedupe_list(new_grids)
    with open(new_grid_file,'w') as f:
        string = "# These " + str(len(qrz_grids)) + \
            " grids might be new; created by lotw_tool.py\n"
        f.write(string)
        string = "# v" + version + " from " + qrzfile + "\n"
        f.write(string)
        for x in new_grids:
            string = x + '\n'
            f.write(string)
    print("Wrote list of",len(new_grids),"possibly confirmed grids")
    print("\tto", new_grid_file)

    # create the qso list
    unconfirmed_qsos = []
    for x in qrz:
        for y in qso_list:
            if y[1] == x[1]:
                # replace the '----' with putative grid in angle brackets
                y[5] = '<' + x[0] + '>'
                unconfirmed_qsos.append(y)    
    # sort by grid, call, date
    unconfirmed_qsos.sort(key=lambda x: (x[5],x[1],x[0]))

    # this list is just to know how many calls represent possibly unconfirmed
    unconfirmed_calls = []
    for x in unconfirmed_qsos:
        if x[1]:
            unconfirmed_calls.append(x[1])
    unconfirmed_calls.sort()
    unconfirmed_calls = dedupe_list(unconfirmed_calls)

    with open(unconfirmed_file,'w') as f:
        string = "# " + str(len(unconfirmed_qsos)) + \
            " QSOs that might represent " + str(len(new_grids)).strip() + \
            " new grids, created by lotw_tool.py\n"
        f.write(string)
        string = "# v" + version + " from " + qrzfile + "\n"
        f.write(string)
        string = "# Grid fields are from QRZ.com data\n"
        f.write(string)
        for x in unconfirmed_qsos:
            string = "{}{}{}{}{}{}{}{}{}{}{}{}{}{}\n".format(
                    x[0],sep,x[1],sep,x[2],sep,x[3],sep,x[4],
                    sep,x[5],sep,x[6],sep,x[7])
            f.write(string)

    print(("Wrote {} QSOs ({} unconfirmed calls) " + \
            "with {} unconfirmed grids").format(
            len(unconfirmed_qsos),len(unconfirmed_calls),len(new_grids)))
    print("\tto",unconfirmed_file)
    print()
    print("All finished!")

###############################################################################
###############################################################################
# PROGRAM BEGINS
###############################################################################
###############################################################################

# get options
args = getargs()
sep = args.separator

print()
print("lotw_tool.py by N8UR, version",version)

# if no input file specified, do LoTW download
adifile = args.adifile
if not adifile:
    file_time = time.strftime("%Y%m%d-%H%M%S")
    adifile = args.logcall + file_time + ".adi"
    get_adifile(args,adifile)

# now generate the logfile from the adifile
p = Path(adifile)
if not args.logfile:
    logfile = str(p.parent.joinpath(p.stem + ".log"))
else:
    logfile = args.outfile
make_logfile(args,adifile,logfile)

if args.match_missing_grids:
    # this file will hold the grid/call results from the qrz queries
    qrzfile = str(p.parent.joinpath(p.stem + '_qrz_matches.txt'))
    get_qrz_grids(args,logfile,qrzfile)

    # read in the logfile and build list of QSOs
    qso_list = []
    with open(logfile,'r') as f:
        for l in f:
            if l.startswith('#'):
                continue
            l = l.strip()
            fields = l.split(sep)
            qso_list.append(fields)
    
    get_confirmed_grids(args,logfile)
    
    # read in confirmed grid list
    p = Path(logfile)
    confirmed_grids_file = str(p.parent.joinpath(p.stem +
        "_confirmed_grids.txt"))
    confirmed_grids_list = []
    with open(confirmed_grids_file,'r') as f:
        for l in f:
            if l.startswith('#'):
                continue
            confirmed_grids_list.append(l.strip())

    # read in qrz_grids from qrzfile
    qrz_grids = []
    with open(qrzfile,'r') as f:
        for l in f:
            if l.startswith('#'):
                continue
            l = l.strip()
            fields = l.split(sep)
            qrz_grids.append(fields)

    get_gridless(logfile,qso_list,qrz_grids)

    get_unconfirmed_grids(logfile,qso_list,confirmed_grids_list,qrz_grids)

exit()

