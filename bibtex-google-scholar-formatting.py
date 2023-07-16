#!/usr/bin/env python
# coding: utf-8
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait


import time
import re
import os
from tqdm import tqdm

import getpass
from collections import Counter

import win32clipboard


# In[21]:


def get_bib_text_to_change(bib_text, target_bib_el):
    bib_text=[x for x in bib_text.split("@") if not re.match("\d+",x)]
    bib_text_to_change=[x for x in bib_text if x.startswith(tuple(target_bib_el))]
    if bib_text_to_change==[]:
        return print(f"WARNING: none of {target_bib_el} in bib file! Retry again adding the needed bib tags.")
    bib_text_untouched_els=[ x for x in bib_text if not x.startswith(tuple(target_bib_el))]

    titles_to_change=[x.split("title = {")[1].split("}")[0].replace("\n"," ") for x in bib_text_to_change]
    authors_to_change=[x.split("author = {")[1].split("}")[0].replace("{","").replace("\&",",").replace("\\","").replace("\n"," ") for x in bib_text_to_change]
    type_el_to_change=[x.split("@")[0].split("{")[1].split(",")[0].strip().replace("\n"," ") for x in bib_text_to_change] #[x.split("@")[0].split("{")[-1].replace("\n","") for x in bib_text_to_change]
    
    return titles_to_change, authors_to_change, type_el_to_change, bib_text_to_change, bib_text_untouched_els

#check if other args are needed
def google_scholar_search(driver, titles_to_change, authors_to_change, action, type_el_to_change=[]):
    time.sleep(2)
    google_scholar_base= "https://scholar.google.com"
    driver.get(google_scholar_base)

    search_queries=[x + ","+ y for x,y in zip(titles_to_change,authors_to_change)]
    #print("QUERIES", search_queries)
    google_formatted_cits={x:"" for x in search_queries}
    #collect citations (searching them on google scholar)
    for i,q in enumerate(tqdm(search_queries)):
        time.sleep(2)
        search_scholar=driver.find_element(By.CLASS_NAME,"gs_in_txt.gs_in_ac")
        #print(search_scholar)
        #search_scholar.send_keys(q)
        #search_scholar.send_keys(Keys.ENTER)
        
        action.send_keys_to_element(search_scholar, q)
        action.pause(5) #need to wait for particularly long queries before proceeding, otherwise stale element execption
        action.send_keys_to_element(search_scholar, Keys.ENTER)
        try:
            action.perform()
            action.reset_actions()
        except Exception as e:
            #it sometimes throw expetion for missing element but it actually performs the action
            #but if effectively the page is still the home page, then skip to next iteration
            action.reset_actions()
            print(f"error in search query '{q}'")
            if driver.current_url!=google_scholar_base:
                print(f"BUT DONT WORRY, if the browser got to the search page there is no problem.")
            elif driver.current_url==google_scholar_base:
                print("Error in searching the title, skip to next.")
                driver.get(google_scholar_base)
                time.sleep(3)
                continue
                
        time.sleep(1)
        #captcha error (wait to solve the eventual captcha)
        #wait for side menu to populate
        WebDriverWait(driver, timeout=timeout_val).until(lambda d:driver.find_elements(By.CLASS_NAME,"gs_bdy_sb_sec"))
        #get reuslts
        query_results= driver.find_elements(By.CLASS_NAME,"gs_r.gs_or.gs_scl")
        #get citation cell
        try:
            citation_btn=query_results[0].find_element(By.XPATH, ".//a[@aria-controls='gs_cit']")
        except:
            print(f"no results for '{q}', skip to next query.")
            driver.get(google_scholar_base)
            time.sleep(3)
            continue
        time.sleep(2)
        citation_btn.click()
        time.sleep(3)
        #get bibtex link (the first one)
        #target_res=query_results[0].find_element(By.CLASS_NAME, "gs_fl").find_elements(By.TAG_NAME,"a")
        #click on link
        cit_link= WebDriverWait(driver, timeout=timeout_val)                  .until( lambda d: driver.find_element(By.ID,"gs_cit").find_element(By.XPATH,"//a[text()='BibTeX']") )
        driver.find_element(By.ID,"gs_cit").find_element(By.XPATH,"//a[text()='BibTeX']").click()
        time.sleep(3)
        #in the new window, take the citation
        cit_new= WebDriverWait(driver, timeout=timeout_val).until(lambda d:driver.find_element(By.TAG_NAME, "pre").text)
        if len(type_el_to_change)>0:
            #use old bib var
            cit= cit_new.split("{")[0] + "{" + type_el_to_change[i] + ",".join(cit_new.split(",")[1:])
        elif len(type_el_to_change)==0:
            cit= cit_new
        google_formatted_cits[q]=cit
        driver.get(google_scholar_base)
        time.sleep(3)
        
    return google_formatted_cits

def save_results(google_formatted_cits, bib_path, bib_text_untouched_els=[]):
     #save these cits to new .bib file
    results= "\n".join(google_formatted_cits.values())
    os.makedirs("./results/",exist_ok=True)
    with open("./results/"+bib_path.split("\\")[-1].replace(".txt",".bib"),"w", encoding="utf-8") as file:
        if len(bib_text_untouched_els)>0: #if targetting an old bib tex file
            final_file= "\n@".join([results,"\n@".join(bib_text_untouched_els)])  #modified entris + untouched ones (e.g. @online, @misc, ...)
        elif len(bib_text_untouched_els)==0:#if targetting a txt file (no old text to retain, it is only a list)
            final_file=results
        file.write(final_file)
    print("File succesfully saved in: ./results/"+bib_path.split("\\")[-1].replace(".txt",".bib"))
    driver.close()


# In[22]:

if  __name__=="__main__":
    timeout_val=100000 # for WebDriverWait (circa 1 day)
    session_type=input("Do you want to use a local .bib or to take it from overleaf? [local|overleaf]: ")
    #open selenium, log to overleaf, find the .bib file, get the file
    if session_type.lower().strip()=="overleaf":
        #login inp
        email= input("Overleaf email: ") #"f.dicursi@studenti.unipi.it"
        password= getpass.getpass("Overleaf password: ")

        #search for document
        doc_name= input("Overleaf project name: ") #"Research Proposal (CS) (BACKUP)" 

        print("\nWARNING: the .bib file must be in the root directory of the Overleaf project in order to work.")
        print("\tBefore proceeding, make sure that the .bib on Overleaf is in the correct location.\n")
        bib_path= input("Bib file name on Overleaf (.bib included): ")#"Bibliography.bib" #input
        print("\n")
        #take the text from .bib
        #consider only scientific plublications
        target_bib_el=["article","phdthesis","inproceedings"] #find for other common elements in scientific citation
        change_bib_els=input( "["+ ",".join(target_bib_el)+ "] <== These are the default tags that will be extracted from the .bib file,\n do you wish to add new ones? [y|n]")
        if change_bib_els.strip()=="y":
            new_bib_els=input("Insert a list of tags separated only by comma \n as in 'inbook,incollection,book,...': ")
            target_bib_el.extend([x.lower().strip() for x in new_bib_els.split(",")])
            print("\nTarget bib elements updated: ", target_bib_el)
        
        google_scholar_base= "https://scholar.google.com"
        #thorugh selenium go to google scholar
        #for of link is https://scholar.google.com/scholar?q={name of the pubblication with + instead of spaces}
        #e.g. https://scholar.google.com/scholar?q=A+Network+View+of+Social+Media+Platform+History:+Social+Structure,+Dynamics+and+Content+on+YouTube

        #select the element > click on cite > bibtex > select the text and copy it to a new .bib file 
        #REPEAT FOR ALL ORIGINAL BIB ELS

        #selenium els
        email_id="email"
        pass_id="password"
        
        options= webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver= webdriver.Chrome(options=options)
        driver.get("https://www.overleaf.com/login")
        time.sleep(4)

        #-log_in
        email_inp=driver.find_element(By.ID,email_id)
        email_inp.send_keys(email)
        pass_inp=driver.find_element(By.ID,pass_id)
        pass_inp.send_keys(password)
        action=ActionChains(driver)
        action.send_keys(Keys.ENTER)
        action.perform()
        action.reset_actions()

        #wait for captcha
        WebDriverWait(driver,timeout=timeout_val).until(lambda d:driver.find_element(By.CLASS_NAME, "project-dash-table"))
        #-find file
        #show all projects
        action.scroll(0,0,0,10000)
        action.perform()
        action.reset_actions()
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[@aria-label='Show 1 more projects']").click()
        #get files refs
        project_table=driver.find_element(By.CLASS_NAME, "project-dash-table")
        project_names=[x.text for x in project_table.find_elements(By.CLASS_NAME,"dash-cell-name")[1:]] #TABLE WITH NO HEADER
        project_els=[x for x in project_table.find_elements(By.CLASS_NAME,"dash-cell-name")[1:]]
        projects_dict={x:y for x,y in zip(project_names, project_els)}
        #get file
        driver.get(projects_dict[doc_name].find_element(By.TAG_NAME,"a").get_attribute("href"))
        time.sleep(4)


        #go to .bib
        main=WebDriverWait(driver, timeout=timeout_val).until(lambda d: driver.find_element(By.ID,"ide-body"))
        main.click()
        files_dict={x.text: x for x in main.find_element(By.TAG_NAME,"aside").find_element(By.TAG_NAME,"file-tree-root")                    .find_element(By.CLASS_NAME, 'file-tree-inner').find_elements(By.TAG_NAME,"*")
                }

        #select target file
        try:
            target_bib_file=files_dict[bib_path]
            target_bib_file.click()
        except KeyError:
            print(".bib not found, try a valid path")
            bib_path2=input("Insert a valid path or stop the program")
            try:
                target_bib_file=files_dict[bib_path2]
                target_bib_file.click()
                bib_path=bib_path2
            except KeyError:
                print("file not found")

        #find bib text
        bib_text_wait= WebDriverWait(driver, timeout=timeout_val).until(lambda d: driver.find_element(By.TAG_NAME, "source-editor"))
        time.sleep(1)
        #action.scroll(0,0,0,100000)
        #select all text (raw txt of the editor is only that is displayed in the view)
        action.key_down(Keys.CONTROL)
        action.send_keys("a")
        action.key_up(Keys.CONTROL)
        action.perform()
        action.reset_actions()
        time.sleep(1)
        #COPY TEXT
        action.key_down(Keys.CONTROL)
        action.send_keys("c")
        action.key_up(Keys.CONTROL)
        action.perform()
        action.reset_actions()
        time.sleep(1)
        # GET COPIED TEXT FROM CLIPBOARD
        win32clipboard.OpenClipboard()
        bib_text= win32clipboard.GetClipboardData()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        time.sleep(1)
        #create sub elements for the scholar queries
        titles_to_change, authors_to_change, type_el_to_change,    bib_text_to_change, bib_text_untouched_els = get_bib_text_to_change(bib_text, target_bib_el)
        print(f"\n{len(titles_to_change)} titles to change: ", titles_to_change)
        
        #go to scholar
        google_formatted_cits= google_scholar_search(driver, titles_to_change, authors_to_change, action, type_el_to_change)
        #save results
        save_results(google_formatted_cits, bib_path, bib_text_untouched_els)
        
    elif session_type=="local":
        #create a local input file
        os.makedirs("./local input files", exist_ok=True)
        print("\nWARNING: Local input folder created, insert the files to elaborate in the folder before proceeding!")
        
        print("""\nAs local file, do you want to use:\n
    - bib: a local .bib file\n
    - txt: a .txt with a list of items (with ; as a separator in the line and \\n as line separator) in the form: \n
        'title1;authors1.1;authors1.2;...\n
        title2;authors2.1;authors2.2;...\n
        ...'""")
        
        local_session_type= input("[bib|txt]: ")    
        if local_session_type=="bib":
            bib_path=input(f"""Insert the name of the {local_session_type} file\n(remember, it must be in 'local input files' folder and must incluide '.bib'): """)
            #consider only scientific plublications
            target_bib_el=["article","phdthesis","inproceedings"] #find for other common elements in scientific citation
            change_bib_els=input( "["+ ",".join(target_bib_el)+ "] <== These are the default tags that will be extracted from the .bib file,\n do you wish to add new ones? [y|n]")
            if change_bib_els.strip()=="y":
                new_bib_els=input("Insert a list of tags separated only by comma \n as in 'inbook,incollection,book,...': ")
                target_bib_el.extend([x.lower().strip() for x in new_bib_els.split(",")])
                print("\nTarget bib elements updated: ", target_bib_el)
            
            bib_text=""
            with open("./local input files/"+bib_path.strip(), "r", encoding='utf-8') as oldfile:
                bib_text=oldfile.read()
            #create sub elements for the scholar queries
            titles_to_change, authors_to_change, type_el_to_change,        bib_text_to_change, bib_text_untouched_els = get_bib_text_to_change(bib_text, target_bib_el)
            print(f"\n{len(titles_to_change)} titles to change: ", titles_to_change)
            
            #init driver
            options= webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            driver= webdriver.Chrome(options=options)
            #init action
            action= ActionChains(driver)
            
            #go to scholar
            google_formatted_cits= google_scholar_search(driver, titles_to_change, authors_to_change, action, type_el_to_change)
            #save results
            save_results(google_formatted_cits, bib_path, bib_text_untouched_els)
                
        elif local_session_type=="txt":
            #bib_path is actually txt_path in this
            txt_path=input(f"""\nInsert the name of the {local_session_type} file\n(remember, it must be in 'local input files' folder and must include '.txt'"): """)
            text_=""
            with open("./local input files/"+ txt_path.strip(), "r", encoding='utf-8') as oldfile:
                text_= oldfile.read()
            
            titles_to_collect=[x.split(";")[0] for x in text_.split("\n")]
            authors_to_collect=[",".join(x.split(";")[1:]).replace("\\n","") for x in text_.split("\n")]
            print(f"\n{len(titles_to_collect)} titles to collect: ", titles_to_collect)
        
            #init driver
            options= webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            driver= webdriver.Chrome(options=options)
            #init action
            action= ActionChains(driver)
            #go to scholar
            google_formatted_cits= google_scholar_search(driver, titles_to_collect, authors_to_collect, action)
            #save to file
            save_results(google_formatted_cits, txt_path)

        
    else:
        print("\nWrong input, closing the program. Try again with [local|overleaf]")
        time.sleep(2)
        
