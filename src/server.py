from flask import Flask,request,jsonify
import json
from itertools import chain
import VisRecommendation
import Utility
import database_interface
import dataform_helper

########### handle front/back end attrs #############
model = None
init_model_option = "" # scratch, pretrain, transfer, heuristic
init = True  #是否為新user
curr_data =''
curr_user_name = ''


app = Flask(__name__)

### init web ###
@app.route('/get_datasets',methods=['GET','POST'])
def get_datasets():
    if request.method == 'GET':
        dataset_names = database_interface.get_all_dataset_names()
        datasets= [{"name":name} for name in dataset_names]
        
    rst = jsonify(datasets)   
    rst.headers.add('Access-Control-Allow-Origin', '*')

    return rst,200

@app.route('/get_options',methods=['GET','POST'])
def get_options():
    global curr_data,model,init,init_model_option,curr_user_name
    if request.method == 'POST':
        get_data = json.loads(request.get_data())
        dataset_name = get_data['dataset_name']
        
        
        if init : 
            # Init model if a new user come
            curr_data = dataset_name
            init_model_option = get_data['init_model_option']

            if init_model_option == "scratch":
                print('Model from scratch: ',curr_data)
                model = None

            elif init_model_option == "pretrain":
                print("Model from pretrain: " ,curr_data)
                #model = tool.read_data('AQ_pretrain') if curr_data=="AQ"\
                #    else tool.read_data('Transaction_pretrain') if curr_data== "Transaction"\
                #    else None
                
            elif init_model_option == "heuristic":
                print("Model from heuristic(no model): " ,curr_data)
                model = None
            
            else:
                print("Unknown model status")
                model = None


            # create a new user log in db
            curr_user_name = database_interface.get_user_num()
            database_interface.create_new_user_log(curr_user_name)

            init = False
            
        
        else:
            # change dataset with the same user
            if dataset_name!=curr_data or init_model_option == "transfer":
                print("Model from transfer: " ,curr_data)

                # set model option
                curr_data = dataset_name 
                init_model_option = "transfer"
                database_interface.update_exploration_tree(model,curr_user_name,get_data)
        

    #set column options
    data = {}
        
    nominal_cols = database_interface.get_dataset_columns(dataset_name,'nominal')
    temporal_cols = database_interface.get_dataset_columns(dataset_name,'temporal')
    quan_cols = database_interface.get_dataset_columns(dataset_name,'quantitative')
    
    data['x_axis'] = [{'name':column}for column in nominal_cols+temporal_cols]
    data['y_axis'] = [{'name':column}for column in quan_cols]
    data['x_default'] = database_interface.get_axis_default(dataset_name,'x')
    data['y_default'] = database_interface.get_axis_default(dataset_name,'y')
    
    rst = jsonify(data)   
    rst.headers.add('Access-Control-Allow-Origin', '*')

    return rst,200


@app.route('/get_init_chart',methods=['GET','POST'])
def get_init_chart():
    global curr_data
    if request.method == 'POST':
        # get client data 
        get_data = json.loads(request.get_data())
        
        # find the same vis in the db
        vis = database_interface.get_vis_by_axis(curr_data,get_data['x'],get_data['y'])
        vis["par_vis"] = None

        # change the format to client chart.js
        data = dataform_helper.getChartData(vis)
    
    rst = jsonify(data)   
    rst.headers.add('Access-Control-Allow-Origin', '*')
    

    return rst,200

@app.route('/get_seq_data',methods=['GET','POST'])
def get_seq_data(): # data structure of the treant(tree structure) lib
    if request.method == 'POST':
        get_data = json.loads(request.get_data())
        data = get_data['data']

        if len(data)>0:
            node = {
                #'innerHTML': list(data.keys())[0],
                'innerHTML': "root",
                'pseudo': True,
            }
            stacks = [node]

            while(stacks):
                curr = stacks[-1]
                stacks.pop()
                
                if len(data[curr['innerHTML']])>0:
                    curr['connectors'] = {
                        "style":{
                            "stroke-width": 0.0
                        }
                    }
                    curr['children'] = [{'innerHTML':child} for child in data[curr['innerHTML']]]
                    stacks.extend(curr['children'])
        else:
            node = {}
            
    rst = jsonify(node)   
    rst.headers.add('Access-Control-Allow-Origin', '*')
    return rst,200


@app.route('/get_vis_rec',methods=['GET','POST'])
def get_vis_rec():
    global model,init_model_option
    data = {}
    
    if request.method == 'POST':
        get_data = json.loads(request.get_data())
        tree_vizs = get_data["chart_indices"]  # vis index of chart in the tree view
        clicked_vis = database_interface.get_vis_by_index(curr_data,int(get_data['chart_index']))
        userSelectedInsight = dataform_helper.getUserSelectedInsight(clicked_vis,get_data['click_item'])

        if not userSelectedInsight:
                userSelectedInsight={}
                userSelectedInsight['insightType'] = 'none',
                userSelectedInsight['key'] = get_data['click_item']
        
        if init_model_option != "heuristic":
            # no need to train model if the model option == heuristic 
            # train model based on the label_data

            if init_model_option == "transfer":
                
                train_x=[list(chain(*list(clicked_vis["features"].values())))]
                train_x,train_y = Utility.update_train_data(get_data['label_data'],curr_data,curr_user_name,train_x,[[0.0]])
                
                print('cross init feature length:',len(train_x))
                model,init_model_option = Utility.trainRegression(train_x,train_y,model,init_model_option)
            
            elif (len(get_data['label_data'])>1):
                #get training data
                train_x,train_y = Utility.update_train_data(get_data['label_data'],curr_data,user_name=curr_user_name)
                train_y = Utility.getDecayingLabel(train_y)

                #train model
                model,init_model_option = Utility.trainRegression(train_x,train_y,model,init_model_option)
            
        #get rec based on the regression model
        type1_visRec,type2_visRec, clicked_vis = VisRecommendation.getVisRec(curr_data,clicked_vis,userSelectedInsight,model,tree_vizs)
                 
        data['type1'] = [dataform_helper.getChartData(vis,rank=i+1) for i,vis in enumerate(type1_visRec)]
        data['type2'] = [dataform_helper.getChartData(vis,rank=i+1) for i,vis in enumerate(type2_visRec)]

    rst = jsonify(data)   
    rst.headers.add('Access-Control-Allow-Origin', '*')
    
    return rst,200

@app.route('/get_new_data',methods=['GET','POST'])
def get_new_data():  # modify aggre and sorting order based on option button in ui
    data = {}
    if request.method == 'POST':
        get_data = json.loads(request.get_data())
        index = int(get_data['chart_index'])
        aggre = get_data['aggre']
        sort = get_data['sort']
        vis = database_interface.get_vis_by_index(curr_data,index)

        # new sorted_group
        data["datas"] = []
        
        ### get new group based on new aggre
        subgroup = dataform_helper.group_by_aggre(vis,aggre) if (vis["x"] != vis["y"]) else vis["subgroup"]
        
        ### sorted based on the sort option
        if vis["x"] in database_interface.get_dataset_columns(curr_data,'nominal'):
            if sort == "desc":
                subgroup = dict(sorted(subgroup.items(),key=lambda x : x[1],reverse=True))
            elif sort == "asc":
                subgroup = dict(sorted(subgroup.items(),key=lambda x : x[1]))
        data["datas"].append(list(subgroup.values()))
        
        
        ### overall
        if vis["pre_vis"]:
            pre_subgroup = dataform_helper.group_by_aggre(vis["pre_vis"],aggre) if (vis["x"] != vis["y"]) else vis["pre_vis"]["subgroup"]
            data["datas"].append([pre_subgroup[key] for key in list(subgroup.keys())])
            
        
        # new aggre legend
        data["y"] = vis["y"] + '(' + aggre+')' if vis["y"]!=vis["x"] else "percentage of count",
        # sorted labels
        data["labels"] = list(subgroup.keys())

    
    rst = jsonify(data)   
    rst.headers.add('Access-Control-Allow-Origin', '*')

    return rst,200


@app.route('/change_user',methods=['GET','POST'])
def change_user():
    global model,init,curr_data
    if request.method == 'POST':
        get_data = json.loads(request.get_data())
        curr_data = get_data['dataset']
        
        #save data
        print('save tree structures')
        database_interface.update_exploration_tree(model,curr_user_name,get_data)

        # Reset variables
        for vis in database_interface.get_enumerate_vis(curr_data,isAll=True):
            database_interface.update_key(curr_data,vis,"par_vis",None)
            
        init = True
        model = None
    
    data ={}
    rst = jsonify(data)   
    rst.headers.add('Access-Control-Allow-Origin', '*')
    return rst,200

@app.route('/update_tr_data',methods=['GET','POST'])
def update_tr_data():
    if request.method == 'POST':
        get_data = json.loads(request.get_data())
        Utility.update_train_data(get_data['label_data'],curr_data,curr_user_name)
        
    rst = jsonify({})   
    rst.headers.add('Access-Control-Allow-Origin', '*')
    
    return rst,200


@app.route('/update_dataset',methods=['GET','POST'])
def update_dataset():
    global model,curr_user_name
    if request.method == 'POST':
        get_data = json.loads(request.get_data())
        database_interface.update_exploration_tree(model,curr_user_name,get_data)
    
    data ={}
    rst = jsonify(data)   
    rst.headers.add('Access-Control-Allow-Origin', '*')
    return rst,200



if __name__ == "__main__":
    app.run()
    #app.run(debug=True,port=5000)
    #app.run(host="192.168.0.1",port=5010) #設定特定的IP