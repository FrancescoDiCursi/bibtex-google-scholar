# bibtex-google-scholar-formatting


You can either:

- Take your hill formatted .bib file from Overleaf (personalizing the bibTeX tags you need
- Take a local file, either a:
  + .bib file (as in the overleaf case)
  + .txt file: a list on whose each lines contains the title along with the authors in the following syntax:

   ```
   title1;author1.1;author1.2;...
   
   title2;author2.1;...

   ...
   ```
- Search and retrieve the correct bibTeX citations from Google Scholar.


______
:exclamation: REQUIREMENTS

In order to run the script you need to install the following libraries:
 - selenium==4.10.0
 - pywin32==228
 - tqdm==4.65.0
   
You will also need the correct ChromeDriver according to your Chrome version, [see the tutorial](https://sites.google.com/a/chromium.org/chromedriver/getting-started) (Getting started > Setup)

______
:question: HOW TO USE IT:

Before proceeding, if you want to use a local file, make sure that the file that you need to format is in the "local input files" folder.

Download the zip and extract the folder.

Open the terminal in that folder and, once you have installed all the needed libraries (along with the ChromeDriver), just run the following command:  `python bibtex-google-scholar-formatting.py`

Follow the questions according to your need and be carefull to insert the correct answers, otherwise the script will crash.
______
⚠️ REMIND

Services hate automation, also the ethic one. <sub>(When it is done by others of course 😏)</sub>

So if you have a really long bibliography then you should stay close to the PC, doing CAPTCHAs when needed (the longest the saddest). 

Despite this, don't worry about time: the script is conceived to wait (up to 1 day circa) in points in which CAPTCHAs appear and to perform a bit slowler than humans (in order not to be blocked).

Given this, if you need an instant
aneous formatter, good luck in your search. 

