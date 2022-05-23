import dill
import pymongo
import pandas as pd
from collections import defaultdict
from sklearn.preprocessing import OneHotEncoder,LabelEncoder
import numpy as np
import itertools
from collections import defaultdict
from scipy import stats
import Utility
import dataform_helper
import InsightFinding


#################################
# 1. compute dataset features
# 2. create enumerate vis 
#################################

### 已存在的dataInfo 進database###
def dataInfo2database(mycol):
    dataInfos_path = "..\\src\\data_infos\\dataInfos" #pre stored visualizations
    with open(dataInfos_path,'rb') as f:
        print("dataInfos exists!")        
        dataInfos = dill.load(f)

    print("dataInfo")

    new_list =[]
    for key,item in dataInfos.items():
        new_dict = {}
        new_dict['dataName'] = key
        new_dict['info'] = {
            'readFilePath':item['readFilePath'],
            'ID_col':item['ID_col'],
            'x_default':item['x_default'],
            'y_default':item['y_default'],
            'col_type':{
                'nominal':list(item['nominal']),
                'temporal':list(item['temporal']),
                'quantitative':list(item['quantitative']),
                }
        }
        new_list.append(new_dict)
    
    #mycol.delete_many({})
    mycol.insert_many(new_list)

    print("data")
    
############### dataset features #################
# set column unique value
# set one hot encoding
# set enumerate vis


def set_col_unique_value(dataName,raw_data_col,data_info_col):
    # get unique value of "nomial" and "temporal" features
    # colFeatures = {
    #      'month':[1,2,3,4,...12]
    # }
    data_document = data_info_col.find_one({"dataName":dataName})
    col_types = data_document["info"]["col_type"]
    data= pd.DataFrame(list(raw_data_col.find({})))
    
    # find unique key value
    col_unique_value = {}
    
    # nominal columns
    for col_name in col_types['nominal']:
        col_unique_value[col_name] = list(pd.unique(data[col_name]))

    # temporal columns
    for col_name in col_types['temporal']:
        if col_name == "invoice_month" or col_name == "invoice_day":
            data[col_name] = data[col_name].astype("int")
            col_unique_value[col_name] = [str(item)for item in sorted(list(pd.unique(data[col_name])))]
    col_unique_value["invoice_weekday"] = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    # update to database
    data_info_col.update(data_document,
                             {"$set":{"col_unique_value":col_unique_value}})
    
def set_encoding_to_type(dataName,data_info_col):    
    result = defaultdict(lambda:dict())
    
    document = data_info_col.find_one({"dataName": dataName})
    columns = [value for _,value in document["info"]["col_type"].items()]
    columns = list(itertools.chain(*columns))
    
    #LabelEncoder
    labelencoder = LabelEncoder()
    all_types = [col1+col2 for col1 in columns for col2 in columns]
    all_types_label = labelencoder.fit_transform(all_types)
    all_types_label = np.reshape(all_types_label,(-1,1))
        
    #one hot encoding 
    onehotencoder = OneHotEncoder()
    one_X = onehotencoder.fit_transform(all_types_label).toarray().tolist()

    # map encoding 
    result = dict(zip(all_types,one_X))
    # NA encoding
    noneType = [0]*len(list(one_X[0]))
    result[''] = noneType
    
    # getGroup to database
    data_info_col.update(document,{"$set":{"encoding_onehot":result}})
   
def getExpand2Type():
    return {'':[0,0,0],'drill_down':[1,0,0],'roll_up':[0,1,0],'comparison':[0,0,1]} 



################## visualization scope ###################
def enumerateVis(dataName,raw_data_col,data_info_col): # based on DeepEye P.8  # y不能是nomial
    
    enumerateVizs = []

    document = data_info_col.find_one({"dataName":dataName}) 
    q_cols = document["info"]["col_type"]['quantitative']
    n_cols = document["info"]["col_type"]['nominal']
    t_cols = document["info"]["col_type"]['temporal']

    # x is nominal
    if q_cols and n_cols:
        y_aggre = "mean"
        
        enumerateVizs.extend([dataform_helper.Vis(x=n_col,x_type='n',y=q_col,y_type='q',y_aggre=y_aggre,dataName=dataName) for n_col in n_cols for q_col in q_cols])
    
    # x, y are nominal
    if n_cols and (dataName=='police' or dataName=='Transaction'):
        enumerateVizs.extend([dataform_helper.Vis(x=n_col_x,x_type='n',y=n_col_x,y_type='n',y_aggre="cnt",globalAggre="per",dataName=dataName) for n_col_x in n_cols])

    # x is temporal
    if t_cols and q_cols:
        y_aggre = "mean"
        enumerateVizs.extend([dataform_helper.Vis(x=t_col,x_type='t',y=q_col,y_type='q',y_aggre=y_aggre,dataName=dataName) for t_col in t_cols for q_col in q_cols])
    
    # set vis features
    for i,vis in enumerate(enumerateVizs):
        vis.subgroup,vis.max_key,vis.min_key = dataform_helper.getGroup(vis.get_instance_attributes())
        vis.insights = InsightFinding.findExtreme(vis.get_instance_attributes())
        vis.is_root_vis = True
        vis.index = i
        Utility.setVisFeature(vis.get_instance_attributes(),True) 
        print("vis" , i)
        
    return enumerateVizs


def vis2database(visz,AQ_vis_col):
    for vis in visz:
        attrs = vis.get_instance_attributes()
        AQ_vis_col.insert_one(attrs)


dataName = "Transaction"

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["dataset"]
data_info_col = mydb["data_info"]
raw_data_col = mydb["TR_CH"]
AQ_vis_col = mydb["TR_vis"]
#raw_data_col = mydb["AQ_CH"]
#AQ_vis_col = mydb["AQ_vis"]

#dataInfo2database(data_info_col)
set_col_unique_value(dataName,raw_data_col,data_info_col)
#set_encoding_to_type(dataName,data_info_col)
#testvis = vis(x="weekDay",y="PM2_5(ug/m3)",x_type="n",y_type="q",dataName="AQ")
#getGroup(raw_data_col,data_info_col,testvis)
#AQ_vis_col.delete_many({})
visz = enumerateVis(dataName,raw_data_col,data_info_col)
vis2database(visz,AQ_vis_col)