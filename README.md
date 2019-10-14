lotw_tool.py by John Ackermann   N8UR   jra@febo.com

This is a simple tool to download and/or parse the ADIF format files
delivered by queries to the ARRL Log of The World (LoTW) service.
It can also access the QRZ.com XML interface to get nominal grids for
QSOs where the grid is not know.

There are two ways to get data:

1.  To download and process an LoTW file, supply the --login, --password,
and --logcall parameters.  --logcall is the "my callsign" requested and
is required because multiple callsigns can be registered to one account.

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

ALL THE OPTIONS (as of 2019-10-13.1):
```
usage: lotw_tool.py [-h] [--adifile ADIFILE] [--login LOGIN]
                    [--password PASSWORD] [--logcall LOGCALL]
                    [--own_gridsquare OWN_GRIDSQUARE]
                    [--qso_qsl | --qso_noqsl] [--match_missing_grids]
                    [--qrz_login QRZ_LOGIN] [--qrz_password QRZ_PASSWORD]
                    [--qso_startdate QSO_STARTDATE]
                    [--qso_enddate QSO_ENDDATE] [--qso_call QSO_CALL]
                    [--qso_band QSO_BAND] [--qso_mode QSO_MODE] [--dx_only]
                    [--gridsquare GRIDSQUARE]
                    [--sortby {CALL,GRIDSQUARE,STATE,COUNTRY,BAND,MODE}]
                    [--logfile LOGFILE] [--separator SEPARATOR]

Tool to download/parse ARRL Log of the World ADI files

optional arguments:
  -h, --help            show this help message and exit
  --adifile ADIFILE     read this ADI file (if blank, download from LoTW
  --login LOGIN         LOtW user name
  --password PASSWORD   LOtW user password
  --logcall LOGCALL     Select QSOs where my call is this
  --own_gridsquare OWN_GRIDSQUARE
                        Select QSOs where my grid is this
  --qso_qsl             Download only QSOs with QSL (default download all)
  --qso_noqsl           Output only QSOs without QSL)
  --match_missing_grids
                        Merge QRZ grid data to QSOs with missing grid
  --qrz_login QRZ_LOGIN
                        QRZ user name
  --qrz_password QRZ_PASSWORD
                        QRZ user password
  --qso_startdate QSO_STARTDATE
                        Output QSOs after this date (YYYY-MM-DD)
  --qso_enddate QSO_ENDDATE
                        Output QSOs before this date (YYYY-MM-DD)
  --qso_call QSO_CALL   Output QSOs with this call
  --qso_band QSO_BAND   Select QSOs where the band is this (e.g., '6M')
  --qso_mode QSO_MODE   Select QSOs where the mode is this (e.g., 'CW')
  --dx_only             Select QSOs where country is not U.S.A.
  --gridsquare GRIDSQUARE
                        Select QSOs from this grid; 'None' for missing
  --sortby {CALL,GRIDSQUARE,STATE,COUNTRY,BAND,MODE}
  --logfile LOGFILE     Log file name (if not given, autogenerate it
  --separator SEPARATOR
                        Log file field separator (default is tab)
```
