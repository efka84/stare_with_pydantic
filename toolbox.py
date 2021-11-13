
"""
The 'toolbox.py' contains all the functions that are needed by the main.py
The project is Windows platform specific.

Main parts of 'toolbox.py':
             1.  definitino of  API functions >> GET and POST
             2.  validation of input-data
             3.  functions using the API functions for Database interaction
"""

import json
import numpy as np
import pandas as pd

def stare_api_get(url):  #'url' is the resource 
    """
    get 'read-only' information from the STARE-Database
    input:  API url
    return: Response and Status of API call in json 
    """

    import win32com.client
    # using win32com.client ease of Windows Autolog ability
    # find deatails> https://docs.microsoft.com/en-us/windows/win32/winhttp/winhttprequest
    base_url="https://stare-dev.de.ema.ad.pwcinternal.com/STARE/api" 
    URL=base_url+url  # our endpoint!
    com_obj=win32com.client.Dispatch('WinHTTP.WinHTTPRequest.5.1') # instantiate a WinHttpRequest object
    com_obj.SetAutoLogonPolicy(0) # automatically send user credentials
    com_obj.Open('GET',URL, False) # open an http connection with 'GET' verb/method
    com_obj.SetRequestHeader("Content-Type","application/json") # request header definition
    com_obj.Send() # send the http Request
    return com_obj.ResponseText, com_obj.Status # json objects



def stare_api_POST(url,json_object):
    """
    post information to the STARE-DataBase 
    input:  API url and the input-data in json form
    return: Response and Status of API call in json 
    """
    import win32com.client
    base_url = 'https://stare-dev.de.ema.ad.pwcinternal.com/STARE/api'    
    URL=base_url+url
    COM_OBJ = win32com.client.Dispatch('WinHTTP.WinHTTPRequest.5.1')
    COM_OBJ.SetAutoLogonPolicy(0)
    COM_OBJ.Open('POST', URL, False) # open an http connection with 'POST' verb/method
    COM_OBJ.SetRequestHeader("Content-Type","application/json")
    COM_OBJ.Send(json_object)
    return COM_OBJ.ResponseText, COM_OBJ.Status



# using pydantic library for input-data validation
# using BaseModel and VaildationError classes
# legalItemkey has to be uuid
from pydantic import BaseModel, ValidationError
from uuid import UUID
class api_input_validation(BaseModel):
    legalItemKey          : UUID
    rentablevalue_nr      : int 
    rentablevalue_amnt    : float


# prettify the printing of json for users
def dictprint(dictl):
    import json
    print(json.dumps(dictl, indent=8))


# output clear error messages
def error(msg):
    print("Error: "+msg)
    input()
    quit()

# no empty cells are allowed
# cell content must be provided to allow further validation
def if_null(cellcontent):
    if isinstance(cellcontent,str):
        cellcontent=cellcontent.strip()
    if pd.isnull(cellcontent) or cellcontent=='':
        error(f"Cell cannot be empty!")


#validat GUID
# uuid universal unique identifier
# guid globally unique identifier : MSoft variant
from uuid import UUID
def validate_guid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.
    Parameters  uuid_to_test : str;  version : {1, 2, 3, 4}
    Returns     `True` if uuid_to_test is a valid UUID, otherwise `False`.
    Examples    is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')>>>True
                is_valid_uuid('c9bf9e58') >>>False
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        error("legalItemKeyError:  GUID does not match pattern!\nStopping here!")

    #return False
    return str(uuid_obj) == uuid_to_test


# validate Sollwert 
def validate_Sollwert(v):
    if isinstance(v, str):
        error(f"'Sollwert' should be numeric, without quotations, and point\
             decimal!")



def legalItemKey_exists(legalItemKey):
    """check if the LegalItemKey exists"""
    urlFindlegalItem = f"/LegalItem/FindLegalItem?legalItemKey={legalItemKey}"
    return stare_api_get(urlFindlegalItem)



def validate_entity_type():
    url_GetEntityType = "/DataMaintenance/GetEntityTypes"
    R, S= stare_api_get(url_GetEntityType)
    tt = json.loads(R)
    
    for  counter, t in enumerate(tt,0):
        if "Reference data for Rentable value" in t.keys():
            break
    entityKey = tt[counter-1]['entityKey']
    #entityKey=70
    if entityKey !=40:
        print(f"EntityKey must be 40, found EntityKey = {entityKey}")
        input()
    else:
        return entityKey




def get_dataset_w_value(entityKey,legalItemKey,rentableValue):
    url = f"/DataSet/GetDataSetWithValue?entityTypeKey={entityKey}&legalItemKey={legalItemKey}"
    upload_DataSetWithValue = {
      "xbrlName": "pwc.de.stare.project_rentablevalue.number",
      "itemValue": str(rentableValue)
    }
    jo = json.dumps(upload_DataSetWithValue)  # convert to a json object
    R, S = stare_api_POST(url,jo)
    return R, S


def get_commit_key():
    import os
    user=os.getlogin()
    url= f"/DataMaintenance/GetCommitKey?title={user}-for-DataSet"
    R, S = stare_api_get(url)
    commitKey=json.loads(R)['commitKey']
    return commitKey




def add_data(dataSetKey,commitKey,rentableValue,validFrom1,targetAmount):
    AddDataUrl = f"/Data/AddData?dataSetKey={dataSetKey}&commitKey={commitKey}"
    AddDataUpload = [{
    "xbrlName": "pwc.de.stare.project_rentablevalue.number",
    "itemValue": str(rentableValue),
    "validFrom": str(validFrom1)},   
    {
    "xbrlName": "pwc.de.stare.project_rentablevalue.transactionData.targetAmount",
    "itemValue": str(targetAmount),
    "validFrom": str(validFrom1)}]
    AddDataUpload_json_object= json.dumps(AddDataUpload)
    R, S = stare_api_POST(AddDataUrl,AddDataUpload_json_object)
    return S



def approve_commit(commitKey):
    url_approveCommit = f'/DataMaintenance/ApproveCommit?commitKey={commitKey}'
    R,S = stare_api_POST(url_approveCommit,str(commitKey))
    if S==200:
        print("Data committed successfully!")
        #dictprint(json.loads(R))
    else:
       error("Error")



def get_current(dataSetKey):
    """Returns all values of a dataset that are valid at the current time"""
    url_GetCurrent = f'/Data/GetCurrent?dataSetKey={dataSetKey}'
    R,S = stare_api_get(url_GetCurrent)
    if S == 200:
        print("The following data was uploaded")
        dictprint(json.loads(R))
    else:
        print("No Dataset found!")



def get_entity_location():
    """Returns a list of entities that must always be placed under one or more location"""
    url = f"/Location/GetEntityLocation"
    R,S = stare_api_get(url)
    tt=json.loads(R)
    for ggh, t in enumerate(tt):
        if "Reference data for Rentable value" in t.values():
         break
    return tt[ggh]['entityLocationUnder']



def add_dataset(commitKey,legalItemKey,entityKey):
    """Add a new dataset. In this dataset the values can be insterted afterwards"""
    url_AddDataSet = f"/DataSet/AddDataSet?commitKey={commitKey}"
    upload_AddDataSet = {
     "legalItemKey": str(legalItemKey),
     "title": "Solldaten",
     "entityKey": entityKey,
     "locations": ["/9/"]}
    json_object=json.dumps(upload_AddDataSet )
    R,S = stare_api_POST(url_AddDataSet,json_object)
    return R, S
