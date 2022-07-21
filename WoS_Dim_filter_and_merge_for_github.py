# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 14:00:23 2022

@author: eschares

Script will take data exports from both Web of Science and Dimensions
clean them up and merge them into one file
Typicaly looking at 2018, 19, 20, 21

Dim - ISU+Ames Lab, Export as XLSX
WoS - Core Collection, OG=ISU OR AD=Ames, IA

Use WoS data first, preferred, has Corresponding Author information on nearly all records
Filter down to valid document types, then ISU CAs
Save both with and without ISU CAs
Manually look at without to see if anything obvious we missed

Look at Dimensions data, keep only DOIs we don't already know about from the WoS file
Dimensions doesn't give CA data, have to look those up manually
But first, look at addresses - if all authors from ISU, then it must be an ISU CA (but don't know which author)
"""

import pandas as pd
wos = dim = pd.DataFrame()  #initialize as empty dataframes, enables code to skip parts when not in use

# Read in export files
wos = (pd.read_excel(r"C:\\Users\\eschares\\Collection Development\\WoS_2019-22.xlsx",  sheet_name="savedrecs"))

# Need header=1 because Dim export by default includes an "About the data:" line on row 0
dim = (pd.read_excel(r"C:\\Users\\eschares\\Collection Development\\Dimensions_2017-22.xlsx", sheet_name="Sheet1", header=1))



if not wos.empty:
    print("### Analyzing Web of Science file ###")
    # Keep 17 columns
    wos = wos[['Authors', 'Author Full Names', 'Article Title', 'Source Title', 'Document Type', 'Addresses', 'Reprint Addresses', 'Email Addresses', 'Publisher', 'ISSN', 'eISSN', 'Journal Abbreviation', 'Journal ISO Abbreviation', 'Publication Year', 'DOI', 'UT (Unique WOS ID)', 'Open Access Designations']]
    
    # Add column to remember which database each record came from
    wos['Database'] = "WoS"
    wos['DOI'] = wos['DOI'].str.lower()
    
    
    #### Filter down to valid Document Types ####
    
    # First remove the Book Review type since it contains the word "Review"
    wos = wos.loc[~(wos['Document Type'].isin(['Book Review']))]
    
    # Then keep Articles, which show up as: 
    #     Article; 
    #     Article; Data Paper
    #     Article; Early Access
    # and keep Reviews, which show up as:
    #     Review
    #     Review; Early Access
    # But not Book Review since we removed that in the previous step
    wos = wos.loc[(wos['Document Type'].str.contains('Article', case=False, regex=False, na=False)) | (wos['Document Type'].str.contains('Review', case=False, regex=False, na=False))]
    
    # Sometimes Article Title is repeated from an Early Access version
    wos = wos.drop_duplicates(subset=['Article Title'], keep='first')
    
    
    #### Filter down to ISU CA ####
    filt = ( (wos['Email Addresses'].str.contains('@iastate.edu', case=False, regex=False, na=False)) |
        (wos['Reprint Addresses'].str.contains('Iowa State Univ', case=False, regex=False, na=False)) |
        (wos['Reprint Addresses'].str.contains('Ames, IA', case=False, regex=False, na=False)) |
        (wos['Email Addresses'].str.contains('@ameslab.gov', case=False, regex=False, na=False))
        )
    
    wos['ISU_CA'] = filt
    
    ## Find articles with ISU CA
    wos_ISU = wos.loc[filt]
    print("WoS Rows with ISU CA: ", wos_ISU.shape[0])
    wos_ISU.to_csv("WoS_ISU.csv", index=False)
    
    ## Find articles that DON'T have an ISU CA
    ## Good practice to review this dataframe and see if you missed some articles you should have caught
    wos_notISU = wos.loc[~filt]
    print("WoS Rows NOT with ISU CA: ", wos_notISU.shape[0], "\n")
    wos_notISU.to_csv("WoS_notISU.csv", index=False)
    
    #print(wos_notISU)


if not dim.empty:
    #### Dimensions export ####
    print("### Analyzing Dimensions file ###")
    # Keep 11 columns
    dim = dim[['DOI', 'Title', 'Source title', 'Publisher', 'PubYear', 'Open Access', 'Publication Type', 'Authors', 'Corresponding Authors', 'Authors Affiliations', 'Dimensions URL']]
    
    # Rename columns to match WoS terms
    dim = dim.rename(columns={'Publication Type': 'Document Type', 'Source title': 'Source Title', 'Authors': 'Author Full  Names', 'Title': 'Article Title', 'Authors Affiliations': 'Addresses', 'Corresponding Authors': 'Reprint Addresses', 'PubYear': 'Publication Year', 'Open Access': 'Open Access Designations'})
    dim['Database'] = "Dimensions"
    dim['DOI'] = dim['DOI'].str.lower()
    
    # Need to filter on Document Type in Dimensions, using Dimensions language
    dim = dim.loc[(dim['Document Type'].str.contains('Article', case=False, regex=False, na=False))]
    
    # Sometimes Article Title is repeated from an Early Access version
    dim = dim.drop_duplicates(subset=['Article Title'], keep='first')

    # What DOIs do we already have covered in WoS data
    dois_we_have = wos['DOI']
    dois_we_have = dois_we_have.dropna()
    print("DOIs we got from WoS: ", dois_we_have.shape[0])
    #print(dois_we_have)
    
    # Give me records from Dimensions that are NOT in WoS
    new_DOIs = dim[~dim['DOI'].isin(dois_we_have)]
    
    print("DOIs in Dimensions export that are NOT in WoS export: ", new_DOIs.shape[0])
    #print(new_DOIs)
    
    # If all authors have an ISU address, then the CA must be from ISU as well
    s = (new_DOIs['Addresses'].str.split('\);', expand=True).stack()
       .str.extract('(.*)\s\((.*)')
       .rename(columns={0: 'name', 1: 'location'}))
    
    dim_CA_filt = ( s['location'].str.contains('Iowa State University').groupby(level=0).all() )
    new_DOIs.loc[dim_CA_filt, 'ISU_CA'] = 'TRUE'    #set to TRUE if we can, if not just leave it blank, could still be an ISU CA
    


    ## Combine all WoS and new records from Dimensions, all authors not just ISU CA
    wos_and_dim = pd.concat([wos,new_DOIs], axis=0, ignore_index=True)
    
    # Drop repeat titles, sometimes have two DOIs
    wos_and_dim['Article Title Cleaned'] = wos_and_dim['Article Title'].str.lower().str.replace('-','').str.replace('_','').str.replace('‐','')
    wos_and_dim = wos_and_dim.drop_duplicates(subset=['Article Title Cleaned'], keep='first')
    print("Combined records: ", wos_and_dim.shape[0])
    
    sus_terms = ['editorial', 'retract', 'erratum', 'letter', 'reply', 'letter to the editor', "editors' notes", 'front cover', 'cover feature', 'cover photo', 'cover picture','isbn', 'Response to', 'Titelbild']
    wos_and_dim['Suspicious'] = wos_and_dim['Article Title Cleaned'].apply(lambda x: 1 if any (i in x for i in sus_terms) else 0)
    
    # How many Dimensions CAs did we infer?
    inferred_filt = ((wos_and_dim['ISU_CA'] == 'TRUE') & (wos_and_dim['Database'] == 'Dimensions'))
    print(inferred_filt)
    dim_inferred_ISU_CAs = wos_and_dim[inferred_filt].shape[0]
    
    wos_and_dim.to_csv("allWoS_and_newDim_combined.csv", index=False, encoding='utf-8-sig')


    
    if not wos_and_dim.empty:
        print('\n\n### Analyzing combined WoS and Dim file ###')
        print(f'Combined records: {wos_and_dim.shape[0]}')
        print(f"Possible Suspicious non-articles included (Editorials, Letters, etc): {wos_and_dim['Suspicious'].sum()}")
        print(f"Inferred Dimensions papers as having an ISU CA since ALL authors were from ISU: {dim_inferred_ISU_CAs}")
        print(f"Recommend looking for CA by hand in remaining Dimensions records with blank ISU CA: {wos_and_dim['ISU_CA'].isna().value_counts()[True]}")
    
    

#ToDo:
#add support for a third file, Paid Wiley, will be messier data, can put anything in the title field
#figure out exporting as input, csv or Excel, will mess up the encoding
#put article title and doi drop_duplicates into a function, figure out how that works
#You might want to check the following: Editorial, Retraction, Cover Photo