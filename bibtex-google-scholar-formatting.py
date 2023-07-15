#!/usr/bin/env python
# coding: utf-8

# In[144]:


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


# In[ ]:





# In[147]:

if __name__=="__main__":
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
        target_bib_el=["article","phdthesis"] #find for other common elements in scientific citation
        change_bib_els=input( "["+ ",".join(target_bib_el)+ "] <== These are the default tags that will be extracted from the .bib file,\n do you wish to add new ones? [y/n]")
        if change_bib_els.strip()=="y":
            new_bib_els=input("Insert a list of tags separated only by comma \n as in 'inbook,incollection,book,...': ")
            target_bib_el.extend([x.lower().strip() for x in new_bib_els.split(",")])
            print("\nTarget bib elements updated: ", target_bib_el)
        
        google_scholar_base= "https://scholar.google.com"
        timeout_val=100000
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
        bib_text= WebDriverWait(driver, timeout=timeout_val).until(lambda d: driver.find_element(By.TAG_NAME, "source-editor").text)
        bib_text=[x for x in bib_text.split("@") if not re.match("\d+",x)]
        bib_text_to_change=[x for x in bib_text if x.startswith(tuple(target_bib_el))]
        bib_text_untouched_els=[ x for x in bib_text if not x.startswith(tuple(target_bib_el))]

        titles_to_change=[x.split("title = {")[1].split("}")[0] for x in bib_text_to_change]
        authors_to_change=[x.split("author = {")[1].split("}")[0].replace("{","").replace("\\","") for x in bib_text_to_change]
        type_el_to_change=[x.split("@")[0].split("{")[-1].replace("\n","") for x in bib_text_to_change]

        #find the google scolar cit
        time.sleep(2)
        google_scholar_base= "https://scholar.google.com"
        driver.get(google_scholar_base)

        search_queries=[x + ","+ y for x,y in zip(titles_to_change,authors_to_change)]
        google_formatted_cits={x:"" for x in search_queries}
        #collect citations (searching them on google scholar)
        for i,q in enumerate(tqdm(search_queries)):
            time.sleep(3)
            search_scholar=driver.find_element(By.CLASS_NAME,"gs_in_txt.gs_in_ac")
            print(search_scholar)
            #search_scholar.send_keys(q)
            #search_scholar.send_keys(Keys.ENTER)
            action.send_keys_to_element(search_scholar, q)
            action.send_keys_to_element(search_scholar, Keys.ENTER)
            try:
                action.perform()
                action.reset_actions()
            except:
                #it sometimes throw expetion for missing element but it actually performs the action
                #but if effectively the page is still the home page, then skip to next iteration
                print("error in search")
                if driver.current_url==google_scholar_base:
                    continue
            time.sleep(3)
            #captcha error (wait to solve the eventual captcha)
            query_results= WebDriverWait(driver, timeout=timeout_val).until(lambda d:driver.find_elements(By.CLASS_NAME,"gs_r.gs_or.gs_scl"))
            #get search results
            #query_results=driver.find_elements(By.CLASS_NAME,"gs_r.gs_or.gs_scl")
            #get citation cell
            citation_btn=query_results[0].find_element(By.XPATH, ".//a[@aria-controls='gs_cit']")
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
            #use old bib var
            cit= cit_new.split("{")[0] + "{" + type_el_to_change[i] + ",".join(cit_new.split(",")[1:])
            google_formatted_cits[q]=cit
            driver.get(google_scholar_base)
            time.sleep(3)


        #save these cits to new .bib file
        results= "\n".join(google_formatted_cits.values())
        os.makedirs("./results/",exist_ok=True)
        with open("./results/"+bib_path.split("\\")[-1],"w") as file:
            final_file= "\n@".join([results,"\n@".join(bib_text_untouched_els)])  #modified entris + untouched ones (e.g. @online, @misc, ...)
            file.write(final_file)
        print("File succesfully saved in: ./results/"+bib_path.split("\\")[-1])
        driver.close()
    elif session_type=="local":
        print("Coming soon... Closing the program.")
        time.sleep(2)

    else:
        print("Wrong input, closing the program. Try again with [local|overleaf]")
        time.sleep(2)


    # In[ ]:


    #Research Proposal (CS) (BACKUP)

