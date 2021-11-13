
"""
The application does (see also uml.md):
    1. uploads data from an excel file puts them in a pandas DataFrame
    2. validates the data in the DataFrame with 'pydantic' library
    3. uploads them in the STARE Database

To Do:
    1. Error Messaging with 'pydantic'
    2. Validate dates with 'pydantic'
    3. Type notation implementation

"""
import time 
start = time.time()  #start the stop-watch
import pandas as pd
import json
import numpy as np
from pydantic import BaseModel, ValidationError
from uuid import UUID
from toolbox import stare_api_POST, stare_api_get, dictprint, legalItemKey_exists,validate_guid,\
     validate_entity_type,get_dataset_w_value,get_commit_key,add_data,approve_commit, get_current,\
          get_entity_location, add_dataset,validate_Sollwert, error, if_null, api_input_validation


print("===================================================================")
print("                      STARE IMPORTER TOOL                          ")
print("===================================================================")

# Data upload
xlsx="Solldaten.xlsx"

try:
    df=pd.read_excel(xlsx,skiprows=[0])
except FileNotFoundError as err:
    error("Excel File not found!\nPut a copy of 'Solldaten.xlsx' in the same folder as the .exe file!")

# loop over the rows of excel
for index, row in df.iterrows():
    print(f"\n Excel row no.: {index+3} \n")
    legalItemKey  = df.iloc[index]['legalItemKey']
    print(f"            Mandant : {legalItemKey}")
    ent= df.iloc[index]['EntityKey']
    print(f"         Entity key : {ent}")
    rentableValue = df.iloc[index]['pwc.de.stare.project_rentablevalue.number']
    print(f" Einheitswertnummer : {rentableValue}")
    targetAmount  = df.iloc[index]['pwc.de.stare.project_rentablevalue.transactionData.targetAmount']
    print(f"           Sollwert : {targetAmount}")
    validFrom1    = df.iloc[index]['validFrom']
    print(f"   Gültigkeitsdatum : {validFrom1}\n")
    
    ## VALIDATION WITH PYDANTIC
    # bundle the values to be validated in a dict
    data2 = { 
          'legalItemKey' : legalItemKey,
          'rentablevalue_nr' : rentableValue,
          'rentablevalue_amnt': targetAmount
        }

    print(data2)    
    try:
        api_input_validation(**data2)
    except ValidationError as e:
        print(e.json())
        input()
        quit()        

    # make sure, date is not empty >> todo: validate with pydantic
    if_null(validFrom1)
    entityKey =  validate_entity_type()
    
    ## LEGALITEMKEY/Client EXISTS?
    
    R,S = legalItemKey_exists(legalItemKey)
    # if legal item already exists
    # http status codes 'developer.mozilla.org/de/docs/Web/HTTP/Status'
    if S==200: # 200 = yes!
        print("\n\t legalItemKey exists already!")
        R,S = get_dataset_w_value(entityKey,legalItemKey,rentableValue)
        
        if S == 200: # yes, Client exists and the DataSet exists
            print("\tDataSet exists already!")
            print("\tgetting commit key...") #  show  access-rights
            dataSetKey = json.loads(R)[0]['dataSetKey']
            rights_r   = json.loads(R)[0]['isReadable']
            rights_w   = json.loads(R)[0]['isWriteable']
            print(f"\nUser Rights:\nHas Reader Rights:{rights_r}\nHas Writing Rights: {rights_w}")

            # start updating
            # get commitkey 
            commitKey  = get_commit_key()
            #Dataset exist! only update Record => add_data()
            print("\n\tAdding Data...") 
            status     = add_data(dataSetKey,commitKey,rentableValue,validFrom1,targetAmount)
            if status != 200:
                error(" \tDataSet konnte nicht aktualisiert werden!")
            approve_commit(commitKey)
            get_current(dataSetKey)
        # LegalItemKey exists but the Dataset does not
        else:
            print("DataSet does not exist!\tAdding a DataSet...\n")
            print("getting commit key...")
            commitKey=get_commit_key()
            print("Adding DataSet...")
            R,S = add_dataset(commitKey,legalItemKey,entityKey)
            if S==200:
                dataSetKey = json.loads(R)['dataSetKey']
            else:
                print(R)
                error("DataSet could not be added")
            #   commitKey  = get_commit_key()
            print("Adding Data...")
            status     = add_data(dataSetKey,commitKey,rentableValue,validFrom1,targetAmount)
            if status != 200:
                print(f"Status code: {status}")
                error("Data could not be added!")
            approve_commit(commitKey)
            get_current(dataSetKey)
    
    ## LegalItem does not exist
    else:
            print("DataSet does not exist!\tAdding a DataSet...\n")
            print("getting commit key...")
            commitKey=get_commit_key()
            print("Adding DataSet...")
            R,S = add_dataset(commitKey,legalItemKey,entityKey)
            if S==200:
                dataSetKey = json.loads(R)['dataSetKey']
            else:
                print(R)
                error("DataSet could not be added")
            #   commitKey  = get_commit_key()
            print("Adding Data...")
            status     = add_data(dataSetKey,commitKey,rentableValue,validFrom1,targetAmount)
            if status != 200:
                print(f"Status code: {status}")
                error("Data could not be added!")
            approve_commit(commitKey)
            get_current(dataSetKey)
    
print(f"\t\t {index+1} entries processed in {(time.time()-start)/60:.2f} minutes!")
input()
