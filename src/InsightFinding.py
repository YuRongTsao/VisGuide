# Input : raw data
# Function
#   1.detect column type 
#   2.enumerate combination
#   3.insight detection functions

from scipy import stats

annotations = {
    'max' : '%s has the highest value %.2f for %s of %s ',
    'min' : '%s has the lowest value %.2f for %s of %s ',
    'increase' : '+ %.2f'
}

# find features
def findExtreme(vis):
    #找最大值 + z score
    if len(vis["subgroup"]) ==0:
        return None
    
    keys = list(vis["subgroup"].keys())
    values = list(vis["subgroup"].values())
    
    if len(values)>2:
        zScore = stats.zscore(values)
        pValues = list(map(lambda k : stats.norm.sf(abs(k))*2,zScore))
    else:
        p_value = 1-((max(values) - min(values)) / sum(values)) if sum(values)!=0 else 1
        pValues = [p_value,p_value]

    pValues = dict(zip(keys,pValues))
    
    # find max value in a vis and record it's key name
    obj1 = {'tag':0,'insightType':'max','key':vis["max_key"],'value':vis["subgroup"][vis["max_key"]],'sig' : pValues[vis["max_key"]]}
    obj2 = {'tag':1,'insightType':'min','key':vis["min_key"],'value':vis["subgroup"][vis["min_key"]],'sig' : pValues[vis["min_key"]]}
    
    return  [obj1,obj2]

def findDifDistribution(curr_vis,pre_vis):
    #有不一樣的地方就算insight (標比例有增加的地方)
    curr_subgroup = curr_vis["subgroup"]
    pre_subgroup = pre_vis["subgroup"]
    insights = []
    isInInsight = False

    curr_sum = sum(curr_subgroup.values())
    pre_sum = sum(curr_subgroup.values())

    for key in curr_subgroup.keys():
        if curr_sum!=0 and pre_sum!= 0: 
            curr_per = curr_subgroup[key] / curr_sum #先換成百分比再算增加的比例
            pre_per = pre_subgroup[key] / pre_sum

            if curr_per > pre_per:  
                value = round((curr_per-pre_per),4)
                if value >= 0.05:
                    #check if a bar insight is exit
                    for insight in curr_vis["insights"]:
                        if key == insight['key']: 
                            isInInsight = True 
                            break
                    if not isInInsight:
                        p_value = 1-value        
                        annotation = annotations['increase'] % (value*100) + '%' if curr_vis["globalAggre"] =='per' else annotations['increase'] % (value)
                        insights.append({'tag':2,'insightType':'increase','key':key,'value':value,'description' : annotation,'sig' : p_value})
    
    return insights

    






