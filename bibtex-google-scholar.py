#!/usr/bin/env python
# coding: utf-8

# In[1]:


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


# In[2]:


def get_bib_text_to_change(bib_text, target_bib_el):
    bib_text=[x for x in bib_text.split("@") if not re.match("\d+",x) if x!=""]
    bib_text_to_change=[x for x in bib_text if x.startswith(tuple(target_bib_el))]
    if bib_text_to_change==[]:
        return print(f"WARNING: none of {target_bib_el} in bib file! Retry again adding the needed bib tags.")
    bib_text_untouched_els=[ x for x in bib_text if not x.startswith(tuple(target_bib_el))]

    titles_to_change=[re.split("title\s*=\s*{", x)[1].split("}")[0].replace("\n"," ") for x in bib_text_to_change if x!=""]
    authors_to_change=[re.split("author\s*=\s*{", x)[1].split("}")[0].replace("{","").replace("\&",",").replace("\\","").replace("\n"," ") for x in bib_text_to_change if x!=""]
    type_el_to_change=[x.split("@")[0].split("{")[1].split(",")[0].strip().replace("\n"," ") for x in bib_text_to_change if x!=""] #[x.split("@")[0].split("{")[-1].replace("\n","") for x in bib_text_to_change]
    
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
            cit= cit_new.split("{")[0] + "{" + type_el_to_change[i] + "," + ",".join(cit_new.split(",")[1:])
        elif len(type_el_to_change)==0:
            cit= cit_new
        google_formatted_cits[q]=cit
        driver.get(google_scholar_base)
        time.sleep(3)
        
    return google_formatted_cits

def save_results(google_formatted_cits, bib_path, doc_name="", bib_text_untouched_els=[]):
     #save these cits to new .bib file
    results= "\n".join(google_formatted_cits.values())
    if doc_name!="":
        doc_name+="_"
        
    os.makedirs("./results/",exist_ok=True)
    with open("./results/"+f"{doc_name}"+bib_path.split("\\")[-1].replace(".txt",".bib"),"w", encoding="utf-8") as file:
        if len(bib_text_untouched_els)>0: #if targetting an old bib tex file
            final_file= "\n@".join([results,"\n@".join(bib_text_untouched_els)])  #modified entris + untouched ones (e.g. @online, @misc, ...)
        elif len(bib_text_untouched_els)==0:#if targetting a txt file (no old text to retain, it is only a list)
            final_file=results
        file.write(final_file)
    print("File succesfully saved in: ./results/"+ f"{doc_name}_"+bib_path.split("\\")[-1].replace(".txt",".bib"))


# In[21]:

if __name__=="__main__":
    try:
        timeout_val=100000 # for WebDriverWait (circa 1 day)
        session_type=input("Where are your files? [local|overleaf|research rabbit]: ")
        #open selenium, log to overleaf, find the .bib file, get the file
        if session_type.lower().strip()=="overleaf":
            #login inp
            email= input("Overleaf email: ") #"f.dicursi@studenti.unipi.it"
            password= getpass.getpass("Overleaf password: ")

            #search for document
            doc_name= input("Overleaf project name(s separated by comma):  ") #"Research Proposal (CS) (BACKUP)" 
            doc_name_list=[x.strip() for x in doc_name.split(",")]

            print("\nWARNING: the .bib file must be in the root directory of the Overleaf project in order to work.")
            print("\tBefore proceeding, make sure that the .bib on Overleaf is in the correct location.\n")
            bib_path= input("Bib file name(s separated by  comma) on Overleaf, .bib included.\n If the bib name is the same in all projects, just insert that name: ")#"Bibliography.bib" #input
            bib_path_list=[x.strip() for x in bib_path.split(",")]
            #if bibs shorter then doc names, make the bibs longer
            if len(doc_name_list)>1 and len(bib_path_list)==1:
                print(f"\nLength of project names list ({len(doc_name_list)}) does not match with the bibs one {len(bib_path_list)}, assuming the same bib name for all projects.")
                bib_path_list=[x for x in [str(bib_path_list[0]+"#~#~#")*len(doc_name_list)][0].split("#~#~#") if x!=""]
                print("\nNew bib list: ", bib_path_list)
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

            for doc_name, bib_path in zip(doc_name_list, bib_path_list):
                print("\n> FILE ", str(doc_name_list.index(doc_name)+1)+ " of "+str(len(doc_name_list))+": "+doc_name )
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
                files_dict={x.text: x for x in main.find_element(By.TAG_NAME,"aside").find_element(By.TAG_NAME,"file-tree-root")                            .find_element(By.CLASS_NAME, 'file-tree-inner').find_elements(By.TAG_NAME,"*")
                        }

                #select target file
                try:
                    target_bib_file=files_dict[bib_path]
                    target_bib_file.click()
                except KeyError:
                    print("\n.bib not found, try a valid path")
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
                titles_to_change, authors_to_change, type_el_to_change,            bib_text_to_change, bib_text_untouched_els = get_bib_text_to_change(bib_text, target_bib_el)
                print(f"\n{len(titles_to_change)} titles to change: ", titles_to_change)

                #go to scholar
                google_formatted_cits= google_scholar_search(driver, titles_to_change, authors_to_change, action, type_el_to_change)
                #save results
                save_results(google_formatted_cits, bib_path, doc_name, bib_text_untouched_els)

                if len(doc_name_list)>1: #repeat the process for other files
                    if doc_name_list.index(doc_name) == len(doc_name_list)-1: #close browser after last doc
                        print("\nClosing the program")
                        driver.close()
                    else:
                        driver.get("https://www.overleaf.com")
                        time.sleep(3)
                else:
                    driver.close()


        elif session_type=="research rabbit":
            #retrieve a list from a ResearchRabbit collection
            rabbit_email=input("Research Rabbit email: ")
            rabbit_pass=input("Research Rabbit password: ")
            rabbit_collections=input("Research Rabbit collection name(s separated by comma): ")
            rabbit_collections= [x.strip() for x in rabbit_collections.split(",")]
            rabbit_url="https://researchrabbitapp.com/"

            print("""\n Choose if you want to save all collections in the same file:
            -'y': only one file will be created.
            -'n': a file for each collection will be created.""")
            rabbit_merge_outputs=input("Do you want to save all collections in the same file? [y|n]:  ")

            options= webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            driver= webdriver.Chrome(options=options)
            #init action
            action= ActionChains(driver)
            #go to Rabbit
            driver.get(rabbit_url)
            time.sleep(4)
            rabbit_log_cont=driver.find_element(By.CLASS_NAME, "login-form")
            mail_inp, pass_inp=rabbit_log_cont.find_elements(By.TAG_NAME,"input")
            mail_inp.send_keys(rabbit_email)
            pass_inp.send_keys(rabbit_pass)

            pass_inp.send_keys(Keys.TAB)
            pass_inp.send_keys(Keys.ENTER)

            WebDriverWait(driver, timeout=timeout_val).until(lambda d: driver.find_elements(By.XPATH,"//div[@class='collection-button']"))

            collections_= [x for x in driver.find_elements(By.XPATH,"//div[@class='collection-button' or (contains(@class,'is-selected') and contains(@class,'collection-button'))]")
                        if x.text.split("\n")[0].strip() in rabbit_collections
                        ]
            #if y, save all collections in the same file
            if rabbit_merge_outputs=="y":
                # for each collection and each item get authors and paper name
                titles_results=[]
                authors_results=[]
                for collection in collections_:
                    collection.click()
                    paper_list=WebDriverWait(driver, timeout=timeout_val).until(lambda d:driver.find_element(By.XPATH,"//ul[@class='collection-items']"))
                    list_items=WebDriverWait(driver, timeout=timeout_val).until(lambda d:paper_list.find_elements(By.TAG_NAME,"li"))
                    for item in list_items:
                        #expand authors if expansion button
                        try:
                            item.find_element(By.CLASS_NAME,"toggle-expansion-button").click()
                        except:
                            print("no author expansion button")
                        #get authors
                        authors= ",".join([x.text for x in item.find_elements(By.CLASS_NAME,"author")])
                        title= item.find_element(By.CLASS_NAME,"title").text
                        titles_results.append(title)
                        authors_results.append(authors)
                        time.sleep(1)
                    time.sleep(1)

                #go to scholar
                google_formatted_cits= google_scholar_search(driver, titles_results, authors_results, action)
                #save to file
                if len(rabbit_collections)>1:
                    rabbit_output_name= f"{rabbit_collections[0]} and {len(rabbit_collections)-1} others.bib"
                elif len(rabbit_collections)==1:
                    rabbit_output_name= f"{rabbit_collections[0]}.bib"
                save_results(google_formatted_cits, rabbit_output_name)
                driver.close()
            elif rabbit_merge_outputs=="n":
                # for each collection and each item get authors and paper name
                titles_results_per_file=[]
                authors_results_per_file=[]
                for collection in collections_:
                    titles_results=[]
                    authors_results=[]

                    collection.click()
                    paper_list=WebDriverWait(driver, timeout=timeout_val).until(lambda d:driver.find_element(By.XPATH,"//ul[@class='collection-items']"))
                    list_items=WebDriverWait(driver, timeout=timeout_val).until(lambda d:paper_list.find_elements(By.TAG_NAME,"li"))
                    for item in list_items:
                        #expand authors if expansion button
                        try:
                            item.find_element(By.CLASS_NAME,"toggle-expansion-button").click()
                        except:
                            print("no author expansion button")
                        #get authors
                        authors= ",".join([x.text for x in item.find_elements(By.CLASS_NAME,"author")])
                        title= item.find_element(By.CLASS_NAME,"title").text
                        titles_results.append(title)
                        authors_results.append(authors)
                        time.sleep(1)
                    titles_results_per_file.append(titles_results)
                    authors_results_per_file.append(authors_results)
                    time.sleep(1)

                #search and save for each file
                for i,collection in enumerate(rabbit_collections):
                    print("Collection number " + str(i+1)+ ": "+collection)
                    target_titles= titles_results_per_file[i]
                    target_authors= authors_results_per_file[i]
                    #go to scholar
                    google_formatted_cits= google_scholar_search(driver, target_titles, target_authors, action)
                    #save to file
                    rabbit_output_name= collection+".bib"
                    save_results(google_formatted_cits, rabbit_output_name)
                driver.close()


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
                bib_path_list=input(f"""Insert the name of the {local_session_type} file(s separated by comma) and\n remember, it must be in 'local input files' folder and must incluide '.bib' at the end: """)
                bib_path_list=[x.strip() for x in bib_path_list.split(",") if x!=""]
                #consider only scientific plublications
                target_bib_el=["article","phdthesis","inproceedings"] #find for other common elements in scientific citation
                change_bib_els=input( "["+ ",".join(target_bib_el)+ "] <== These are the default tags that will be extracted from the .bib file,\n do you wish to add new ones? [y|n]")
                if change_bib_els.strip()=="y":
                    new_bib_els=input("Insert a list of tags separated only by comma \nas in 'inbook,incollection,book,...': ")
                    target_bib_el.extend([x.lower().strip() for x in new_bib_els.split(",")])
                    print("\nTarget bib elements updated: ", target_bib_el)
                #init driver
                options= webdriver.ChromeOptions()
                options.add_argument("--start-maximized")
                driver= webdriver.Chrome(options=options)
                #init action
                action= ActionChains(driver)
                for bib_path in bib_path_list:
                    print("\n> FILE ", str(bib_path_list.index(bib_path)+1)+ " of "+str(len(bib_path_list))+": "+bib_path )

                    bib_text=""
                    with open("./local input files/"+bib_path.strip(), "r", encoding='utf-8') as oldfile:
                        bib_text=oldfile.read()
                    #create sub elements for the scholar queries
                    titles_to_change, authors_to_change, type_el_to_change,                bib_text_to_change, bib_text_untouched_els = get_bib_text_to_change(bib_text, target_bib_el)
                    print(f"\n{len(titles_to_change)} titles to change: ", titles_to_change)



                    #go to scholar
                    google_formatted_cits= google_scholar_search(driver, titles_to_change, authors_to_change, action, type_el_to_change)
                    #save results
                    save_results(google_formatted_cits, bib_path, "", bib_text_untouched_els) #no doc name (need to make this explicit due to arg pos (not last))

                    if len(bib_path_list)>1: #repeat the process for other files
                        if bib_path_list.index(bib_path) == len(bib_path_list)-1: #close browser after last doc
                            print("\nClosing the program")
                            driver.close()
                        else:
                            continue
                    else:
                        driver.close()


            elif local_session_type=="txt":
                #bib_path is actually txt_path in this
                txt_path_list=input(f"""\nInsert the name of the {local_session_type} file(s separeted by comma)\nand remember, it must be in 'local input files' folder and must include '.txt'": """)
                txt_path_list= [x.strip() for x in txt_path_list.split(",") if x!=""]
                #init driver
                options= webdriver.ChromeOptions()
                options.add_argument("--start-maximized")
                driver= webdriver.Chrome(options=options)
                #init action
                action= ActionChains(driver)

                for txt_path in txt_path_list:
                    print("\n> FILE ", str(txt_path_list.index(txt_path)+1)+ " of "+str(len(txt_path_list))+": "+txt_path )

                    text_=""
                    with open("./local input files/"+ txt_path.strip(), "r", encoding='utf-8') as oldfile:
                        text_= oldfile.read()

                    titles_to_collect=[x.split(";")[0] for x in text_.split("\n") if x!=""]
                    authors_to_collect=[",".join(x.split(";")[1:]).replace("\\n","") for x in text_.split("\n") if x!=""]
                    print(f"\n{len(titles_to_collect)} titles to collect: ", titles_to_collect)
                    #go to scholar
                    google_formatted_cits= google_scholar_search(driver, titles_to_collect, authors_to_collect, action)
                    #save to file
                    save_results(google_formatted_cits, txt_path)

                    if len(txt_path_list)>1: #repeat the process for other files
                        if txt_path_list.index(txt_path) == len(txt_path_list)-1: #close browser after last doc
                            print("\nClosing the program")
                            driver.close()
                        else:
                            continue
                    elif len(txt_path_list)==1:
                        driver.close()




        else:
            print("\nWrong input, closing the program. Try again with [local|overleaf|research rabbit]")
            time.sleep(2)
    except Exception as e:
        print("\nERROR\n",e)
        print("\nSomething went wrong. Check the given answers cause some of them may be wrong.")
        print("\nClosing the program.")
        driver.close()






