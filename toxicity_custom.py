# Dont touch this file! This is intended to be a template for implementing new custom checks

from inspect import currentframe
from flask import current_app, g
from .functions import checkData
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import copy
from scipy import stats

def toxicity(all_dfs):
    
    current_function_name = str(currentframe().f_code.co_name)
    
    # function should be named after the dataset in app.datasets in __init__.py
    assert current_function_name in current_app.datasets.keys(), \
        f"function {current_function_name} not found in current_app.datasets.keys() - naming convention not followed"

    expectedtables = set(current_app.datasets.get(current_function_name).get('tables'))
    assert expectedtables.issubset(set(all_dfs.keys())), \
        f"""In function {current_function_name} - {expectedtables - set(all_dfs.keys())} not found in keys of all_dfs ({','.join(all_dfs.keys())})"""

    eng = g.eng

    # define errors and warnings list
    errs = []
    warnings = []
    def dcValueAgainstMultipleValues (field,ucfield,listname,listfield,df):
        # author - Jordan Golemo
        # example: field = qacode, ucfield = QACode, listname = lu_toxtestacceptability, listfield = testacceptability, df = results
        # get published lookup list value
        try:
            results = eng.execute("select * from lu_toxtestacceptability;")
            db = pd.DataFrame(results.fetchall())
            db.columns = results.keys()
            list_of_codes = db[listfield].tolist()
            # submitted field to check against lookup list
            df_search = df[field]
            # bug fix number 26 - 23feb18
            df_search = df_search.apply(lambda row: str(row))
            df_err = df_search.dropna().str.replace(', ',',').str.replace(',',' ').str.split(' ',expand=True)
            # Creates list of rows with errors (er_inds) / list of the problematic value (er_vals)
            inds = [df_err[i].index[(df_err[i].notnull()) & (~df_err[i].isin(list_of_codes))] for i in range(len(df_err.columns))]
            er_inds = [item for sublist in inds for item in sublist]
            vals = [df_err[i].loc[(df_err[i].notnull()) & (~df_err[i].isin(list_of_codes))] for i in range(len(df_err.columns))]
            er_vals = [item for sublist in vals for item in sublist]
            # errors out NaN rows as well as Invalid QA Rows
            for i in range(len(er_inds)):
                            print("commented out an irrelevant check")
            i#checkData([er_inds[i]],str(ucfield),'Undefined Error','error','You have submitted an invalid code: %s. Please see lookup list: <a href=http://checker.sccwrp.org/checker/scraper?action=help&layer=%s target=_blank>%s</a>' % (er_vals[i],listname,listname),df)

        except ValueError:
            # need to setup some code to email sccwrp if fails
            print("Failed to get lookup list value: %s" % listname)

    toxbatch = all_dfs['tbl_toxbatch']
    toxbatch = toxbatch.assign(tmp_row = toxbatch.index)
    
    toxresults = all_dfs['tbl_toxresults']
    toxresults = toxresults.assign(tmp_row = toxresults.index)
    
    toxwq = all_dfs['tbl_toxwq']
    toxwq = toxwq.assign(tmp_row = toxwq.index)
    

    toxbatch_args = {
        "dataframe": toxbatch,
        "tablename": 'tbl_toxbatch',
        "badrows": [],
        "badcolumn": "",
        "error_type": "",
        "is_core_error": False,
        "error_message": ""
    }

    toxresults_args = {
        "dataframe": toxresults,
        "tablename": 'tbl_toxresults',
        "badrows": [],
        "badcolumn": "",
        "error_type": "",
        "is_core_error": False,
        "error_message": ""
    }

    toxwq_args = {
        "dataframe": toxwq,
        "tablename": 'tbl_toxwq',
        "badrows": [],
        "badcolumn": "",
        "error_type": "",
        "is_core_error": False,
        "error_message": ""
    }
    eng  = g.eng

    ## LOGIC ##
    print("Starting Toxicity Logic Checks")
    
    # 1 - All records for each table must have a corresponding record in the other tables due on submission. Join tables on Agency/LabCode and ToxBatch/QABatch
    ### make sure there are records that match between batch and result - otherwise big problem
    # EACH TAB MUST HAVE A CORRESPONDING RELATED RECORD IN ALL THE OTHER TABS - JOIN TABLES BASED ON TOXBATCH AND LAB
    
    # batch
    badrows = toxbatch[~toxbatch[['toxbatch','lab']].isin(toxresults[['toxbatch','lab']].to_dict(orient='list')).all(axis=1)].tmp_row.tolist()
    toxbatch_args.update({
        "dataframe": toxbatch,
        "tablename": 'tbl_toxbatch',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "Each Toxicity Batch record must have a corresponding Toxicity Result record. Records are matched on ToxBatch and Lab"
    })
    errs = [*errs, checkData(**toxbatch_args)]
    
    badrows = toxbatch[~toxbatch[['toxbatch','lab']].isin(toxwq[['toxbatch','lab']].to_dict(orient='list')).all(axis=1)].tmp_row.tolist()
    toxbatch_args.update({
        "dataframe": toxbatch,
        "tablename": 'tbl_toxbatch',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "Each Toxicity Batch record must have a corresponding Toxicity WQ record. Records are matched on ToxBatch and Lab."
    })
    errs = [*errs, checkData(**toxbatch_args)]

    
    # result
    badrows = toxresults[~toxresults[['toxbatch','lab']].isin(toxbatch[['toxbatch','lab']].to_dict(orient='list')).all(axis=1)].tmp_row.tolist()
    toxresults_args.update({
        "dataframe": toxresults,
        "tablename": 'tbl_toxresults',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "Each Toxicity Batch record must have a corresponding Toxicity Result record. Records are matched on ToxBatch and Lab"
    })
    errs = [*errs, checkData(**toxbatch_args)]

    badrows = toxresults[~toxresults[['toxbatch','lab']].isin(toxwq[['toxbatch','lab']].to_dict(orient='list')).all(axis=1)].tmp_row.tolist()
    toxresults_args.update({
        "dataframe": toxresults,
        "tablename": 'tbl_toxresults',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "ach Toxicity Result record must have a corresponding Toxicity WQ record. Records are matched on ToxBatch and Lab."
    })
    errs = [*errs, checkData(**toxresults_args)] 
    
    # wq
    badrows = toxwq[~toxwq[['toxbatch','lab']].isin(toxbatch[['toxbatch','lab']].to_dict(orient='list')).all(axis=1)].tmp_row.tolist()
    toxwq_args.update({
        "dataframe": toxwq,
        "tablename": 'tbl_toxwq',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "Each Toxicity WQ record must have a corresponding Toxicity Batch record. Records are matched on ToxBatch and Lab."
    })
    errs = [*errs, checkData(**toxwq_args)]
    
    badrows = toxwq[~toxwq[['toxbatch','lab']].isin(toxresults[['toxbatch','lab']].to_dict(orient='list')).all(axis=1)].tmp_row.tolist()
    toxwq_args.update({
        "dataframe": toxwq,
        "tablename": 'tbl_toxwq',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "Each Toxicity WQ record must have a corresponding Toxicity Result record. Records are matched on ToxBatch and Lab."
    })
    errs = [*errs, checkData(**toxwq_args)]

    # 2 - Check for the minimum number of replicates - ee and mg = 5 and na = 10
    ## first get a lab replicate count grouped on stationid, toxbatch, and species
    dfrep = pd.DataFrame(toxresults.groupby(['stationid','toxbatch','species']).size().reset_index(name='replicatecount'))
    ## merge the lab replicant group with results so that you can get the tmp_row - the lab rep count will be matched with each lab rep
    ## we will want to highlight them as a group rather than by row
    dfrep = pd.merge(dfrep,toxresults, on=['stationid','toxbatch','species'], how='inner')
    print("## A MINIMUM NUMBER OF 5 REPLICATES ARE REQUIRED FOR SPECIES EOHAUSTORIUS ESTUARIUS AND MYTILUS GALLOPROVINCIALIS ##")
    badrows = dfrep[
        (dfrep['species'].isin(['Eohaustorius estuarius','EE','Mytilus galloprovincialis','MG'])) & 
        (dfrep['replicatecount'] < 5)
    ].tmp_row.tolist()
    toxresults_args.update({
        "dataframe": toxresults,
        "tablename": 'tbl_toxresults',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "A minimum number of 5 replicates are required for species Eohaustorius estuarius and Mytilus galloprovincialis"
    })
    errs = [*errs, checkData(**toxresults_args)] 
    print("## A MINIMUM NUMBER OF 10 REPLICATES ARE REQUIRED FOR SPECIES NEANTHES ARENACEODENTATA ##")
    badrows = dfrep[(dfrep['species'] == 'Neanthes arenaceodentata') & (dfrep['replicatecount'] < 10)].tmp_row.tolist()
    toxresults_args.update({
        "dataframe": toxresults,
        "tablename": 'tbl_toxresults',
        "badrows": badrows,
        "badcolumn": "toxbatch,lab",
        "error_type": "Logic Error",
        "is_core_error": False,
        "error_message": "A minimum number of 10 replicates are required for species Neanthes arenaceodentata"
    })
    errs = [*errs, checkData(**toxresults_args)] 
    
    # 3. EACH BS or SWI BATCH MUST HAVE A "REFERENCE TOXICANT" BATCH WITHIN A SPECIFIED DATE RANGE.
    print("# 3. EACH BS or SWI BATCH MUST HAVE A REFERENCE TOXICANT BATCH WITHIN A SPECIFIED DATE RANGE.")
    # get reference toxicant dataframe
    batchrt = toxbatch[
        ['toxbatch','teststartdate', 'actualtestduration', 'actualtestdurationunits', 'referencebatch']
    ].where(toxbatch['matrix'].isin(['RT','Reference Toxicant']))
    # drop emptys
    batchrt = batchrt.dropna()
    if len(batchrt.index) != 0:
        # get bs dataframe added swi on 21june17
        batchbs = toxbatch[
            ['toxbatch', 'matrix', 'species', 'teststartdate', 'actualtestduration', 'actualtestdurationunits', 'referencebatch','tmp_row']
        ].where(toxbatch['matrix'].isin(['BS','SWI','Whole Sediment','Sediment Water Interface']))
        # drop emptys
        batchbs = batchbs.dropna()
        # get bs dataframe
        if len(batchbs.index) != 0:
            # find any bs batch records with a missing rt 
            # merge bs and rt
            bsmerge = pd.merge(batchbs, batchrt, how = 'inner', on = ['referencebatch'])
            if len(bsmerge.index) != 0:
                # create date range column
                def checkRTDate(grp):
                    grp['teststartdate_x'] = pd.to_datetime(grp['teststartdate_x'])
                    grp['teststartdate_y'] = pd.to_datetime(grp['teststartdate_y'])
                    d = grp['teststartdate_x'] - grp['teststartdate_y']
                    grp['daterange'] = abs(d.days)
                    return grp
                bsmerge = bsmerge.apply(checkRTDate, axis = 1)
                # checks by species and datarange
                badrows = bsmerge.loc[(bsmerge['species'] == 'Eohaustorius estuarius') & (bsmerge['daterange'] > 10)].tmp_row.tolist()
                toxbatch_args.update({
                    "dataframe": toxbatch,
                    "tablename": 'tbl_toxbatch',
                    "badrows": badrows,
                    "badcolumn": "matrix",
                    "error_type": "Logic Error",
                    "is_core_error": False,
                    "error_message": "Each BS or SWI batch must have a Reference Toxicant batch within a specified date range: EE less than 10 days"
                })
                errs = [*errs, checkData(**toxbatch_args)] 
                
                badrows = bsmerge.loc[
                    (bsmerge['species'] == 'Mytilus galloprovincialis') & (bsmerge['daterange'] > 2)
                ].tmp_row.tolist()
                toxbatch_args.update({
                    "dataframe": toxbatch,
                    "tablename": 'tbl_toxbatch',
                    "badrows": badrows,
                    "badcolumn": "matrix",
                    "error_type": "Logic Error",
                    "is_core_error": False,
                    "error_message": "Each BS or SWI batch must have a Reference Toxicant batch within a specified date range: MG less than 2 days"
                })
                errs = [*errs, checkData(**toxbatch_args)] 
        else:
            toxbatch_args.update({
                    "dataframe": toxbatch,
                    "tablename": 'tbl_toxbatch',
                    "badrows": toxbatch.tmp_row.to_list(),
                    "badcolumn": "matrix",
                    "error_type": "Logic Error",
                    "is_core_error": False,
                    "error_message": "A submission requires a Bulk Sediment record in batch submission"
                })
            errs = [*errs, checkData(**toxbatch_args)] 
    else:
        toxbatch_args.update({
            "dataframe": toxbatch,
            "tablename": 'tbl_toxbatch',
            "badrows": toxbatch.tmp_row.to_list(),
            "badcolumn": "matrix",
            "error_type": "Logic Error",
            "is_core_error": False,
            "error_message": "A submission requires a Reference Toxicant record in batch submission"
        })
        errs = [*errs, checkData(**toxbatch_args)] 

    print("# Eric - A toxicity submission (batch, results, wq) requires that the field data be submitted first. ")
    print("# To check all unique Result/StationID records should have a corresponding record in Field/Grab/StationID (make sure it wasn't abandoned also). This should be an error.")
    
    # first we need to call the field grab event table and get back all the stations that did not fail
    sql_df = pd.read_sql("SELECT stationid FROM tbl_grabevent WHERE toxicity = 'Yes' AND grabfail = 'None'", eng)
    
    # get only the unique records for database/stationid
    unique_stations = sql_df.stationid.unique()
    
    # find what records dont match the unique stations in the database
    badrows = toxresults[~toxresults.stationid.isin(unique_stations)].tmp_row.tolist()
    toxresults_args.update({
        "dataframe": toxresults,
        "tablename": 'tbl_toxresults',
        "badrows": badrows,
        "badcolumn": "stationid",
        "error_type": "Undefined Error",
        "is_core_error": False,
        "error_message": "A toxicity submission requires that the field data be submitted first. Your station does not match the grab event table."
    })
    errs = [*errs, checkData(**toxresults_args)] 
    ## END LOGIC CHECKS ##
    print("## END LOGIC CHECKS ##")

    ## CUSTOM CHECKS ##
    print("## CUSTOM CHECKS ##")
    if len(errs) == 0:
        ## BATCH CHECKS ##
        print("Starting Toxicity Batch Information Checks")
        # 1. EACH BATCH WITH A MATRIX OF BS MUST INCLUDE A CORRESPONDING RESULT CNEG SAMPLE
        print("## EACH BATCH WITH A MATRIX OF BS MUST INCLUDE A CORRESPONDING RESULT CNEG SAMPLE ##")
        # first get unique cneg records from result dataframe
        bsresult = toxresults[['toxbatch','sampletypecode']].where(toxresults['sampletypecode'] == 'CNEG')
        bsresult = bsresult.dropna() 
        bsresult['unique'] = np.nan
        bsresult = bsresult.groupby(['toxbatch','sampletypecode'])['unique'].nunique().reset_index()
        # second get unique batch records with a matrix of bs
        bsbatch = toxbatch[['toxbatch','matrix','tmp_row']].where(toxbatch['matrix'].isin(["Whole Sediment","BS"]))
        bsbatch = bsbatch.dropna()
        bsbatch['unique'] = np.nan
        bsbatch = bsbatch.groupby(['toxbatch','matrix','tmp_row'])['unique'].nunique().reset_index()
        # merge unique cneg and toxbatch records on where they match
        bsmerge = bsbatch.merge(bsresult, on='toxbatch', how='inner')
        bslocate = bsbatch[(~bsbatch.toxbatch.isin(bsmerge.toxbatch))].toxbatch.tolist()
        # label toxbatch records
        print(bsbatch[(~bsbatch.toxbatch.isin(bsmerge.toxbatch))])
        badrows = bsbatch[(~bsbatch.toxbatch.isin(bsmerge.toxbatch))].tmp_row.tolist()
        toxbatch_args.update({
            "dataframe": toxbatch,
            "tablename": 'tbl_toxbatch',
            "badrows": badrows,
            "badcolumn": "sampletypecode",
            "error_type": "Undefined Error",
            "is_core_error": False,
            "error_message": "Each batch with a matrix of BS must include a corresponding toxresults CNEG sample."
        })
        errs = [*errs, checkData(**toxbatch_args)]  

        # 2. EACH BATCH WITH A MATRIX OF RT MUST INCLUDE A CORRESPONDING toxresults WITH SAMPLETYPECODE = RFNH3.
        print("## EACH BATCH WITH A MATRIX OF RT MUST INCLUDE A CORRESPONDING toxresults WITH SAMPLETYPECODE = RFNH3. ##")
        # first get unique rfnh3 records from result dataframe
        rtresult = toxresults[['toxbatch','sampletypecode']].where(toxresults['sampletypecode'] == 'RFNH3')
        rtresult = rtresult.dropna() 
        rtresult['unique'] = np.nan
        rtresult = rtresult.groupby(['toxbatch','sampletypecode'])['unique'].nunique().reset_index()
        # second get unique toxbatch records with a matrix of rt
        rtbatch = toxbatch[['toxbatch','matrix','tmp_row']].where(toxbatch['matrix'].isin(["Reference Toxicant","RT"]))
        rtbatch = rtbatch.dropna()
        rtbatch['unique'] = np.nan
        rtbatch = rtbatch.groupby(['toxbatch','matrix','tmp_row'])['unique'].nunique().reset_index()
        # merge unique rt and batch records on where they match
        rtmerge = rtbatch.merge(rtresult, on='toxbatch', how='inner')
        print(rtbatch[(~rtbatch.toxbatch.isin(rtmerge.toxbatch))])
        badrows = rtbatch[(~rtbatch.toxbatch.isin(rtmerge.toxbatch))].tmp_row.tolist()
        toxbatch_args.update({
            "dataframe": toxbatch,
            "tablename": 'tbl_toxbatch',
            "badrows": badrows,
            "badcolumn": "sampletypecode",
            "error_type": "Undefined Error",
            "is_core_error": False,
            "error_message": "Each batch with a matrix of RT must include a corresponding result SampleTypeCode = RFNH3."
        })
        errs = [*errs, checkData(**toxbatch_args)]      
        
        # 3. TESTACCEPTABILITY CHECK - A SINGLE QACODE IS REQUIRED BUT MULTIPLE QACODES ARE POSSIBLE (MANY TO MANY) author - Jordan Golemo
        ## WORKS BUT TOO SLOW
        print("TESTACCEPTABILITY CHECK - A SINGLE QACODE IS REQUIRED BUT MULTIPLE QACODES ARE POSSIBLE (MANY TO MANY)")
        dcValueAgainstMultipleValues ('testacceptability','TestAcceptability','lu_toxtestacceptability','testacceptability',batch)
        ## END BATCH CHECKS ##

        ## RESULT CHECKS ##
        print("Starting Toxicity Result Checks")
        
        # 1. CHECK IF SAMPLES WERE TESTED WITHIN 28 DAY HOLDING TIME
        print("## CHECK IF SAMPLES WERE TESTED WITHIN 28 DAY HOLDING TIME ##")
        # merge result and batch on toxbatch but include teststartdate
        df28 = pd.merge(toxresults, toxbatch[['toxbatch', 'teststartdate']], how = 'left', on = 'toxbatch')
        # change the following field types to pandas datetime so they can be calculated (we arent changing submitted data)
        df28['teststartdate'] = pd.to_datetime(df28['teststartdate'])
        df28['samplecollectdate'] = pd.to_datetime(df28['samplecollectdate'])
        # put day differences into own column
        df28['checkdate'] = df28['teststartdate'] - df28['samplecollectdate']
        # locate any records with a greater than 28 period
        print(df28.loc[df28['checkdate'].dt.days > 28])
        badrows = df28.loc[df28['checkdate'].dt.days > 28].tmp_row.tolist()
        toxresults_args.update({
            "dataframe": toxresults,
            "tablename": 'tbl_toxresults',
            "badrows": badrows,
            "badcolumn": "sampletypecode",
            "error_type": "Undefined Error",
            "is_core_error": False,
            "error_message": "Samples must be tested within a 28 day holding time."
        })
        errs = [*errs, checkData(**toxresults_args)] 

        # 2. REFERENCE TOXICANT IN THE MATRIX FIELD MUST HAVE DATA IN CONCENTRATION FIELD. CAN'T BE -88.
        print("## REFERENCE TOXICANT IN THE MATRIX FIELD MUST HAVE DATA IN CONCENTRATION FIELD. CANT BE -88 ##")
        print(toxresults.loc[toxresults['matrix'].isin(['Reference Toxicant','RT']) & (toxresults['concentration'] == -88)])
        badrows = toxresults.loc[toxresults['matrix'].isin(['Reference Toxicant','RT']) & (toxresults['concentration'] == -88)].tmp_row.tolist()
        toxresults_args.update({
            "dataframe": toxresults,
            "tablename": 'tbl_toxresults',
            "badrows": badrows,
            "badcolumn": "concentration",
            "error_type": "Undefined Error",
            "is_core_error": False,
            "error_message": "A Reference Toxicant record in the Matrix field can not have a -88 in the Concentration field."
        })
        errs = [*errs, checkData(**toxresults_args)] 
        
        
        # 4. QACODE CHECK - A SINGLE QACODE IS REQUIRED BUT MULTIPLE QACODES ARE POSSIBLE (MANY TO MANY). author - Jordan Golemo
        print("QACODE CHECK - A SINGLE QACODE IS REQUIRED BUT MULTIPLE QACODES ARE POSSIBLE (MANY TO MANY)")
        dcValueAgainstMultipleValues ('qacode','QACode','lu_toxtestacceptability','testacceptability',toxresults)
        ## END RESULT CHECKS ##

        ## START WQ CHECKS ##
        print("Starting Toxicity WQ Checks")
        print("Starting Toxicity WQ Checks")
        # 1. CHECK THAT WATER QUALITY PARAMETERS ARE WITHIN ACCEPTABLE RANGES. - WARNING ONLY NOT ERROR MESSSAGE
        # merge wq and batch on toxbatch to get species from batch
        dfwq = pd.merge(toxwq[['toxbatch','parameter','result','matrix']], toxbatch[['toxbatch', 'species']], how = 'left', on = 'toxbatch')
        
        
        print(dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','Mytilus galloprovincialis','EE','MG'])) & (dfwq['parameter'] == 'Temperature') & ((dfwq['result'] < 13) | (dfwq['result'] > 17))])
        badrows = dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','Mytilus galloprovincialis','EE','MG'])) & (dfwq['parameter'] == 'Temperature') & ((dfwq['result'] < 13) | (dfwq['result'] > 17))].index.tolist()
        toxwq_args.update({
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": badrows,
            "badcolumn": "result",
            "error_type": "Undefined Warning",
            "is_core_error": False,
            "error_message": "Water quality parameter for Temperature not in acceptable range: must be between 13-17."
        })
        warnings = [*warnings, checkData(**toxwq_args)]
        
        
        print(dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','Mytilus galloprovincialis','EE','MG'])) & (dfwq['parameter'] == 'Salinity') & ((dfwq['result'] < 30) | (dfwq['result'] > 34))])
        badrows = dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','Mytilus galloprovincialis','EE','MG'])) & (dfwq['parameter'] == 'Salinity') & ((dfwq['result'] < 30) | (dfwq['result'] > 34))].index.tolist()
        toxwq_args.update({
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": badrows,
            "badcolumn": "result",
            "error_type": "Undefined Warning",
            "is_core_error": False,
            "error_message": "Water quality parameter for Salinity not in acceptable range: must be between 30-34."
        })
        warnings = [*warnings, checkData(**toxwq_args)]
        
        
        print(dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','EE'])) & (dfwq['parameter'] == 'Dissolved Oxygen') & (dfwq['result'] < 7.5)])
        badrows = dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','EE'])) & (dfwq['parameter'] == 'Dissolved Oxygen') & (dfwq['result'] < 7.5)].index.tolist()
        toxwq_args.update({
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": badrows,
            "badcolumn": "result",
            "error_type": "Undefined Warning",
            "is_core_error": False,
            "error_message": "Water quality parameter for Dissolved Oxygen not in acceptable range: must be greater than 7.5."
        })
        warnings = [*warnings, checkData(**toxwq_args)]

            
        print(dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','EE'])) & (dfwq['parameter'] == 'pH') & ((dfwq['result'] < 7.7) | (dfwq['result'] > 8.3))])
        badrows = dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','EE'])) & (dfwq['parameter'] == 'pH') & ((dfwq['result'] < 7.7) | (dfwq['result'] > 8.3))].index.tolist()
        toxwq_args.update({
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": badrows,
            "badcolumn": "result",
            "error_type": "Undefined Warning",
            "is_core_error": False,
            "error_message": "Water quality parameter for pH not in acceptable range: must be between 7.7-8.3."
        })
        warnings = [*warnings, checkData(**toxwq_args)]

        
        print(dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','EE'])) & (dfwq['parameter'] == 'Total Ammonia') & (dfwq['result'] > 20)&(dfwq['matrix']!='Reference Toxicnat')])
        badrows = dfwq.loc[(dfwq['species'].isin(['Eohaustorius estuarius','EE'])) & (dfwq['parameter'] == 'Total Ammonia') & (dfwq['result'] > 20)&(dfwq['matrix']!='Reference Toxicant')].index.tolist()
        toxwq_args.update({
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": badrows,
            "badcolumn": "result",
            "error_type": "Undefined Warning",
            "is_core_error": False,
            "error_message": "Water quality parameter for Total Ammonia not in acceptable range: must be less than 20."
        })
        warnings = [*warnings, checkData(**toxwq_args)]

        
        print(dfwq.loc[(dfwq['species'].isin(['Mytilus galloprovincialis','MG'])) & (dfwq['parameter'] == 'Dissolved Oxygen') & (dfwq['result'] < 4.0)])
        badrows = dfwq.loc[(dfwq['species'].isin(['Mytilus galloprovincialis','MG'])) & (dfwq['parameter'] == 'Dissolved Oxygen') & (dfwq['result'] < 4.0)].index.tolist()
        toxwq_args.update({
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": badrows,
            "badcolumn": "result",
            "error_type": "Undefined Warning",
            "is_core_error": False,
            "error_message": "Water quality parameter for Dissolved Oxygen not in acceptable range: must be greater than 4.0."
        })
        warnings = [*warnings, checkData(**toxwq_args)]
        
        
        print(dfwq.loc[(dfwq['species'].isin(['Mytilus galloprovincialis','MG'])) & (dfwq['parameter'] == 'pH') & ((dfwq['result'] < 7.6) | (dfwq['result'] > 8.3))])
        badrows = dfwq.loc[(dfwq['species'].isin(['Mytilus galloprovincialis','MG'])) & (dfwq['parameter'] == 'pH') & ((dfwq['result'] < 7.6) | (dfwq['result'] > 8.3))].index.tolist()
        toxwq_args.update({
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": badrows,
            "badcolumn": "result",
            "error_type": "Undefined Warning",
            "is_core_error": False,
            "error_message": "Water quality parameter for paramter pH not in acceptable range: must be between 7.6-8.3."
        })
        warnings = [*warnings, checkData(**toxwq_args)]
        
        #UPDATE: Jordan - Make sure all Species/SampleTypeCode groups have all parameters present in data.
        #        Jordan - Check that all water quality parameters are present at required time points (beginning and end of test and on an every-other-day basis in between)
        print("## Check that all water quality parameters are present at required time points ##")
        dfwq = pd.merge(
            toxwq[['timepoint','parameter','sampletypecode','toxbatch','tmp_row']], toxbatch[['species','toxbatch']],
            how = 'left',
            on='toxbatch'
        )
        print(dfwq)

        # Creates series that consists of sets of submitted parameters
        pgs = dfwq.groupby(['toxbatch','species','sampletypecode'])['parameter'].apply(set).reset_index()
        # Determines whether all appropriate parameters have been submitted
        pgs['missing'] = pgs.parameter.apply(lambda x: set(['Dissolved Oxygen', 'Salinity', 'Temperature', 'pH', 'Total Ammonia', 'Unionized Ammonia'])-x)
        # Provide Error for any missing parameters
        kk = pgs[pgs.missing != set()]
        for j in kk.index:
            badrows = toxbatch[(toxbatch.toxbatch == kk.toxbatch[j])&(toxbatch.species == kk.species[j])].tmp_row.tolist()
            toxbatch_args.update({
                "dataframe": toxbatch,
                "tablename": 'tbl_toxbatch',
                "badrows": badrows,
                "badcolumn": "toxbatch",
                "error_type": "Undefined Error",
                "is_core_error": False,
                "error_message": 'Associated water quality group %s/%s missing parameter(s): %s.' %(kk.species[j],kk.sampletypecode[j],list(kk.missing[j]))
            })
            errs = [*errs, checkData(**toxbatch_args)]

        pg = dfwq.groupby(['toxbatch','parameter','species','sampletypecode'])['timepoint'].apply(set).reset_index()
        # CORRECTION: For Total and Unionized Ammonia Parameters with species EE, only required to make measurements for 0,10. With species MG 0,2. 
        # For EE & Unionized or Total Ammonia (CNEG/GRAB/QA):
        p1 = pg[((pg.parameter == 'Total Ammonia')|(pg.parameter == 'Unionized Ammonia'))&(pg.species=='Eohaustorius estuarius')&((pg.sampletypecode=='CNEG')|(pg.sampletypecode=='Grab')|(pg.sampletypecode=='QA'))].timepoint.apply(lambda x: set([0,10])-x)
        # For EE & All other parameters (CNEG/GRAB/QA):
        p2 = pg[((pg.parameter != 'Total Ammonia')&(pg.parameter != 'Unionized Ammonia'))&(pg.species=='Eohaustorius estuarius')&((pg.sampletypecode=='CNEG')|(pg.sampletypecode=='Grab')|(pg.sampletypecode=='QA'))].timepoint.apply(lambda x: set([0,2,4,6,8,10])-x)
        # For EE & Unionized or Total Ammonia (Reference Toxicant):
        p3 = pg[((pg.parameter == 'Total Ammonia')|(pg.parameter == 'Unionized Ammonia'))&(pg.species=='Eohaustorius estuarius')&(pg.sampletypecode =='RFNH3')].timepoint.apply(lambda x: set([0,4])- x)
        # For EE & All other parameters (Reference Toxicant):
        p4 = pg[((pg.parameter != 'Total Ammonia')&(pg.parameter != 'Unionized Ammonia'))&(pg.species=='Eohaustorius estuarius')&(pg.sampletypecode =='RFNH3')].timepoint.apply(lambda x: set([0,2,4])- x)
        # For MG (ALL):
        p5 = pg[(pg.species=='Mytilus galloprovincialis')].timepoint.apply(lambda x: set([0,2])-x)
        # Concatenate to create field for missing timepoint values
        pg['missing'] = pd.concat([p1,p2,p3,p4,p5])
        # Provide Error for any missing timepoints
        print("Provide Error for any missing timepoints")
        k = pg[pg.missing != set()]
        print(k)
        for i in k.index:
            if k.sampletypecode[i] != 'CNSL':
                badrows = toxbatch[(toxbatch.toxbatch == k.toxbatch[i])&(toxbatch.species == k.species[i])].tmp_row.tolist()
                toxbatch_args.update({
                    "dataframe": toxbatch,
                    "tablename": 'tbl_toxbatch',
                    "badrows": badrows,
                    "badcolumn": "toxbatch",
                    "error_type": "Undefined Error",
                    "is_core_error": False,
                    "error_message": 'Associated water quality group %s/%s/%s is missing time points %s.' %(k.parameter[i],k.species[i],k.sampletypecode[i],list(k.missing[i]))
                })
                errs = [*errs, checkData(**toxbatch_args)]
    ## END WQ CHECKS ##
    ## END CUSTOM CHECKS ##
    
    
    
    
    ### SUMMARY TABLE START ###
    if len(errs) == 0:
        # summary must not be a groupby otherwise below functions wont work
        # all_dataframes[1] is the toxicity results data
        ### CRITICAL ALL VALUES IN THE RESULT FIELD MUST BE INTEGER TO RUN MEAN
        ### DONT RUN THIS) FUNCTION IF THERE ARE DATA TYPE ERRORS IN RESULT COLUMN
        print("Creating Toxicity Summary Results Table")
        print("Creating Toxicity Summary Results Table")
        #sql = "select tbl_grabevent.stationid,tbl_grabevent.latitude,tbl_grabevent.longitude,tbl_grabevent.stationwaterdepth,tbl_grabevent.stationwaterdepthunits,field_assignment_table.areaweight,field_assignment_table.stratum,tbl_grabevent.shape from field_assignment_table inner join tbl_grabevent on field_assignment_table.stationid = tbl_grabevent.stationid" - bug issue with grab returning multiple records per station moved statement to use occupation instead
        #sql = "select tbl_stationoccupation.stationid,tbl_stationoccupation.occupationlatitude as latitude,tbl_stationoccupation.occupationlongitude as longitude,tbl_stationoccupation.occupationdepth as stationwaterdepth,tbl_stationoccupation.occupationdepthunits as stationwaterdepthunits,field_assignment_table.areaweight,field_assignment_table.stratum,tbl_stationoccupation.shape from field_assignment_table inner join tbl_stationoccupation on field_assignment_table.stationid = tbl_stationoccupation.stationid"
        sql = "select tbl_stationoccupation.stationid,tbl_stationoccupation.occupationlatitude as latitude,tbl_stationoccupation.occupationlongitude as longitude,tbl_stationoccupation.occupationdepth as stationwaterdepth,tbl_stationoccupation.occupationdepthunits as stationwaterdepthunits,field_assignment_table.areaweight,field_assignment_table.stratum,tbl_stationoccupation.shape from field_assignment_table inner join tbl_stationoccupation on field_assignment_table.stationid = tbl_stationoccupation.stationid where tbl_stationoccupation.collectiontype = 'Grab' and tbl_stationoccupation.stationfail = 'None or No Failure'"
        print(sql)

        ### CRITICAL - SUMMARY TABLE CANNOT BE BUILT IF STATIONID SUBMITTED LACKS FIELD DATA (no grabevent data) - bug #7
        ### CHECK
        #df_sql = pd.read_sql_query(sql,eng)
        # lowercase column names
        #df_sql.columns = [x.lower() for x in df_sql.columns]
        #print(df_sql)
        #df_sql.drop_duplicates(subset=['stationid'], inplace=True)
        #print("DEBUGGING: search field stations against lab submission")	
        #get_unique_stations = result.groupby('stationid').apply(','.join)
        #print(result.loc[~result['stationid'].isin(df_sql['stationid'])])
        #no_field_stations = result.loc[~result['stationid'].isin(df_sql['stationid'])].stationid.tolist()
        #if len(summary_stations) >= 1:
        #	print("we have stations in results that arent in field table")
        #	print(summary_stations)
        #else:
        #	print("all stations match we can run toxicity summary")
        #	print(summary_stations)
        ### DONE CHECKING 
        ###
        #if not no_field_stations:
                    #df_match = pd.merge(result,df_sql, on=['stationid'], how='left')
        df_match = copy.deepcopy(toxresults)
        print(df_match.head())
        print(df_match.columns)
        print("Building Calculated Columns")
        def getCalculatedValues(grp):                                  
            grp['mean'] = grp[grp.result != -88]['result'].mean()
            #grp['n'] = grp['fieldreplicate'].sum() - bug n values was returning incorrect sum due to merge with grab table above
            grp['n'] = len(grp[grp.result != -88].index.tolist())
            grp['stddev'] = grp[grp.result != -88]['result'].std()
            grp['variance'] = grp['stddev'].apply(lambda x: x ** 2 )
            if grp['mean'].unique().item() != float(0):
                grp['coefficientvariance'] = ((grp['stddev']/grp['mean']) * 100)
            else:
                grp['coefficientvariance'] = 0
            return grp
        
        #summary = summary.groupby(['stationid','toxbatch','fieldreplicate']).apply(getCalculatedValues) - working - in beta no database though
        # doesnt check against database only results !IMPORTANT
        #summary = result.groupby(['stationid','toxbatch','fieldreplicate']).apply(getCalculatedValues)
        # checks against database merges with results stationid has to be in database !IMPORTANT

        grouping_columns = ['stationid','toxbatch','sampletypecode','samplecollectdate','treatment','concentration']
        #grouping_columns = ['stationid','toxbatch','sampletypecode','fieldreplicate']

        print("1 - who said print statements aren't debuggers?")
        print(list(df_match.groupby(grouping_columns)))
        toxsummary = df_match.groupby(grouping_columns).apply(getCalculatedValues)
        
        print("summary")
        print(toxsummary)

        print("2 - who said print statements aren't debuggers?")
        # get all control records
        cneg = toxsummary[grouping_columns + ['mean']].where(toxsummary['sampletypecode'] == 'CNEG')
        print("3 - who said print statements aren't debuggers?")
        # get all non control records
        nocneg = toxsummary[grouping_columns + ['mean']].where(toxsummary['sampletypecode'] != 'CNEG')

        # get all reference toxicant records just save them for now
        print("4 - who said print statements aren't debuggers?")
        reference_toxicants = toxsummary.loc[toxsummary['matrix'].isin(['Reference Toxicant'])]
        # drop all reference toxicants from the summary dataframe - not a part of summary results
        print("5 - who said print statements aren't debuggers?")
        summary = summary.loc[~summary['matrix'].isin(['Reference Toxicant'])]

        cneg = cneg.dropna()
        print("6 - who said print statements aren't debuggers?")
        nocneg = nocneg.dropna()
        print("7 - who said print statements aren't debuggers?")

        cneg['unique'] = np.nan
        nocneg['unique'] = np.nan

        print("8 - who said print statements aren't debuggers?")
        control_mean = cneg.groupby(grouping_columns + ['mean'])['unique'].nunique().reset_index()
        print("9 - who said print statements aren't debuggers?")
        result_mean = nocneg.groupby(grouping_columns + ['mean'])['unique'].nunique().reset_index()

        print("10 - who said print statements aren't debuggers?")
        control_mean_dict = control_mean.set_index('toxbatch')['mean'].to_dict()

        print("11 - who said print statements aren't debuggers?")
        # copy control_mean dataframe column mean to controlvalue
        control_mean['controlvalue'] = control_mean['mean']
        summary = toxsummary.merge(control_mean[['toxbatch','controlvalue']], how = 'left', on = ['toxbatch'])

        def getPctControl(row):
            ## toxbatch control should always be 100
            if(row['sampletypecode'] == 'CNEG'):
                row['pctcontrol'] = 100
            elif row['toxbatch'] in control_mean_dict:
                # if the toxbatch is in the lookup dictionary then
                # divide the result mean from the control mean and times by 100
                row['pctcontrol'] = ((row['mean']/control_mean_dict[row['toxbatch']]) * 100)
            else:
                row['pctcontrol'] = np.nan
            return row
        toxsummary = toxsummary.apply(getPctControl, axis=1)

        print("toxsummary")
        print(toxsummary.head())

        ## author - Tyler Vu
        def getPValue(summary):
            for index, values in summary['toxbatch'].iteritems():
                station_code = summary.ix[index, 'stationid']
                cneg_result = summary[['result']].where((summary['sampletypecode'] == 'CNEG') & (summary['toxbatch'] == values))
                result_both = summary[['result']].where((summary['toxbatch'] == values) & (summary['stationid'] == station_code) )
                #plus it was causing a critical and i dont know why
                cneg_result = cneg_result.dropna()
                result_both = result_both.dropna()
                t, p = stats.ttest_ind(cneg_result, result_both, equal_var = False)
                print("pvalue t: %s, p: %s" % (t,p))
                summary.ix[index, 'tstat'] = t
                single_tail = p/2
                #summary.ix[index, 'pvalue'] = p/2 #we divide by 2 to make it a 1 tailed
                summary.ix[index, 'pvalue'] = single_tail #we divide by 2 to make it a 1 tailed
                if (t < 0):
                    summary.ix[index, 'sigeffect'] = 'NSC'
                else:
                    if (single_tail <= .05):
                        summary.ix[index, 'sigeffect'] = 'SC'
                    else:
                        summary.ix[index, 'sigeffect'] = 'NSC'
        getPValue(toxsummary)
        print("done w getPValue")

        ## author - Tyler Vu 
        def getSQO(grp):
            #if(grp['species'] == 'EE'): - coded values
            if(grp['species'] == 'Eohaustorius estuarius'):
                if(grp['mean'] < 90):
                        if (grp['pctcontrol'] < 82):
                                if (grp['pctcontrol'] < 59):
                                        grp['sqocategory'] = 'High Toxicity'
                                else:
                                        if (grp['sigeffect'] == 'NSC'):
                                                grp['sqocategory'] = 'Low Toxicity'
                                        else:
                                                grp['sqocategory'] = 'Moderate Toxicity'
                        else:
                                if (grp['sigeffect'] == 'NSC'):
                                        grp['sqocategory'] = 'Nontoxic'
                                else:
                                        grp['sqocategory'] = 'Low Toxicity'
                else:
                        grp['sqocategory'] = 'Nontoxic'
            #elif (grp['species'] == 'MG'): - coded values
            elif (grp['species'] == 'Mytilus galloprovincialis'):
                if (grp['mean'] < 80):
                    if (grp['pctcontrol'] < 77):
                        if (grp['pctcontrol'] < 42):
                                grp['sqocategory'] = 'High Toxicity'
                        else:
                            if (grp['sigeffect'] == 'NSC'):
                                    grp['sqocategory'] = 'Low Toxicity'
                            else:
                                    grp['sqocategory'] = 'Moderate Toxicity'
                    else:
                        if (grp['sigeffect'] == 'NSC'):
                                grp['sqocategory'] = 'Nontoxic'
                        else:
                                grp['sqocategory'] = 'Low Toxicity'
                else:
                        grp['sqocategory'] = 'Nontoxic'
            return grp
        #print("calling getSQO")
        #summary = summary.apply(getSQO, axis=1)
        #print("print summary")
        #print(summary['sqocategory'])

        #summary.drop('result', axis=1, inplace=True)
        #summary.drop('labrep', axis=1, inplace=True)
        # group on the following columns and reset as a dataframe rather than groupby object
        #summary = summary.groupby(['stationid','lab','sampletypecode','toxbatch','species','concentration','endpoint','resultunits','sqocategory','mean','n','stddev','pctcontrol','sigeffect','qacode']).size().to_frame(name = 'count').reset_index()
        ### SUMMARY TABLE END ###
    
    
    
        ## SUMMARY TABLE CHECKS ##
        print("Starting Toxicity Summary Result Checks")
        toxsummary_args = {
            "dataframe": toxwq,
            "tablename": 'tbl_toxwq',
            "badrows": [],
            "badcolumn": "",
            "error_type": "",
            "is_core_error": False,
            "error_message": ""
        }
        # 1 - WARNING TO CHECK FOR DATA ENTRY ERRORS IF THE STANDARD DEVIATION FOR A SAMPLE EXCEEDS 50 
        print("## WARNING TO CHECK FOR DATA ENTRY ERRORS IF THE STANDARD DEVIATION FOR A SAMPLE EXCEEDS 50 ##")
        print(toxsummary.loc[(toxsummary["stddev"] > 50)])
        badrows = toxsummary.loc[(toxsummary["stddev"] > 50)].index.tolist()
        toxbatch_args.update({
            "dataframe": toxbatch,
            "tablename": 'tbl_toxbatch',
            "badrows": badrows,
            "badcolumn": "toxbatch",
            "error_type": "Undefined Error",
            "is_core_error": False,
            "error_message": 'Associated water quality group %s/%s/%s is missing time points %s.' %(k.parameter[i],k.species[i],k.sampletypecode[i],list(k.missing[i]))
        })
        errs = [*errs, checkData(**toxbatch_args)]

        # ## END SUMMARY TABLE CHECKS ##

        # ORGANIZE SUMMARY OUTPUT
        # results no database fields
        
        # with database fields
        # rename a few columns to match with existing b13 column names
        toxsummary.rename(columns={"resultunits": "units"}, inplace=True)
        # set p and tstat values if they are empty to -88
        toxsummary['tstat'].fillna(-88,inplace=True)
        toxsummary['pvalue'].fillna(-88,inplace=True)
        # group on the following columns and reset as a dataframe rather than groupby object
        print("summary start")

        # get summary dataframe with error columns before it is replaced - bug fix number 37 below for duplicate summary rows
        toxsummary = toxsummary.drop_duplicates(subset = ['stationid','toxbatch','fieldreplicate','pvalue'],keep='first')

        print("summary end")
        ## END SUMMARY TABLE CHECKS ##

   

    return {'errors': errs, 'warnings': warnings}
