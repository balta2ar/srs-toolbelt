
import numpy as np
import pandas as pd
#import scipy
#from scipy.cluster.vq import kmeans, vq
#from sklearn.preprocessing import normalize
#from sklearn.cluster import KMeans

from sklearn import model_selection
from sklearn.ensemble import RandomForestClassifier
#import matplotlib.pyplot as plt
#import seaborn as sns
#%matplotlib inline"


data = pd.read_csv('lines.csv')
data['index'] = data.index
data.head()

features = ['ink_volume',
            'fiber_ink_volume',
            'height',
            'width',
            'area',
            'words_ratio',
            'line_index']
target = 'lineclass'
X = data.loc[:, features].values
y = data.loc[:, [target]].values.ravel()
#print(y)


#url = "https://archive.ics.uci.edu/ml/machine-learning-databases/pima-indians-diabetes/pima-indians-diabetes.data"
#names = ['preg', 'plas', 'pres', 'skin', 'test', 'mass', 'pedi', 'age', 'class']
#dataframe = pandas.read_csv(url, names=names)
#array = dataframe.values
#X = array[:,0:8]
#Y = array[:,8]
seed = 0
num_trees = 100
max_features = 4
kfold = model_selection.KFold(n_splits=10, random_state=seed)
model = RandomForestClassifier(n_estimators=num_trees, max_features=max_features, n_jobs=-1)
scores = model_selection.cross_val_score(model, X, y, cv=kfold)
print(scores.mean())
print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))
#from ipdb import set_trace; set_trace()
