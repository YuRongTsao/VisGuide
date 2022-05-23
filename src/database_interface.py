import pymongo 
import pickle

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["dataset"]

data_info_col = mydb["data_info"]
AQ_raw_data_col = mydb["AQ_CH"]
AQ_vis_col = mydb["AQ_vis"]
TR_raw_data_col = mydb["TR_CH"]
TR_vis_col = mydb["TR_vis"]
explore_records = mydb["explore_records"]

############################
##### data_info column######
############################
def get_all_dataset_names():
    return [item["dataName"]  for item in list(data_info_col.find({}))]

def get_axis_default(dataName,axis):
    document = data_info_col.find_one({"dataName": dataName})
    return document["info"]['x_default'] if axis=="x" else document["info"]['y_default']
    
def get_dataset_columns(dataName,col_type):
    return list(data_info_col.find_one({"dataName": dataName})["info"]["col_type"][col_type])

def get_dataset_hierarachy(dataName):
    return dict(data_info_col.find_one({"dataName": dataName})["hierarchy"])

def get_dataset_expand2type(dataName):
    return dict(data_info_col.find_one({"dataName": dataName})["expand2type"])

def get_dataset_encoding2type(dataName):
    return dict(data_info_col.find_one({"dataName": dataName})["encoding_onehot"])

#########################
#### raw data column ####
#########################

def get_row_data_col(dataName):
    if dataName == "AQ":
        return AQ_raw_data_col
    elif dataName == "Transaction":
        return TR_raw_data_col

####################
#### vis column ####
####################
def update_key(dataName,vis,key,value):
    if dataName == "AQ":
        vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col
        
    vis_col.update_one(vis_col.find_one({"index":vis["index"]}),{"$set":{key:value}})

def update_document(dataName,vis):
    if dataName == "AQ":
        vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col
        
    vis_col.update_one(vis_col.find_one({"index":vis["index"]}),{"$set":vis})

def insert_new_vis(dataName,vis):
    if dataName == "AQ":
        vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col

    vis_col.insert_one(vis)

def get_db_vis_idx(dataName):
    if dataName == "AQ":
        vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col
        
    return vis_col.count()

def get_enumerate_vis(dataName,isAll=False,isRoot=False):
    if dataName == "AQ":
        vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col
    
    if isAll:
        return list(vis_col.find({}))
    else:
        return list(vis_col.find({"is_root_vis":True}) if isRoot else vis_col.find({"is_root_vis":False}))
    

def get_visz_by_query(dataName,query):
    if dataName == "AQ":
            vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col
    
    return vis_col.find(query)

def get_vis_by_axis(dataName,x,y,filter={}):
    if dataName == "AQ":
        vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col
        
    return vis_col.find_one({"x":x,"y":y,"filter":filter})

def get_vis_by_index(dataName,index):
    if dataName == "AQ":
        vis_col = AQ_vis_col
    elif dataName == "Transaction":
        vis_col = TR_vis_col
        
    return vis_col.find_one({"index":index})


#############################
#### exploration records ####
#############################
def get_user_num():
    return explore_records.count()

def create_new_user_log(user_name):
    new_log = {
        "user_name": user_name,
        "exploration": {},
        "train_x": [],
        "train_y": [],
    }
    explore_records.insert_one(new_log)

def update_user_train_data(user_name,train_x,train_y):
    user_log = explore_records.find_one({"user_name":user_name})
    explore_records.update_one(user_log,{"$set":{"train_x":train_x,"train_y":train_y}})
    
def get_user_train_data(user_name):
    doc = explore_records.find_one({"user_name":user_name})
    return doc["train_x"],doc["train_y"]

def update_user_log(user_name,key,value):
    user_log = explore_records.find_one({"user_name":user_name})
    explore_records.update_one(user_log,{"$set":{key:value}})
    
def update_exploration_tree(model,curr_user_name,get_data=None):
    #store tree structure and model
    if get_data!=None and len(list(get_data.keys()))>3:
        update_user_log(curr_user_name,"store_structure",get_data["store_structure"])
        update_user_log(curr_user_name,"store_label_data",get_data["store_label_data"])
        update_user_log(curr_user_name,"store_chart_data",get_data["store_chart_data"])

        print('save curr model:',get_data["store_dataset"])
        save_model(model,"model//"+ get_data["store_dataset"]+"_"+str(curr_user_name))
        
        
##### local save model ####
def save_model(model,filepath):
    with open(filepath,"wb")as f:
        pickle.dump(model,f)
        