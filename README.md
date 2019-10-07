lotw_tool.py by John Ackermann   N8UR   jra@febo.com

This is a simple tool to download and/or parse the ADIF format files
delivered by queries to the ARRL Log of The World (LoTW) service.

There are two modes of operation:

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
does NOT do any validation on the parameters you specify.

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

ALL THE OPTIONS (as of 2019-10-07.1):
usage: lotw_tool.py [-h] [--adifile ADIFILE] [--login LOGIN]
                    [--password PASSWORD] [--logcall LOGCALL]
                    [--own_gridsquare OWN_GRIDSQUARE] [--qso_qsl]
                    [--qso_startdate QSO_STARTDATE]
                    [--qso_enddate QSO_ENDDATE] [--qso_call QSO_CALL]
                    [--qso_band QSO_BAND] [--qso_mode QSO_MODE] [--dx_only]
                    [--gridsquare GRIDSQUARE]
                    [--sortby {CALL,GRIDSQUARE,STATE,COUNTRY,BAND,MODE}]
                    [--outfile OUTFILE] [--separator SEPARATOR]
