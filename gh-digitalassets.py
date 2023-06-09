#!/usr/bin/env python
# set -e

# echo "Hello gh-digitalassets!"
import argparse
from github import Github
from github import GithubException
import subprocess
import json 
import dotenv
import os
import sys
from InquirerPy import prompt
import base64
import requests as request
import github
from fuzzywuzzy import fuzz



def check_login():
    token = subprocess.run("gh auth token", shell = True, capture_output = True)
    token = token.stdout.decode('ascii').strip()
    dotenv_file = dotenv.find_dotenv('variables.env')
    dotenv.load_dotenv(dotenv_file)
    #print(os.environ["AUTH_TOKEN"])
    if(os.environ['AUTH_TOKEN'] != token):
        token = login()
        os.environ["AUTH_TOKEN"] = token 
        dotenv.set_key(dotenv_file, "AUTH_TOKEN", os.environ["AUTH_TOKEN"])

    return token



def login():
    print('logging in')
    subprocess.run("gh auth login", shell = True)

    token = subprocess.run("gh auth token", shell = True, capture_output = True)

    token = token.stdout.decode('ascii').strip()
    return token




def topic_writing():
    print("Please choose a topic according to the ENS standards. Here are the topics you can choose from:")
    questions = [
        {
        'type': 'list',
        'name': 'topic',
        'message': 'What topic to add?',
        'choices': ["ens-machineLearning", "ens-mathematics", "ens-lifeSciences", "ens-Sports", "ens-others"],
        'filter': lambda val: val.lower()
        },
    ]
    answers = prompt(questions)
    print("Do you want to add more topics?, If yes, please add them coma separated:")
    resp = input().split(',')
    resp.append(answers['topic'])
    return(resp)

def interactiveBuilding():
    metaData = {}
    print("Please provide the asset Name.")
    assetName = str(input())
    metaData["assetName"] = assetName
    print("Please provide a one liner description")
    description = str(input())
    metaData["description"] = description
    topic_inp = topic_writing()
    topics = topic_inp

    var = any(tag in ensTopicList for tag in topics)
    print(var)
    if(not var):
        return("Please provide a topic acoording to the ENS standards", 0)
    else:
        metaData["Topics"] = topics

    print("Please provide the associations(URSL's). If multiple, provide then coma separated")
    associations = input().split(',')
    metaData["Associations"] = associations

    json_object = json.dumps(metaData, indent = 4)
    return(json_object, 1)




def metaDataParser(fileContent):
    parsers = ['assetName', 'description', 'Topics', 'Associations']
    try:
        metaData = json.loads(fileContent or '{}')
    except json.decoder.JSONDecodeError:
        print("Please check the format of your json file")


    remaining = {}
    keys = []
    counter = 0
    topics_bool = True
    for tag in parsers:
        if(tag in metaData):
            if(tag == 'Topics'):
                topics_list = metaData['Topics']
                var = any(tag in ensTopicList for tag in topics_list)
                if(not var):
                    print("Please provide a topic according to the ENS standards.")
                    topics_bool = False
            if(tag == 'Associations'):
                if(metaData[tag]):
                    if(type(metaData[tag]) != list):
                        lst = [metaData[tag]]
                        metaData[tag] = lst

            if(metaData[tag]):
                pass 
                counter += 1
            else:
                print("There is no value provided for the key {}".format(tag))
                remaining[tag] = ""
        else:
            print("{} key not present in the file".format(tag))
            keys.append(tag)
    if(counter == 4 and topics_bool == True):
        return(metaData, 1)

    if(len(remaining) > 0 or len(keys) > 0 or topics_bool == False):
        print("Do you want to interactively add the missing keys or values?: Y or N")
        resp = input()
        if(resp == 'Y'):
            if(len(remaining) > 0):
                for tag in remaining:
                    if(tag == 'Associations'):
                        print("Please provide the associations(URL's). If multiple, provide then coma separated")
                        associations = input().split(',')
                        metaData["Associations"] = associations
                    else:
                        print("Please provide the value of the {}".format(tag))
                        resp_tag = input()
                        metaData[tag] = resp_tag
            if(len(keys) > 0):
                print("Please provide the value for the following keys")
                for tag in keys:
                    if(tag == 'Topics'):
                        print("Provide the value of the tag {}".format(tag))
                        metaData['Topics'] = []
                        topic_inp = topic_writing()
                        
                        for top in range(len(topic_inp)):
                            metaData['Topics'].append(topic_inp[top])
                    elif(tag == 'Associations'):
                        print("Please provide the associations(URL's). If multiple, provide then coma separated")
                        associations = input().split(',')
                        metaData["Associations"] = associations
                    else:
                        print("Provide the value of the tag {}".format(tag))
                        resp_tag = input()
                        metaData[tag] = resp_tag
            if(not topics_bool):
                topic_inp = topic_writing()

                for top in range(len(topic_inp)):
                    metaData['Topics'].append(topic_inp[top])

        else:
            return("Please change your json file accordingly and re-upload", 0)

    json_object = json.dumps(metaData, indent = 4)
    return(json_object, 1)







def gitUpload(fileContent, file_content):
    # update
    updateFile = repo.get_contents(file_content , ref = 'main')
    repo.update_file(updateFile.path, "updating the file with some changes", fileContent, updateFile.sha, branch = 'main')

    print("Updated the file in the repo")

def gitUpload_data(fileContent, updateFile):

    file_content = repo.get_contents(updateFile , ref = 'main')
    
    repo.update_file(file_content.path, "updating the file with some changes", fileContent, file_content.sha, branch = 'main')

    print("Updated the file in the repo")



def metadata():
    if(args.filepath):
        file_list = os.listdir(args.filepath)
        if('metadata.json' not in file_list):
            print("No metadata file present. Do you want to interactively build it and upload?")
            resp = input()
            if(resp == 'Y'):
                uploadFile, flag = interactiveBuilding()
                if(not flag):
                    print(uploadFile)
                else:
                    gitUpload(uploadFile, metadata.json)
        else:
            with open(args.filepath + 'metadata.json') as file:
                fileContent = file.read()
            var, flag = metaDataParser(fileContent)

            if(flag == 0):
                return(var)
            else:
                gitUpload(str(var), 'metadata.json')


    else:
        cwd = os.getcwd()
        cwd += '/'
        file_list = os.listdir(cwd)
        if('metadata.json' not in file_list):
            print("No metadata file present. Do you want to interactively build it and upload?")
            resp = input()
            if(resp == 'Y'):
                uploadFile, flag = interactiveBuilding()
                if(not flag):
                    print(uploadFile)
                else:
                    gitUpload(uploadFile, 'metadata.json')
        else:
            with open(cwd + 'metadata.json') as file:
                fileContent = file.read()
            var, flag = metaDataParser(fileContent)

            if(flag == 0):
                return(var)
            else:
                gitUpload(str(var), 'metadata.json')


def data():
    if(args.filepath):
        file_list = os.listdir(args.filepath)
        if(not args.updateFile):
            
            if(len(file_list) == 0):
                return('The folder is empty. Please have your data file in the directory')
            if('.DS_Store' in file_list):
                file_list.remove('.DS_Store')
            if('metadata.json' in file_list):
                file_list.remove('metadata.json')
            
        
            if(len(file_list) != 0):
                for files in range(len(file_list)):
                    with open(args.filepath + file_list[files], 'rb') as file:
                        fileContent = file.read()
                    base64_content = base64.b64encode(fileContent).decode('utf-8')
                    updateFile = file_list[files]
                    gitUpload_data(fileContent, updateFile)
            else:
                return("No data file present")
        else:
            if(args.updateFile not in file_list):
                return("Data file does not exist")
            with open(args.filepath + args.updateFile, 'rb') as file:
                fileContent = file.read()
            base64_content = base64.b64encode(fileContent).decode('utf-8') 
            updateFile = args.updateFile
            gitUpload_data(fileContent, updateFile)

    else:
        cwd = os.getcwd()
        cwd += '/'
        file_list = os.listdir(cwd)
        if(not args.updateFile):
            
            if(len(file_list) == 0):
                return('The folder is empty. Please have your data file in the directory')
            if('.DS_Store' in file_list):
                file_list.remove('.DS_Store')
            if('metadata.json' in file_list):
                file_list.remove('metadata.json')
            
        
            if(len(file_list) != 0):
                for files in range(len(file_list)):
                    with open(cwd + file_list[files], 'rb') as file:
                        fileContent = file.read()
                    base64_content = base64.b64encode(fileContent).decode('utf-8')
                    updateFile = file_list[files]
                    gitUpload_data(fileContent, updateFile)
            else:
                return("No data file present")
        else:
            if(args.updateFile not in file_list):
                return("Data file does not exist")
            with open(cwd + args.updateFile, 'rb') as file:
                fileContent = file.read()
            base64_content = base64.b64encode(fileContent).decode('utf-8') 
            updateFile = args.updateFile
            gitUpload_data(fileContent, updateFile)


##########################################################################
## helper commands for create ##
##########################################################################

### Metadata Checking and interactive building
def metaDataParserCreate(fileContent):
    parsers = ['assetName', 'description', 'topics', 'associations']
    try:
        metaData = json.loads(fileContent)
    except:
        print("Metadata file is empty. You can use interactive building to build the metadata on the fly. Press Y or N")
        userinp = input()
        if userinp == "Y":
            return inetractiveBuildingCreate() 
        else:
            print("Please change the file and come back.")
            sys.exit()

    remaining = {}
    keys = []
    counter = 0
    topics_bool = True
    for tag in parsers:
        if(tag in metaData):
            if(tag == 'topics'):
                topics_list = metaData['topics']
                ensTopicListLower = [x.lower() for x in ensTopicList]
                var = any(tag in ensTopicListLower for tag in topics_list)
                if(not var):
                    print("Please provide a topic according to the ENS standards.")
                    topics_bool = False
            if(metaData[tag]):
                pass 
                counter += 1
            else:
                print("There is no value provided for the key {}".format(tag))
                remaining[tag] = ""
        else:
            print("{} key not present in the file".format(tag))
            keys.append(tag)
    if(counter == 4 and topics_bool == True):
        json_object = json.dumps(metaData, indent = 4)
        return(json_object, 1,metaData["topics"],metaData["description"])

    if(len(remaining) > 0 or len(keys) > 0 or topics_bool == False):
        print("Do you want to interactively add the missing keys or values?: Y or N")
        resp = input()
        if(resp == 'Y'):
            if(len(remaining) > 0):
                for tag in remaining:
                    print("Please provide the value of the {}".format(tag))
                    resp_tag = input()
                    metaData[tag] = resp_tag
            if(len(keys) > 0):
                print("Please provide the value for the following keys")
                for tag in keys:
                    if(tag == "topics"):
                        print("Provide the value of the tag {}".format(tag))
                        metaData["topics"] = []
                        topic_inp = topic_writing()
                        for top in range(len(topic_inp)):
                            metaData['topics'].append(topic_inp[top])
                    else:
                        print("Provide the value of the tag {}".format(tag))
                        resp_tag = input()
                        metaData[tag] = resp_tag
            if(not topics_bool):
                topic_inp = topic_writing()
                for top in range(len(topic_inp)):
                    metaData['topics'].append(topic_inp[top])

        else:
            return("Please change your json file accordingly and re-upload", 0,0,0)

    json_object = json.dumps(metaData, indent = 4)
    return(json_object,1,metaData["topics"],metaData["description"])

##################################################################

## Interactive building if there is no metadata file

def inetractiveBuildingCreate():
    metaData = {}
    print("Please provide the asset Name.")
    assetName = str(input())
    metaData["assetName"] = assetName
    print("Please provide a one liner description")
    description = str(input())
    metaData["description"] = description
    topics = []
    print("Please select a mandatory topic from below")
    questions = [
        {
        'type': 'list',
        'name': 'topic',
        'message': 'What topic to add?',
        'choices': ["ens-machinelearning", "ens-mathematics", "ens-lifeSciences", "ens-Sports", "ens-others"],
        'filter': lambda val: val.lower()
        },
    ]
    answers = prompt(questions)
    # print(answers['topic'])
    topics.append(answers['topic'])

    userinp1 = input("You can also add custom topics to this digital asset. Press Y if you want to add new topics to the repo. Otherwise press N: ")
    if userinp1 == "Y":
        userinp2 = input("Enter the topic names using comma separation: ")
        inputsplit = userinp2.split(",")
        for topic in inputsplit:
            if topic in topics:
                print("This topic "+topic+" is already added")
                continue
            topics.append(topic)
    

    metaData["topics"] = topics

    print("Please provide the associations(URSL's). If multiple, provide by giving space")
    associations = input().split()
    metaData["associations"] = associations

    json_object = json.dumps(metaData, indent = 4)
    return(json_object,1,metaData["topics"],metaData["description"])

def uploadFiles_Directory(filePath,createdRepoName):
    allFiles = os.listdir(filePath)
    print(allFiles)
    for files in allFiles:
        if files == ".git":
            continue
        with open((os.path.join(filePath,files)),'rb') as file:
            fileContent = file.read()
        ## upload file to the repo
        # createdRepoName.create_file("testfile.txt","create file",fileContent,branch="main")

        createdRepoName.create_file(files,"create file",fileContent,branch="main")
    print("All files in the specified directory uploaded")

def createRepo(repoName):
    createdRepo = user.create_repo(repoName)
    return g.get_repo(createdRepo.full_name)

def addTopicsCreation(createdRepoName):
    print("Topics must be added to this digital asset.\n Please choose from one of the assets below.")
    repoobj = g.get_repo(createdRepoName.full_name)
    topics = repoobj.get_topics()
    questions = [
        {
        'type': 'list',
        'name': 'topic',
        'message': 'What topic to add?',
        'choices': ensTopicList,
        'filter': lambda val: val.lower()
        },
    ]
    answers = prompt(questions)
    # print(answers['topic'])
    topics.append(answers['topic'])
    repoobj.replace_topics(topics)
    print("Added the given topics to the repo")
    print("Current topics in this repo are "+str(topics)+"\n")
    userinp = input("You can also add custom topics to this digital asset. Press Y if you want to add new topics to the repo. Otherwise press N: ")
    if userinp == "Y":
        userinp1 = input("Enter the topic names using comma separation: ")
        inputsplit = userinp1.split(",")
        for topic in inputsplit:
            if topic in topics:
                print("This topic "+topic+" is already added")
                continue
            topics.append(topic)
    else:
        print("Terminating")
        sys.exit()
        
    repoobj.replace_topics(topics)
    print("Added the given topics to the repo")
    print("Current topics in this repo are "+str(topics))


def addDesc(createdRepoName):
    userinp = input("please enter a one line description for the digital asset")
    subprocess.run(f"gh repo edit {createdRepoName.full_name} -d \"{userinp}\"",shell=True)

######################################################################################
def download_repo(type,repo,chunkSize = 128):
    repo = getRepo(repo)
    repoName = repo.name
    type = type.lower()
    archive_link = repo.get_archive_link(type+"ball",repo.default_branch)
    response = request.get(archive_link,headers={"Authorization": f"token {token}"})
    if response.status_code == 404:
        print("Failed to fetch download file")
    else :
        print("Downloading %s File",type)
        res = request.get(archive_link , stream = True)
        with open(repoName+"."+type,'wb')  as f:
            for chunk in res.iter_content(chunk_size = chunkSize):
                if chunk:
                    f.write(chunk)
        print("Download Successful")

def download_files(files):
    response = request.get(files.download_url, allow_redirects=True)
    open(files.name,'wb').write(response.content)
    print("Download Successful :" + files.name)

def expandRepo(reponame):
    repo = getRepo(reponame)
    contents = repo.get_contents("")
    expandedContents = []
    while(contents):
        newContent = contents.pop(0)
        if newContent.type == 'dir':
            contents.extend(repo.get_contents(newContent.path))
        else:
            expandedContents.append(newContent)
    return expandedContents

def searchfiles(repoN,filename):
    newRepo = getRepo(repoN)
    contents = newRepo.get_contents("")
    while contents:
        check = True
        newContent = contents.pop(0)
        if newContent.type == 'dir':
            contents.extend(newRepo.get_contents(newContent.path))
        else:
            if newContent.name == filename and newContent.type != 'dir':
                response = request.get(newContent.download_url, allow_redirects=True)
                open(newContent.name,'wb').write(response.content)
                print("Download Successful :" + newContent.name)
            elif fuzz.partial_ratio(newContent.name.lower(), filename.lower()) >= 80 and newContent.type != 'dir':
                response = request.get(newContent.download_url, allow_redirects=True)
                open(newContent.name,'wb').write(response.content)
                print("Download Successful :" + newContent.name)
            else :
                check = False
    if check == True:
        print("No file found")


def getRepo(repoName):
    try:
        repo = g.get_repo(repoName)
        return repo
    except github.BadCredentialsException:
        print("Invalid User Token")
        sys.exit()
    except github.UnknownObjectException:
        print("Repo not found. Please enter a valid repo")
        sys.exit()
    except github.GithubException as e:
        print("Error Occured:", e)
        sys.exit()


############ Search Functions ####################
def get_github_data(topics, input, value):
    st = ""
    first = True
    for t in topics:
        if(first):
            st = st + "topic:" + t
            first = False
        else:
            st = st + "+topic:" + t

    url_2 = "https://api.github.com/search/repositories?q="+st

    data = request.get(url_2)
    data_json  = data.json()
    count = 0
    for i in range(0,len(data_json['items'])):
        count += 1
        owner = data_json['items'][i]['owner']['login']
        name = data_json['items'][i]['name']
        url = data_json['items'][i]['html_url']

      #   file_content = github_read_file(owner,name)
        if(input == 'topics'):
           print(count)
           print('Name: ' + name,'\nLink: ' + url, '\nUploaded By: ' + owner + '\n')

def search(input,value):
   topics = ['ens-asset']
   if input == 'topics':
      custom_topics = value.split(",")
      for v in custom_topics:
         topics.append(v)
   get_github_data(topics, input, value)

def github_read_file_str(username, repository_name, github_token=None):
    headers = {}
    if github_token:
        headers['Authorization'] = f"token {github_token}"
        
    try:
        url = f'https://api.github.com/repos/{username}/{repository_name}/contents/digital-asset-metadata.json'
        r = request.get(url, headers={
    'Authorization': 'Bearer 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',
    'Accept': 'application/vnd.github+json'})
        r.raise_for_status()
        data = r.json()
        file_content = data['content']
        file_content_encoding = data.get('encoding')
        if file_content_encoding == 'base64':
            file_content = base64.b64decode(file_content).decode()
    except:
        file_content = ""
    return file_content

def populate_data(data_json,keyword):
    count = 0
    for i in range(0,len(data_json['items'])):

        owner = data_json['items'][i]['owner']['login']
        name = data_json['items'][i]['name']
        url = data_json['items'][i]['html_url']

        file_content = github_read_file_str(owner,name)
        
        for k in keyword:
            if k.lower() in file_content.lower():
                count += 1
                print(count)
                print('Name: ' + name,'\nLink: ' + url, '\nUploaded By: ' + owner + '\n')

def repo_name_search(name):
   url_2 = "https://api.github.com/search/repositories?q="+name+" in:name topic:ens-asset"

   data = request.get(url_2)
   data_json  = data.json()
   # print('Total Results:',len(data_json['items']),'\n')

   res = []
   count = 0
   for i in range(0,len(data_json['items'])):
         count += 1
         print(count)
         owner = data_json['items'][i]['owner']['login']
         name = data_json['items'][i]['name']
         url = data_json['items'][i]['html_url']

         print('Name: ' + name,'\nLink: ' + url, '\nUploaded By: ' + owner + '\n')



def keyword_search(keywords):
   
   keywords_sp = []
   custom_topics = keywords.split(",")
   for v in custom_topics:
     keywords_sp.append(v)

   url = 'https://api.github.com/search/repositories?q=topic:ens-asset&per_page=100&page=1'

   data = request.get(url,headers={
      'Authorization': 'Bearer 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',
      'Accept': 'application/vnd.github+json'})
   data_json  = data.json()

   headers = data.headers

   populate_data(data_json,keywords_sp)

   if "Link" in headers.keys():
      print('Exists')
      iterate = True
      j = data.headers['Link']
      j = j.split(",")
      url = j[0].split(';')[0].replace('<','').replace('>','')
      
   else:
      iterate = False

   while(iterate):
      data = request.get(url,headers={
         'Authorization': 'Bearer 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',
         'Accept': 'application/vnd.github+json'})
      # data_json  = data.json()
      
      populate_data(data_json,'asset')
      
      if "Link" in data.headers.keys():
         j = data.headers['Link']
         j = j.split(",")
         if('next' in j[1]):
               url = j[1].split(';')[0].replace('<','').replace('>','')
         else:
               iterate = False
      else:
         iterate = False
		 
		 
######################################################################################
def main():
    if args.command == "update-file":
        print("\n####################### Update File ##########################\n")

        if(args.type == 'metadata'):
            imp = metadata()
            if(type(imp) == str):
                print(imp)

        elif(args.type == 'data'):
            imp = data()
            if(type(imp) == str):
                print(imp)
        
        elif(args.type == 'both'):
            imp = metadata()
            imp1 = data()
            if(type(imp) == str):
                print(imp)
            if(type(imp1) == str):
                print(imp1)
        else:
            return("Invalid input")

    ##############################################
    ## Create related code ##
    ##############################################
    if args.command == "createrepo":
        metadataFlag = 0
        # g,user = getAuthToken()
        ## create repo
        if args.empty == "True":
            # createdRepo = user.create_repo(args.reponame)
            createdRepoName = createRepo(args.reponame)
            print("Empty repo created. Upload the digital asset files.")
        else:
            # createdRepo = user.create_repo(args.reponame)
            
            # createdRepoName = g.get_repo(createdRepo.full_name)

            ## read file content
            if args.filepath is None:
                print("Files must be uploaded when creating a non-empty repo")
                print("Files in the current repo are: ")
                print(os.listdir(os.getcwd()))
                userinp = input("Do you want all files in the current directory to be uploaded?  Press Y/N: Pressing N will not create any repo.")
                if userinp == "Y":
                    allFiles = os.listdir(os.getcwd())
                    print(allFiles)
                    for files in allFiles:
                        if "metadata.json" in files:
                            metadataFlag = 1
                            with open((os.path.join(os.getcwd(),files)),'rb') as file:
                                fileContent = file.read()
                                jsonObject, flag, topicsFunc, descFunc = metaDataParserCreate(fileContent)
                                
                                if(flag == 0):
                                    print(jsonObject)
                                    sys.exit()
                                else:
                                    with open(f"{os.getcwd()}/metadata.json","w") as outfile:
                                        outfile.write(jsonObject)



                    if metadataFlag == 0:
                        print("Metadata file not found. It is mandatory for a digital asset.")
                        userinp = input("You can create it interactively. Press Y to create interactively, or press N to create it manually: ")
                        if userinp == "Y":
                            jsonObject,flag,topicsFunc,descFunc = inetractiveBuildingCreate()
                            with open(f"{os.getcwd()}/metadata.json","w") as outfile:
                                outfile.write(jsonObject)
                        else:
                            print("Please come back after creating the metadata.json file")
                            sys.exit()

                    createdRepoName = createRepo(args.reponame)
                    print("Repo created with name "+ str(createdRepoName.full_name))
                    uploadFiles_Directory(os.getcwd(),createdRepoName)
                    ###################
                    ## add the topics to the repo
                    ###################
                    repoobj = g.get_repo(createdRepoName.full_name)
                    print("This is topic func test")
                    print(topicsFunc)
                    repoobj.replace_topics(topicsFunc)
                    ###################
                    ## add the desc to the repo
                    ###################
                    subprocess.run(f"gh repo edit {createdRepoName.full_name} -d {descFunc}",shell=True)
                    # addTopicsCreation(createdRepoName)
                    # addDesc(createdRepoName)
                else:
                    sys.exit()

            elif os.path.isfile(args.filepath):
                createdRepoName = createRepo(args.reponame)
                print("Repo created with name "+ str(createdRepoName.full_name))
                with open(args.filepath, 'rb') as file:
                    fileContent = file.read()
                ## upload file to the repo
                # createdRepoName.create_file("testfile.txt","create file",fileContent,branch="main")

                createdRepoName.create_file(args.filepath.split('\\')[-1],"create file",fileContent,branch="main")
                print("testfile created in the repo" + str(createdRepoName.full_name))
                addTopicsCreation(createdRepoName)
                addDesc(createdRepoName)

            elif os.path.isdir(args.filepath):
                allFiles = os.listdir(args.filepath)
                print(allFiles)
                for files in allFiles:
                    if "metadata.json" in files:
                        metadataFlag = 1
                        with open((os.path.join(args.filepath,files)),'rb') as file:
                            fileContent = file.read()
                            jsonObject, flag, topicsFunc, descFunc = metaDataParserCreate(fileContent)
                            
                            if(flag == 0):
                                print(jsonObject)
                                sys.exit()
                            else:
                                with open(f"{args.filepath}/metadata.json","w") as outfile:
                                    outfile.write(jsonObject)

                if metadataFlag == 0:
                    print("Metadata file not found. It is mandatory for a digital asset.")
                    userinp = input("You can create it interactively. Press Y to create interactively, or press N to create it manually: ")
                    if userinp == "Y":
                        jsonObject,topicsFunc,descFunc = inetractiveBuildingCreate()
                        with open(f"{args.filepath}/metadata.json","w") as outfile:
                            outfile.write(jsonObject)
                    else:
                        print("Please come back after creating the metadata.json file")
                        sys.exit()

                createdRepoName = createRepo(args.reponame)
                print("Repo created with name "+ str(createdRepoName.full_name))
                uploadFiles_Directory(args.filepath,createdRepoName)
                ###################
                ## add the topics to the repo
                ###################
                repoobj = g.get_repo(createdRepoName.full_name)
                repoobj.replace_topics(topicsFunc)
                ###################
                ## add the desc to the repo
                ###################
                subprocess.run(f"gh repo edit {createdRepoName.full_name} -d {descFunc}",shell=True)

                # addTopicsCreation(createdRepoName)
                # addDesc(createdRepoName)
    
    if args.command == "clone":
        print("Cloning a repo")

    elif args.command == "downloadRepo":
        repo = args.repoName
        questions = [
            {
            'type' : 'list',
            'name' : 'format',
            'message' : 'How would you like to download the repo?',
            'choices' : ['Zip','Tar'],
            'filter' : lambda option : option
         }
        ]
        result = prompt(questions)
        if result['format'] == 'Zip':
            type = "zip"
            download_repo(type,repo)
        elif result['format'] == 'Tar':
            type = 'tar'
            download_repo(type,repo)
        else:
            print("Download Failed. Please check the repo name")

    elif args.command == "downloadFile": 
        filename = args.fileName
        repoN = args.repoName
        if(filename):
            searchfiles(repoN,filename)
        else:
            newRepo = getRepo(repoN)
            contents = expandRepo(repoN)
            questions = [
                {
                    'type' : 'list',
                    'name' : 'dFile',
                    'message' : 'Select a file to download',
                    'choices' : [x.name for x in contents],
                    'filter' : lambda option : option
                    }
                ]
            result = prompt(questions)
            for each in contents:
                if result['dFile'] == each.name:
                    download_files(each)

    elif args.command == "listContents":
        newName = args.repoName
        try:
            contents = expandRepo(newName)
            print("File contents of "+ newName)
            for each in contents:
                print(each.path)
        except Exception as ex:
            print("An error Occured. Repo " + ex.data['message'])

     
    elif args.command == "readMetadata":
        repo = getRepo(args.repoName)
        try:
            content = repo.get_contents("metadata.json")
            contentData = content.decoded_content
            data = contentData.decode('utf8').replace("'", '"')
            jsonData = json.loads(data)
            print("******************* Metadata Contents ******************")
            for i in jsonData['Topics']:
                print(i)

        except github.UnknownObjectException:
            print("Metadata file not available.")
            sys.exit()
        except github.BadCredentialsException:
            print("Invalid user token")
            sys.exit()
        except github.GithubException as e:
            print("Error Occured: ", e)
            sys.exit()
        except Exception as e:
            print("Error Occured")


    elif args.command == 'deleteFile':
        repo = getRepo(args.repoName)
        check = False
        try:
            contents = expandRepo(args.repoName)
            for each in contents:
                if each.name == args.fileName:
                    repo.delete_file(each.path, args.fileName + " Deleted",each.sha, branch = 'main')
                    print(args.fileName + " Deleted")
                    sys.exit()
                else:
                    check = True
            if check == True:
                print("File Not Found")
        except github.BadCredentialsException:
            print("User Token Invalid")
            sys.exit()
        except github.UnknownObjectException :
            print("File doesn't exist.")
            sys.exit()
        except github.GithubException as e:
            print("Error Occured:", e)
            sys.exit()
			
    if args.command == "search":
        try:
            if args.name != None:
                repo_name_search(args.name)
            elif args.topics != None:
                search("topics",args.topics)
            elif args.keywords != None:
                keyword_search(args.keywords)
            else:
                raise Exception("Error: One of the following search criteria must be provided: name, topics, keywords")
        except Exception as e:
            print(e)

if __name__ == '__main__':

    #login and token part done here
    token = check_login()
    g = Github(token)
    user = g.get_user()

    #####
    parser = argparse.ArgumentParser(prog="digitalassets", description="Simple helper commands to interact with Github Repos")

    subparser = parser.add_subparsers(dest='command',help="Testing help command")

    #reponame = subparser.add_parser("reponame")
    update_repo = subparser.add_parser("update-file")

    update_repo.add_argument("--reponame", type = str, required = True)
    update_repo.add_argument("--type", type = str, required = True)
    #update_repo.add_argument("--interactiveBuilding", type = str, required = True)
    update_repo.add_argument("--updateFile", type = str, required = False)
    update_repo.add_argument("--filepath", type = str, required = False)

    ############################################################
    ## Create repo related commands
    ############################################################

    createrepo = subparser.add_parser("createrepo",help="Testing help command")
    createrepo.add_argument("--reponame",type=str,required=True,help="Give the name of the repo to be created")
    createrepo.add_argument("--filepath",type=str,required=False,help= "Give a folder/file path to upload files. Not a required argument")
    createrepo.add_argument("--empty",type=str,required=False,default="False",help="True if we need to create empty repo. By defualt False")
    createrepo.add_argument("--addtopics",nargs='+',type=str,required=False,help="Give a list of topics separated by spaces. Not a required argument")

    #################################################################
    ##Read and download repo
    #################################################################

    clone = subparser.add_parser('clone')
    downloadRepo = subparser.add_parser('downloadRepo',help = "Provide the name of the repo to download it as Zip or Tar file")
    downloadFile = subparser.add_parser('downloadFile', help = "Download an individual file from the repo. Requires repo name and file name")
    listContents = subparser.add_parser('listContents', help = "List the contents of the repo")
    readMetadata = subparser.add_parser('readMetadata', help = "Read the metadata file from the repo")
    deleteFile = subparser.add_parser('deleteFile' , help = "Delete a file from the repo. Requires repo name and file name")

    clone.add_argument('--repoName', type = str, required = True, help = "Provide the name of the repo to clone")
    downloadRepo.add_argument('--repoName', type = str, required = True, help = "Name of the repo")
    downloadFile.add_argument('--fileName', type = str, required = False, help = "File name to be downloaded")
    readMetadata.add_argument('--repoName', type = str, required = True, help = "Name of the repo")
    downloadFile.add_argument('--repoName', type = str, required = True, help = "Name of the repo")
    listContents.add_argument('--repoName', type = str, required = True, help = "Name of the repo")
    deleteFile.add_argument('--repoName',type = str, required = True, help = "Name of the repo")
    deleteFile.add_argument('--fileName',type = str, required = True, help = "Name of the file to be deleted")
	
    ############################################################
    ## Search repo related commands
    ############################################################

    search_command = subparser.add_parser("search")
    search_command.add_argument("--name", type = str)
    search_command.add_argument("--topics", type = str)
    search_command.add_argument("--keywords", type = str)


    args = parser.parse_args()
    if args.command != "search":
        repo_name = args.reponame
        try:
            repo = g.get_repo(repo_name)
        except GithubException as e:
            if e.status == 404:
                print("Repository not found. Go ahead and create it")


    #file_content = repo.get_contents(args.updateFile , ref = 'main')

    ensTopicList = ["ens-machineLearning", "ens-mathematics", "ens-lifeSciences", "ens-Sports", "ens-others"]
   #  args = parser.parse_args()

    main()