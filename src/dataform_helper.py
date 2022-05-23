import pandas as pd
import database_interface

#### client server data transform ###
def getChartData(vis,rank = 0): # for client front end chart.js
    values = list(vis["subgroup"].values())
    keys = list(vis["subgroup"].keys())
    label = 'Overall' if len(vis["filter"]) == 0 else ', '.join([key+':'+ str(value) for key,value in vis["filter"].items()])
    data = {
        'x':vis["x"],
        'y':vis["y"] + '(' + vis["y_aggre"]+')' if vis["y"]!=vis["x"] else "percentage of count",
        'y_glo_aggre':vis["globalAggre"],
        'type':vis["mark"],
        'labels':keys,
        'datas':[
            {
                'data':values,
                'label':label,      
            },
        ],
        'chart_index': [vis["index"]],
        'label':0,
        'rank':rank,
        'otherInfo':{},
        'rec':{},
        'is_selected':False,
        'insights': {insight["key"]:insight["insightType"] for insight in vis["insights"]},
        'filters':{key:[value] for key,value in vis["filter"].items()},           
        'expandType': vis["expandType"],
        'aggre':"avg" if vis["y_aggre"]=="mean" else vis["y_aggre"],
        'sort':'desc',
        'multiple_yAxes':False
    }
    
    if vis["pre_vis"] and vis["x"] == vis["pre_vis"]["x"] and vis["y"] == vis["pre_vis"]["y"]:
        data["multiple_yAxes"] = True
        data['datas'].append({
            'data': list(vis["pre_vis"]["subgroup"].values()),
            'label' : 'Overall'            
        })

    return data


def getGroup(vis):
    # group = {
    #   '2014': 10,
    #   '2015':20
    # }
        
    # get group based on filter and x-encoing, y-encoding
    raw_data_col = database_interface.get_row_data_col(vis["dataName"])
    data_info_col = database_interface.data_info_col
    
    data = pd.DataFrame(raw_data_col.find(vis["filter"])) # filter 

    # sort x-axis value    
    order = data_info_col.find_one({"dataName":vis["dataName"]})['col_unique_value'][vis["x"]]
    data[vis["x"]] = pd.Categorical(data[vis["x"]], categories = order)
    data.sort_values(vis["x"],inplace=True)

    # aggregate values
    if vis["y_aggre"]=='cnt':
        group = data[vis["x"]].value_counts()
        group = (group/group.agg(sum)).round(2) # compute the percentage
    else:
        group = data.groupby([vis["x"]])[vis["y"]].agg(vis["y_aggre"]) #aggregate
        group.dropna(inplace=True) 
        group.fillna(group.agg("mean"),inplace=True)
        group = (group/group.agg(sum)*100).round(2) if vis["globalAggre"] == 'per' else group.round(2) # percentage
    
    
    return group.to_dict(),group.idxmax(),group.idxmin()


def group_by_aggre(vis,aggre):
    raw_data_col = database_interface.get_row_data_col(vis["dataName"])

    # get group based on filter and x-encoing, y-encoding
    data = pd.DataFrame(raw_data_col.find(vis["filter"])) # filter 

    # aggregate values
    group = data.groupby([vis["x"]])[vis["y"]].agg(aggre) #aggregate
    group.dropna(inplace=True) 
    group.fillna(group.agg("mean"),inplace=True)
    
    group = (group/group.agg(sum)*100).round(2) if vis["globalAggre"] == 'per' else group.round(2) # percentage

    return dict(group)


def default_selected_insight(curr_vis):
    for insight in curr_vis["insights"]:
        if insight['insightType']=='max':
            return insight

         
def getUserSelectedInsight(vis,insight_key): 
    for insight in vis["insights"]:
        if str(insight['key']) == str(insight_key):
            return insight
    return None


######### visualization's data structure #########
class Vis():
    def __init__(self,x='',x_type='',y='',y_type='',y_aggre='mean',dataName='',mark='',order='',bin='',filter={},globalAggre='',index=0,autoSetVisInfo=True):
        
        # visualization information
        self.dataName = dataName
        self.x = x
        self.x_type = x_type
        self.y = y
        self.y_type = y_type
        self.y_aggre = y_aggre
        self.globalAggre = globalAggre
        self.mark = self.setMark() if mark== '' else mark
        self.filter = filter
        self.subgroup = {}
        self.max_key = ''
        self.min_key = ''
        self.index = index
        self.pre_vis = None # 算IG的 (reference vis)
        self.par_vis = None # sequence parent
        
        # visualization features (static)
        self.insights = []
        
        # visualization features (dynamic)
        self.features = {}
        self.filter_percent =0.0
        self.expandType = '' # 1: drill down , 2: comparison
        self.insightType = ''
        self.edgeValue = 0.0
        self.euclidean = 0.0
        
        # tree structure
        self.children ={}
        self.pilot_children =[]
        self.pilot_parents =[]
        self.is_root_vis = False
        
    def setMark(self):
        if self.x_type == "n" and self.y_type == "q":
            return "bar" 
        elif self.x_type == "t" and self.y_type == "q":
            return "line"
        elif self.x_type == "n" and self.y_type == "n":
            return "doughnut"
        else: 
            return "bar"

    def get_instance_attributes(self):
        print('[instance attributes]')
        attrs = {attribute: value for attribute, value in self.__dict__.items()}
        return attrs
    
    
