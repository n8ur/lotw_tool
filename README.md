lotw_tool.py by John Ackermann   N8UR   jra@febo.com

This is a simple tool to download and/or parse the ADIF format files
delivered by queries to the ARRL Log of The World (LoTW) service.
It can also access the QRZ.com XML interface to get nominal grids for
QSOs where the grid is not know.

There are two ways to get data:

1.  To download and process an LoTW file, supply the --login, --password,
and --logcall parameters.  --logcall is the "my callsign" requested and
is required because multiple callsigns can be registered to one account.

You can also place these command line values in a config file.
This allows the password to be removed from the command line history file.
See the config section below.

The program will send a request to the ARRL web server and will save the
results to a file.  You can specify the name with the --adifile option; if
you don't, the filename will be in the format CALLYYYYMMDD-HHMMSS.adi.

It often takes the ARRL server a while to think on the request, so don't
be surprised if nothing happens for a minute or even longer.

2.  If you already have an ADI file to work with (likely one created using
option 1), you can specify it with the --adifile option.  In that case,
do NOT enter the --login, --password, or --logcall options; or any of
the selection options described below other than --gridsquare or --dx_only .

In either case, the results will also be processed into a logfile in more 
human- (and computer-parser-) friendly format.  You can specify a name for 
that file with the --outfile option.  If you don't, the output file will 
have the same name as the adi file except that the extension will be 
changed to ".log".

The fields in the output file are by default separated with a tab character.
You can use another character by specifying it with the --separator option.
For example, to create a CSV (comma separated values) file, use
"--separator ,"  Nonprinting characters like tab should used the escaped
value, e.g., "\t" for tab, "\n" for newline, or "\r\n" for CRLF on a
Windows system.

SELECTION CRITERIA:
The LoTW interface allows records selected by QSO start date (and if so,
optional end date), station call, QSO mode, and QSO band.  You may
make those selections with the --qso_startdate, --qso_enddate,
--qso_call, --qso_band, and --qso_mode options.  Note that the program
does NOT do any validation on the parameters you specify.  Also note
that the LoTW interfaces allows adding starting and ending time to
the QSO date range, but for the moment I have not included that.  It
seems that selection by date range ought to be sufficient.

In addition to those selections, I've added a couple of filter
criteria that are applied AFTER the adifile is downloaded (i.e., these
criteria do NOT affect the content of the adifile.  These options are:

--gridsquare : output only records for specified 4, 6, or 8 character
grid.  If "None" (or "none" or "NONE") is entered, only QSO records
with no gridsquare will be output.

--dx_only : admittedly, this is U.S.-centric.  If this option selected
(it takes no parameters), output only records for DXCC entities other than
the U.S.  (Note: LoTW allows you to select a DXCC country during the download
phase, but the country is identified by DXCC number only, which doesn't seem
too practical.  So I've chosen (for now) not to implement this criterion.)

SORTING:
The output records are always sorted by QSO date and time.  Additionally,
you may select one additional sort field with the --sortby option.  It
accepts CALL, GRIDSQUARE, STATE, COUNTRY, BAND, and MODE as parameters.
Your entry will automatically be changed to upper case if necessary.

FINDING MISSING AND UNCONFIRMED GRIDS:
This is really why I wrote the program.  If you specify the 
"--match_missing_grids" argument and supply your QRZ.com login credentials
with the '--qrz_login" and "-qrz_password" parameters, the program
will read the log file and extract the call field from QSOs where the
grid is unknown.

The program will then feed those callsigns to the QRZ.com XML interface
which will return (among other things) the grid of reference for 
the call.  If the grid is unknown, it will be set to "----".  The results
will be written to file with a name ending "qrz_grids.txt".

Then, that file will be further processed to create two more files:

-- one ending with "gridless.txt" will contain callsigns for which
a grid couldn't be found.  This could be rovers, silent keys (no longer
in the QRZ database), or busted calls.

-- one ending with "unconfirmed.txt" that consists of calls and grids where
the grid does not show up in the LoTW file as being confirmed.  This is the
list you'll want to start with to pump up your grid count.

TYPICAL RUN:
```
jra@flob:~/src/ham-tools/lotw_tool$ ./lotw_tool.py --login n8ur --password xxxx --logcall n8ur --mygrid EN75 --band 6M --match_missing_grids --qrz_login n8ur --qrz_password xxxx

lotw_tool.py by N8UR, version 2019-10-18.1
Sending data request to LoTW...
Saving adif data as n8ur20191018-111518.adi (this may take a while)...
Writing processed log file to n8ur20191018-111518.log
Querying QRZ.com for 587 calls. ...........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................
Finished getting QRZ.com matches for 587 calls in 53
seconds, and wrote data to n8ur20191018-111518_qrz_matches.txt
Writing 265 confirmed grids to n8ur20191018-111518_confirmed_grids.txt
Wrote 33 QSOs (30 unique calls) with no grid
	to n8ur20191018-111518_gridless.txt...
Wrote list of 41 possibly confirmed grids
	to n8ur20191018-111518_new_grid_list.txt
Wrote 63 QSOs (48 unconfirmed calls) with 41 unconfirmed grids
	to n8ur20191018-111518_unconfirmed.txt

All finished!
```

OUTPUT FILES:
Output files are all prefixed with the "logcall" plus date and time

```
n8ur20191018-111518.adi                     Raw ADIF file returned from LoTW
n8ur20191018-111518_confirmed_grids.txt     LoTW confirmed grids  
n8ur20191018-111518_gridless.txt            QSOs we couldn't match to grid
n8ur20191018-111518.log                     Formatted log file from adifile
n8ur20191018-111518_new_grid_list.txt       List of possible new grids
n8ur20191018-111518_qrz_matches.txt         Results of QRZ.com lookup
n8ur20191018-111518_unconfirmed.txt         QSOs with possible new grids
```

CONFIG FILE

The login and password command arguments can be placed in a config file.
The default location is `~/.lotw_tool/config.cfg` but that can be changed with the `--config` argument.
A sample file is as follows:
```
$ cat ~/.lotw_tool/config.cfg
[LoTW]
login:		LOGIN
password:	PASSWORD
logcall:	LOGCALL
$
```
This file should be `chmod 600` to protect the contents.
Additional sections can be added should you manage more than one login at LoTW.
They are selected via the `--section NAME` argument.
For example, here's a config file with more than one login
```
$ cat ~/.lotw_tool/config.cfg
[A1A]
login:		A1A
password:	PASSWORD
logcall:	A1A
[A1B]
login:		A1B
password:	PASSWORD
logcall:	A1B
$
```
You would use these commands: `lotw_tool.py --section A1A` or `lotw_tool.py --section A1B` to
download from different logins/accounts.
This capability can be extended to all the command line arguments if needed.

Note that using `--adifile` with a config file present can produce the
`NOTE: adifile specified, login/password/logcall/mygrid ignored` warning.
This can be safely ignored.

ALL THE OPTIONS (as of 2024-10-23.1):
```
usage: lotw_tool.py [-h]
                    [--config CONFIGFILE] [--section NAME]
                    [--adifile ADIFILE]
                    [--login LOGIN] [--password PASSWORD] [--logcall LOGCALL]
                    [--mygrid MYGRID] [--qsl | --noqsl]
                    [--match_missing_grids] [--qrz_login QRZ_LOGIN]
                    [--qrz_password QRZ_PASSWORD] [--startdate STARTDATE]
                    [--enddate ENDDATE] [--call CALL] [--band BAND]
                    [--mode MODE] [--dx_only] [--grid GRID]
                    [--sortby {CALL,GRIDSQUARE,STATE,COUNTRY,BAND,MODE}]
                    [--logfile LOGFILE] [--separator SEPARATOR]

Tool to download/parse ARRL Log of the World ADI files

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIGFILE   read this config file (default: ~/.lotw_tool/config.cfg)
  --section NAME        config file section name (default: 'LoTW')
  --adifile ADIFILE     read this ADI file (if blank, download from LoTW
  --login LOGIN         LOtW user name
  --password PASSWORD   LOtW user password
  --logcall LOGCALL     Select QSOs where my call is this
  --mygrid MYGRID       Select QSOs where my grid is this
  --qsl                 Download only QSOs with QSL (default download all)
  --noqsl               Output only QSOs without QSL)
  --match_missing_grids
                        Merge QRZ grid data to QSOs with missing grid
  --qrz_login QRZ_LOGIN
                        QRZ user name
  --qrz_password QRZ_PASSWORD
                        QRZ user password
  --startdate STARTDATE
                        Output QSOs after this date (YYYY-MM-DD)
  --enddate ENDDATE     Output QSOs before this date (YYYY-MM-DD)
  --call CALL           Output QSOs with this call
  --band BAND           Select QSOs where the band is this (e.g., '6M')
  --mode MODE           Select QSOs where the mode is this (e.g., 'CW')
  --dx_only             Select QSOs where country is not U.S.A.
  --grid GRID           Select QSOs from this grid; 'None' for missing
  --sortby {CALL,GRIDSQUARE,STATE,COUNTRY,BAND,MODE}
  --logfile LOGFILE     Log file name (if not given, autogenerate it
  --separator SEPARATOR
                        Log file field separator (default is tab)

```
