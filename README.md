# VisGuide: Creating Visualization Trees with User-oriented Recommendations

## Introduction
**Data stories** are increasingly popular as a means for representing and organizing observations and patterns extracted from raw data. 

Previous works proposed the use of **visualization sequences** to represent data stories, using heuristics to automatically arrange charts in a meaningful order. While this approach performs well in specific scenarios, it has some limitations:

* The limitation of the diversity and the flexibility of the output visualization sequences.
* It does not customize the generated sequences to individual users' preferences
* Most of the existing methods arrange charts with a linear, tile or tree layout. For those layout types, their lack of a notion of extended branches requires considerable more effort from users to grasp the overall context spanning multiple charts.

We proposed **VisGuide**, an interactive visualization tree generation tool that helps users create coherent visualization trees by recommending meaningful charts tailored to each user's data-exploration preferences. 

The contributions of VisGudie:

* It is an interactive data exploration environment with recommendations to help users iteratively organize multiple visualizations into a visualization tree
* It  provides user-oriented recommendations using an online learning method that considers data statistics, visualization relations, and user preferences
* It effectively uses a novel tree format, *ViStory Tree*, to support a systematic  presentation of the complex relations among multiple visualization sequences

## User Interface
<p align="center">
  <img src="./img/interface.png">
</p>

### (1)Tree View 
Presents the generated visualization trees.
### (2)Recommendation View
Shows the next chart recommendations of the user-focused chart (Chart C). There are **Drill-down** and **Comparison** two types of the recommendation.
### (3)Sheet Management Bar
Supports users to create multiple visualization trees by adding a new sheet. Users can also switch among the sheets to compare the explored results.

[DEMO VIDEO](https://drive.google.com/file/d/1l28CLZgooxq0PeRy9tMNBYdWOQl_s5R9/view?usp=sharing)

## Method
### System Overview
<p align="center">
  <img src="./img/overview.png" >
</p>

The system consists of two groups of components: a **user interface** and a **recommendation system**.

The **user preference feedback module:** will collect a user's preferences to charts based on his/her interaction with the system and thus get a set of labeled charts. **Chart selection module:** allows users to show their further exploration intentions by clicking on their interested data points in charts (user-focused charts). This action will also trigger VisGuide's recommendation generation process. The recommendation system then uses the user-clicked information about the user-focused chart to generate a set of **candidates of next charts**. Besides, the labeled set of charts generated from the **user preference feedback module** will be used to **train users' preference model**. Afterwards, the recommendation system will predict the preference score of each candidate chart using the users' preference model. VisGuide then presents these charts in a descending order of preference score in the Recommendation View of the user interface.

The selected charts are arranged in a **ViStory Tree**, with which the user can intuitively organize them into a systematic presentation of the structure and patterns of a data story. The above procedures will be repeated to form a insightful visualization tree.

### User Preference Feedback
Users' chart preferences are acquired from their interactions with the system, and the preference score of a chart will be treated as the labeled information, which will be used to train the preference model.

The preference score is a four-level numeric score from 0 to 1:
* Users click the **Star** button: this chart will get score 0.3.
* Users add a chart from the \textit{Recommendation View} to the \textit{Tree View}: this chart will get score 0.6.
* Users click the **Heart** button: this chart will get score 1.0.
* Any chart that is neither selected nor labeled: this chart will get score 0.0. 

### Candidate Chart Generation
To arrive at human-comprehensible sequences of interesting data subsets, VisGuide applies **Drill-down** and **Comparison** operations to the user-focused chart to generate candidate next charts. 

* Drill-down: it combines the original idea of the drill-down operation and the hierarchical structuring, which in effect zooms in to a data subset of interest by applying a user-clicked data point as a filter condition. Its output comprises candidate charts that share the same Y-axis attribute (i.e., measure) but differ from the current chart in their X-axis attributes. For example, Chart D in Figure 1. is a drill-down chart of Chart A.

* Comparison: it is designed also based on the hierarchical structuring, which facilitates users' own comparisons of different measures in the same data subset by generating comparison charts that share the same X-axis and filter values, but differ from the current chart in terms of their Y-axis attributes. For example, Chart B in Figure 1. is a comparison chart of Chart A.

### User Preference Model Training
VisGuide's user preference model is a linear regression model of chart features that is trained online during a user's interaction processes and transferred when the user explores a new dataset. 

**Chart features**:
* (F1) Insight Significance measures: the magnitude of insights in a chart. In this work, we only consider the point insights, e.g. extreme value
* (F2) Deviation: measures the difference between the probability distribution of a recommended candidate chart and that of the reference chart. We use Jensen-Shannon divergence (JSD) to measure the difference of two distributions. Among the candidate charts, the one with larger JSD value is considered more interesting.
* (F3) Granularity: A visualization sequence is more understandable if the charts in the sequence present the data from general to specific or reversely. The granularity feature quantifies the degree of such transitions (e.g., general-to-specific or specific-to-general) from one chart to its following recommended candidate charts. 
* (F4) Consistence of generation operations: A visualization sequence is considered more contextual if the generation operation (i.e., drill-down or comparison) of more transitions in the sequence are the same. This feature calculates the proportion of transitions in the sequence having the same generation operation. 
* (F5) Encoding Transitions: We record the channel encoding transition between two charts to capture a user's preference on the transition of the attributes. For example, if the $X$ channel attribute of the parent chart is *City* and that of its children chart is *Station*, the value of the feature *X-Encoding-Change* will be `City2Station`.

**Linear Regression Model:**

A user-oriented recommendation has two aspects: 
* (1) Capture the user preference on the data and the relation among visualizations
* (2) Bring along the learned user preferences on one dataset to a new dataset. 

To this end, we adopt an online machine learning method to learn users' personal preference model. We use the **stochastic gradient descent (SGD)** method to train a linear regression model that can capture the importance of each chart feature to different users by learning a user-oriented set of feature weights. This model is then used as the utility function to predict a particular user's preference score for each candidate chart. We define the utility function of a visualization as:

FIG

* V: a visualization chart
* w<sub>i</sub> : the weight of the i<sup>th</sup>
* F<sup>V</sup><sub>i</sub>: chart features of V
* w<sub>0</sub> : the intercept

The SGD algorithm updates the weights to minimize the loss function, which is the least square error with L2 regularization.

We adopt the concept of **Transfer learning** to transfer across different learning tasks by exploiting commonalities between them. The trained user-specific preference model could be reused to reduce the user's labeling effort and to speed up its own learning process. Our transfer mechanism reuses the weights of all dataset-independent features (i.e., F1, F2, F3, F4) learned from that user's previously explored datasets as the initial weights of the user's preference model on new datasets. Thus, VisGuide does not need to re-learn that user's preferences from scratch.

### ViStory Tree

To clearly demonstrate the relations among visualizations, VisGuide organizes the recommended charts into a family tree.

The drill-down charts present a smaller granularity of data, so are treated as descendants of the current chart. Therefore, when a user adds a drill-down/descendant chart into the ViStory tree, that chart will be placed at the next tree level, i.e., to the right of the current chart. VisGuide marks such ancestor-descendant links in green, conceptually echoing a tree's leaves.

The comparison charts, in contrast, present the same level of data granularity, but with different measures, and thus are treated as the current chart's siblings. Comparison/sibling charts added to a ViStory tree are placed at the same tree level, i.e., below the current chart. VisGuide marks these sibling links in brown, representing branches.


## Evaluation


## How to launch VisGuide



## Dataset
[Download Datasets](https://drive.google.com/drive/folders/13CNfDDpSL_Lyk4QCw4QT9PAJfAulPEzh?usp=sharing)


**Acknowledgment**

Jia-Yu Pan, Wen-Chien Lin
