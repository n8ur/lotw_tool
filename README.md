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

2.  If you already have an ADI file to work with (likely one created using
option 1), you can specify it with the --adifile option.  In that case,
do NOT enter the --login, --password, or --logcall options.

In either case, the results will also be processed into a logfile in more 
human- (and computer-parser-) friendly format.  You can specify a name for 
that file with the --outfile option.  If you don't, the output file will 
have the same name as the adi file except that the extension will be 
changed to ".log".

The fields in the output file are by default separated with a tab character.
You can use another character by specifying it with the --separator option.


usage: lotw_tool.py [-h] [--login LOGIN] [--password PASSWORD]
                    [--logcall LOGCALL] [--adifile ADIFILE]
                    [--outfile OUTFILE] [--separator SEPARATOR]
                    [--qso_qsl QSO_QSL] [--qso_startdate QSO_STARTDATE]
                    [--qso_enddate QSO_ENDDATE] [--qso_band QSO_BAND]
                    [--qso_mode QSO_MODE] [--own_gridsquare OWN_GRIDSQUARE]
                    [--gridsquare GRIDSQUARE]
                    [--sortby {CALL,GRIDSQUARE,STATE,COUNTRY,BAND,MODE}]
lotw_tool.py: error: Error: either login/password/logcall or adifile required

