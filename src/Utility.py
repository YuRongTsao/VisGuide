from itertools import chain
import math
import operator
import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.spatial.distance import euclidean
from sklearn import linear_model
from scipy import stats

import database_interface

########################################### 
############# vis features ################
###########################################
def setVisFeature(curr_vis,isRoot=False):
    if isRoot:
        curr_vis["features"]['IS'] = [insightSig(curr_vis)]    
        curr_vis["features"]['IG'] = [0]
        curr_vis["features"]['expandType'] = [0,0,0]
        curr_vis["features"]['expandConsis'] = [0]
        curr_vis["features"]['X_encodingType'] = encodingType(curr_vis,curr_vis["par_vis"],'x')
        curr_vis["features"]['Y_encodingType'] = encodingType(curr_vis,curr_vis["par_vis"],'y')
    else:
        curr_vis["features"]['IS'] = [insightSig(curr_vis)]    
        curr_vis["features"]['IG'] = [infoGain(curr_vis,curr_vis["pre_vis"])]
        curr_vis["features"]['expandType'] = expandType(curr_vis,curr_vis["par_vis"])
        curr_vis["features"]['expandConsis'] = [expandConsis(curr_vis)]
        curr_vis["features"]['X_encodingType'] = encodingType(curr_vis,curr_vis["par_vis"],'x')
        curr_vis["features"]['Y_encodingType'] = encodingType(curr_vis,curr_vis["par_vis"],'y')
        curr_vis["euclidean"] = Euclidean(curr_vis,curr_vis["pre_vis"])

def insightSig(curr_vis):
    sigs = [insight['sig'] for insight in curr_vis["insights"]]
    return 1-min(sigs)

def infoGain(curr_vis,pre_vis):
    ### KL divergence , 越大越好
    try:
        curr_values = curr_vis["subgroup"].values()
        pre_values = pre_vis["subgroup"].values()

        dist = jensenshannon(curr_values, pre_values ,2) # do normalize to the distribution # bound (0,1)
    except:
        return 0.0
    return dist

def expandType(curr_vis,par_vis):
    curr_data = curr_vis["dataName"] 
    hierarchy = database_interface.get_dataset_hierarachy(curr_data)
    expand2type = database_interface.get_dataset_expand2type(curr_data)

    if curr_vis["expandType"]=='1':  # drill down 
        try:
            curr_expand_type = hierarchy[curr_vis["x"]][par_vis["x"]] 
        except:
            curr_expand_type = ''
        
        return expand2type[curr_expand_type]
    elif curr_vis["expandType"]=='2':  #comparison
        return expand2type['comparison']
    else:
        return expand2type['']
 

def expandConsis(curr_vis):
    curr_expand_type = curr_vis["features"]['expandType']
    has_par = True
    totalEdges = 0
    match = 0
    
    while(has_par):
        if curr_vis["par_vis"] != None:
            if curr_vis["par_vis"]["features"]['expandType'] == curr_expand_type:
                match+=1       
            totalEdges += 1 
            curr_vis = curr_vis["par_vis"]
        else:
            has_par = False

    return match / totalEdges if totalEdges !=0 else 1

def encodingType(curr_vis,par_vis,channel):
    
    encoding2type = database_interface.get_dataset_encoding2type(curr_vis["dataName"])
    if par_vis == None:
        return encoding2type['']
    else:
        if channel=='x':
            return encoding2type[str(par_vis["x"]+curr_vis["x"])]  
        else:
            return encoding2type[str(par_vis["y"]+curr_vis["y"])]  

def Euclidean(curr_vis,pre_vis):
    try:
        curr_values = curr_vis["subgroup"].values()
        pre_values = pre_vis["subgroup"].values()
        dist = euclidean(np.array(curr_values),np.array(pre_values))
    except:
        return 0.0
    return dist



def update_train_data(label_data,curr_data,user_name,train_x=None,train_y=None):
    
    if train_x==None: 
        # get old train data
        train_x,train_y = database_interface.get_user_train_data(user_name)
        
        #extend new train data
        visLabeled = [database_interface.get_vis_by_index(curr_data,int(idx)) for idx in label_data.keys()]        
        train_x.extend(list(map(lambda vis : list(chain(*list(vis["features"].values()))),visLabeled)))
        train_y.append(list(map(lambda y:float(y),list(label_data.values()))))
        
    # udpate to db
    database_interface.update_user_train_data(user_name,train_x,train_y)
    
    print("update training data, num of records = " + str(len(train_x)))
    
    return train_x,train_y




###########################################     
############# label management ############
###########################################
def getDecayingLabel(train_y):
    #train_y = [[],[],[]...]
    #只留前5個
    duration = 5 
    decay_rate = 0.9
    threshold = len(train_y) - duration
    result = []

    for i,labels in enumerate(train_y):
        diff = i-threshold
        if diff<0:
            result.extend(list(map(lambda label:label * math.pow(decay_rate,abs(diff)),labels)))
        else:
            result.extend(labels)
    return result




###########################################
############ model training ###############
###########################################
def trainRegression(train_X,train_y,model,init_model_option):
    X =  np.reshape(train_X, (len(train_X), len(train_X[0])))
    y = np.array(train_y)

    if init_model_option == "scratch":
        print("From scratch init model , len (y) = " , len(y))
        regressionModel = linear_model.SGDRegressor(max_iter=1000, tol=1e-3,warm_start=True).fit(X, y) 
        init_model_option = ""

    elif init_model_option == "transfer":
        regressionModel = linear_model.SGDRegressor(max_iter=1000, tol=1e-3,warm_start=True).fit(X, y)
        init_model_option = ""

        # transfer first 4 features (len==6)
        pre_weight_len = 6
        coef_old = list(model.coef_)
        coef_new = list(regressionModel.coef_)
        coef = coef_old [:pre_weight_len]
        coef.extend([0]*(len(coef_new)-pre_weight_len))
        regressionModel.coef_ = np.array(coef)
        
        print('new_coef:',len(regressionModel.coef_))
        print('old_coef:',len(model.coef_))
        print('Init Transfer model, len (y) = ', len(y))

    else:
        print('Train regression, len (y) = ', len(y))
        regressionModel = model.fit(X, y) 
        
    return regressionModel,init_model_option


###########################################
############ prediction ###################
###########################################

def edgeValue(rec_cand,regressionModel=None):
    for curr_vis in rec_cand:
        setVisFeature(curr_vis) 
    features = list(map(lambda vis:list(chain(*list(vis["features"].values()))),rec_cand)) 

    if regressionModel == None:
        # same fixed weight to features
        edgeValues = [sum(feature) for feature in features]
        return edgeValues
    else:
        # transfer model
        if len(list(regressionModel.coef_)) != len(features[0]): 
            weights = list(regressionModel.coef_)[:6]
            weights.extend([0.1 for i in range(len(features[0])-6)])
            edgeValues = [sum(map(operator.mul,weights,feature)) for feature in features]
        # model exist and predict
        else:
            edgeValues = regressionModel.predict(features)
        return edgeValues


