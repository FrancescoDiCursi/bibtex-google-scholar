![read me header](https://github.com/FrancescoDiCursi/bibtex-google-scholar/blob/main/read%20me%20header.png)
# bibtex-google-scholar

⚙️ **DESCRIPTION**

### INPUT
- Take your hill formatted **.bib file(s) from Overleaf** choosing the bibTeX entries you need
- or take titles and authors from **Research Rabbit collections**
- or take **local file(s)**, either a:
  + .bib file(s) (as in the overleaf case)
  + .txt file(s): a list where each line contains the title along with the authors in the following syntax:

   ```
   title1;author1.1;author1.2;...
   title2;author2.1;...
   ...
   ```
### OUTPUT
- It returns a new .bib file with correct citations and also with old bib references in case of a .bib input. 

### ESTIMATED TIME
- ± 2 citations per minute.
______
⚠️ **REMIND**
- In the case of a .bib file as input, the entries must have both the title and the author fields.

- The old variable names for each entry of the .bib file will be retained meaning that, when replacing the .bib file in Overleaf, you will not have to change your references!

- Services hate automation, also the ethic one. <sub>(When it is done by others of course 😏)</sub>

So <ins>**if you have a really long bibliography then you should stay close to the PC, doing CAPTCHAs when needed**</ins> (usually 2 per session but it may vary for long files). 

Despite this, **don't worry about time**: the script is conceived to wait (up to 1 day circa) in points in which CAPTCHAs appear and to perform a bit slowler than humans (in order not to be blocked).

Given this, if you need an instantaneous formatter, good luck in your search and contact me if you find it 😎 
______
:exclamation: **REQUIREMENTS**

In order to run the script you need to install the following libraries:
 - selenium==4.10.0
 - pywin32==228
 - tqdm==4.65.0
   
You will also need the correct ChromeDriver according to your Chrome version, [see the tutorial](https://sites.google.com/a/chromium.org/chromedriver/getting-started) (Getting started > Setup)

______
:question: **HOW TO USE IT**

Download the zip and extract the folder.

Before proceeding, if you want to use a local file, make sure that the file that you need to format is in the "local input files" folder.

Open the terminal in that folder and, once you have installed all the needed libraries (along with the ChromeDriver), just run the following command:  `python bibtex-google-scholar.py`

Answer to the questions according to your need and be carefull to insert the correct answers, otherwise the script will crash.

______

# Logic diagram
Legend:
- NORMAL nodes = questions
- CIRCULAR node = process
- RHOMBUS node= manual process
- SQUARE node = file
- LINKS = answers
- DASHED LINKS = possibility

![Logic diagram](https://github.com/FrancescoDiCursi/bibtex-google-scholar/blob/main/mermaid-diagram-2023-07-23-172914.svg)
