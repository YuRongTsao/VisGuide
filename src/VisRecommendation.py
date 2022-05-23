import Utility
import InsightFinding
import database_interface
import dataform_helper

def set_exist_vis(vis,expandType,dataName,clicked_vis_idx,insightType):
    vis["expandType"] = expandType
    vis["par_vis"] = database_interface.get_vis_by_index(dataName,clicked_vis_idx)
    vis["insightType"] = insightType
    
    Utility.setVisFeature(vis,vis["is_root_vis"])  
                    
    # update to db
    database_interface.update_document(dataName,vis)
    
    return vis


def set_new_vis(vis,expandType,dataName,clicked_vis_idx,insightType,new_vis_idx):
    vis["subgroup"],vis["max_key"],vis["min_key"] = dataform_helper.getGroup(vis)
    vis["insights"] = InsightFinding.findExtreme(vis)
    vis["pre_vis"] = database_interface.get_vis_by_axis(dataName,vis["x"],vis["y"])
    vis["insights"].extend(InsightFinding.findDifDistribution(vis,vis["pre_vis"]))
    vis["is_root_vis"] = False
    vis["index"] = new_vis_idx
                
    # set vis features (relate to exploration order)
    vis["par_vis"] = database_interface.get_vis_by_index(dataName,clicked_vis_idx)
    vis["insightType"] = insightType
    vis["expandType"] = expandType
    Utility.setVisFeature(vis,vis["is_root_vis"])  
                
    # push in db (only data)
    del vis['_id']
    database_interface.insert_new_vis(dataName,vis)
                
    return vis


def getExpandVizs(dataName,clicked_vis,userSelectedInsight,tree_vizs):

    # get the candidates based on the expend rule
    if clicked_vis["y_aggre"] == "cnt": 
        type1_candVizs = database_interface.get_visz_by_query(dataName,{"x":{"$ne" : clicked_vis["x"]},
                                                                        "filter":clicked_vis["filter"]}) #diff x, no limit y, the same filter
    else:
        
        type1_candVizs = database_interface.get_visz_by_query(dataName,{"x":{"$ne" : clicked_vis["x"]},
                                                                        "y":clicked_vis["y"],
                                                                        "filter":clicked_vis["filter"]}) #diff x, same y
        
    type2_filter = clicked_vis["filter"] if clicked_vis["filter"]=={} else {"$ne":clicked_vis["filter"]}
    type2_candVizs = database_interface.get_visz_by_query(dataName,{"x":clicked_vis["x"],
                                                                    "y":{"$ne":clicked_vis["y"]},
                                                                    "filter":type2_filter}) #diff y, same x
        
    
    
    
    type1_results=[]
    type2_results=[]
    
    if userSelectedInsight == '':
        userSelectedInsight = dataform_helper.default_selected_insight(clicked_vis)

    new_vis_idx = database_interface.get_db_vis_idx(dataName)

    # type 1 expand
    for vis in type1_candVizs:
        # add new filter 
        vis["filter"][clicked_vis["x"]]=userSelectedInsight['key']
                  
        # check if the vis is alrealy in the db  
        same_vis = database_interface.get_vis_by_axis(dataName,vis["x"],vis["y"],vis["filter"])
            
        if same_vis and same_vis["index"] not in tree_vizs:
            # set the same vis
            same_vis = set_exist_vis(same_vis,"1",dataName,clicked_vis["index"],userSelectedInsight['insightType'])
            type1_results.append(same_vis)

        else:
            # set new vis
            vis = set_new_vis(vis,"1",dataName,clicked_vis["index"],userSelectedInsight['insightType'],new_vis_idx)
            new_vis_idx+=1
            type1_results.append(vis)
            
            
    # type 2 expand 
    for vis in type2_candVizs:
        # check if the vis is alrealy in the db  
        vis["filter"] = clicked_vis["filter"]
        same_vis = database_interface.get_vis_by_axis(dataName,vis["x"],vis["y"],vis["filter"])
        
        
        if same_vis:
            # set the same vis
            type2_results_idx = [int(vis["index"]) for vis in type2_results]
            if same_vis["index"] not in tree_vizs and same_vis["index"] not in type2_results_idx:
                same_vis = set_exist_vis(same_vis,"2",dataName,clicked_vis["index"],userSelectedInsight['insightType'])
                type2_results.append(same_vis)
                
        else:
            # set new vis
            vis = set_new_vis(vis,"2",dataName,clicked_vis["index"],userSelectedInsight['insightType'],new_vis_idx)
            new_vis_idx+=1
            type2_results.append(vis)
            
        
    return type1_results,type2_results

 
def getVisRec(dataName,clicked_vis,userSelectedInsight,regressionModel=None,tree_vizs=[]): #return top 10 recommendation []
    
    type1_rec_cand,type2_rec_cand =  getExpandVizs(dataName,clicked_vis,userSelectedInsight,tree_vizs) 

    #compute type1 recommendation predictive value(edge values)
    if len(type1_rec_cand)!=0:
        edgeValues = Utility.edgeValue(type1_rec_cand,regressionModel)
        for i,vis in enumerate(type1_rec_cand):
            vis["edgeValue"] = edgeValues[i]
        
    #compute type1 recommendation predictive value(edge values)
    if len(type2_rec_cand)!=0:
        edgeValues = Utility.edgeValue(type2_rec_cand,regressionModel)
        for i,vis in enumerate(type2_rec_cand):
            vis["edgeValue"] = edgeValues[i]
    
    # sorting based on the predictive value, which is the rank of the recommendations 
    type1_rec_cand.sort(key = lambda curr_vis:curr_vis["edgeValue"],reverse=True)
    type2_rec_cand.sort(key = lambda curr_vis:curr_vis["edgeValue"],reverse=True)
        

    clicked_vis["children"]['type1'] = type1_rec_cand
    clicked_vis["children"]['type2'] = type2_rec_cand

    return type1_rec_cand,type2_rec_cand,clicked_vis

    
       