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
#       Software to communicate with Ashtech GPS receivers via serial port.
#
################################################################################

version = "2019-10-07.1"

import sys
import string
import time
import requests
from tqdm import tqdm
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
# printqso -- format and output QSO record
###############################################################################
def formatqso(rec):
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

    # note: --login, --password, --logcall, --own_gridsquare
    # are all ignored if --adifile is specified
    parser.add_argument("--login", help='LOtW user name')
    parser.add_argument("--password", help='LOtW user password')

    # these options help select log call or location since LoTW
    # doesn't allow you to sort by the location defined in tQSL.
    parser.add_argument('--logcall',type=str,
                      help='Select QSOs where my call is this')
    parser.add_argument('--own_gridsquare',type=str.upper,
                      help='Select QSOs where my grid is this')

    # selection parameters
    parser.add_argument('--qso_qsl', action='store_true',
                      help='Output only QSOs with QSL received (default no)')
    parser.add_argument('--qso_startdate',type=str,
                      help='Output QSOs after this date (YYYY-MM-DD)')
    parser.add_argument('--qso_enddate',type=str,
                      help='Output QSOs before this date (YYYY-MM-DD)')
    parser.add_argument('--qso_call',type=str.upper,
                      help='Output QSOs with this call')
    parser.add_argument('--qso_band',type=str.upper,
                      help='Select QSOs where the band is this (e.g., \'6M\')')
    parser.add_argument('--qso_mode',type=str.upper,
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

    # LoTW doesn't allow you to specify gridsquare in the download, so
    # if you specify --gridsquare it won't affect the contents of the
    # downloaded adifile.  However, the log output will be filtered
    # to include only the selected grid.  If you want to find records
    # where the grid is blank, use this option with "None" as the argument.
    parser.add_argument('--gridsquare',type=str.upper,
                      help='Select QSOs from this grid; \'None\' for missing')

    # sort parameters.  To keep things sane, you can
    # only sort by one of these (plus QSO date/time).  Input will be
    # changed to upper case.
    choices=['CALL','GRIDSQUARE', 'STATE', 'COUNTRY', 'BAND', 'MODE']
    parser.add_argument('--sortby',type=str.upper,default=None,choices=choices)

    # output file parameters
    parser.add_argument('--outfile',type=str,
                      help='Output file name (if not given, autogenerate it')
    parser.add_argument('--separator',type=str,default='\t',
                      help='Output file field separator (default is tab)')

    args = parser.parse_args()

    if not args.adifile:
        if not args.login or not args.password or not args.logcall:
            parser.error( "Error: either login/password/logcall or "\
                              "adifile required")
    if args.adifile and (args.login or args.password or args.logcall):
        print("NOTE: adifile specified, login/password/logcall/"\
                "own_gridsquare ignored")
    if args.gridsquare in ['none','None','NONE']:
        args.gridsquare = '----'

    if args.qso_qsl:
        args.qso_qsl = 'yes'
    else:
        args.qso_qsl = 'no'

    if args.dx_only:
        args.dx_only = 'yes'
    else:
        args.dx_only = 'no'

    return args

###############################################################################
# PROGRAM BEGINS
###############################################################################

# get options
args = getargs()

print()
print("lotw_tool by N8UR, version",version)

# if no input file specified, do LoTW download
adifile = args.adifile
if not adifile:
    # assemble request url
    base_url = 'https://lotw.arrl.org/lotwuser/lotwreport.adi'
    data = { 'login':args.login,'password':args.password,
       'qso_query':'yes','qso_detail':'yes','qso_mydetail':'yes',
       'qso_qsldetail':'yes', 'qso_withown':'yes','qso_logcall':args.logcall}

    # add selection criteria if set
    # note: we can't specify QSO grid here, so we filter
    # for that in the output routine below
    if args.qso_startdate:
        data['qso_startdate'] = args.qso_startdate
    if args.qso_enddate:
        data['qso_enddate'] = args.qso_startdate
    if args.qso_qsl:
        data['qso_call'] = args.qso_call
    if args.qso_band:
        data['qso_band'] = args.qso_band
    if args.qso_mode:
        data['qso_mode'] = args.qso_mode
    if args.qso_qsl:
        data['qso_qsl'] = args.qso_qsl

    # send off request to lotw
    adifile = args.logcall + time.strftime("%Y%m%d-%H%M%S") + ".adi"
    print("Sending data request to LoTW...")
    print("Saving adif data as",adifile,"(this may take a while)...")
    r = requests.get(base_url,params=data, stream=True)
    t = tqdm(unit='iB',unit_scale=True)

    with open(adifile,'wb') as f:
        for data in r.iter_content(4096):
            t.update(len(data))
            f.write(data)
    t.close()

# Sort and select the results from either new or existing adifile
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

            # print only if my gridsquare matches
            if args.own_gridsquare:
                if args.own_gridsquare not in d['MY_GRIDSQUARE']:
                    break

            # if --dx_only, exclude records where country is U.S.A.
            if args.dx_only == 'yes' and \
                d['COUNTRY'] == "UNITED STATES OF AMERICA":
                    break

            # print only if QSO gridsquare matches, or if specified
            # "None" then only if there is no gridsquare in record
            if args.gridsquare:
                if args.gridsquare == "----" and not d['GRIDSQUARE']:
                    qso_list.append(d)
                elif d['GRIDSQUARE'] and args.gridsquare in d['GRIDSQUARE']:
                    qso_list.append(d)
                break
            qso_list.append(d)
            break

# sort by 'CALL','GRIDSQUARE', 'STATE', 'COUNTRY', 'BAND', 'MODE' first,
# then by date and time

if args.sortby:
    sorted_by = sorted(qso_list, key = lambda i: (i[args.sortby],
    i['QSO_DATE'], i['TIME_ON']))
else:
    sorted_by = sorted(qso_list, key = lambda i: (i['QSO_DATE'], i['TIME_ON']))

# write output file
if not args.outfile:
    p = Path(adifile)
    outfile = str(p.parent.joinpath(p.stem + '.log'))
else:
    outfile = args.outfile

print()
print("Writing processed log file to:",outfile)

options = vars(args)
optstring = ""
for k,v in sorted(vars(args).items()):
    if v:
        if k == 'password':
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

with open(outfile,'w') as f:
    string = "# Log file created by lotw_tool.py from " + adifile + "\n"
    f.write(string)
    for l in lines:
        if len(l) > 1:
            l = '# ' +l + '\n'
            f.write(l)
    string = \
        "# Fields:  Date/Time, Call, Band, Mode, QSL, Grid, State, Country\n"
    f.write(string)

    for rec in sorted_by:
        string = formatqso(rec) + '\n'
        f.write(string)
exit()
