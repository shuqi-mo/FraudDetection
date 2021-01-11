import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve
from scipy import interp
import pandas as pd
# from sklearn.ensemble import AdaBoostClassifier
from cusboost import CUSBoostClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import Normalizer
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import math

from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import StratifiedKFold
import warnings
warnings.filterwarnings('ignore')

dataset = 'pima.txt'

print("dataset : ", dataset)
df = pd.read_csv(dataset, header=None)
df['label'] = df[df.shape[1] - 1]
#
df.drop([df.shape[1] - 2], axis=1, inplace=True)
labelencoder = LabelEncoder()
df['label'] = labelencoder.fit_transform(df['label'])
#
X = np.array(df.drop(['label'], axis=1))
y = np.array(df['label'])

normalization_object = Normalizer()
X = normalization_object.fit_transform(X)
# 将全部训练集分成5个不相交的子集
skf = StratifiedKFold(n_splits=5, shuffle=True)

top_auc = 0
mean_fpr = np.linspace(0, 1, 100)
number_of_clusters = 23
percentage_to_choose_from_each_cluster = 0.5

for depth in range(2, 20, 10):
    for estimators in range(20, 50, 10):
        current_param_auc = []
        current_param_aupr = []
        tprs = []
        for train_index, test_index in skf.split(X, y):
            X_train = X[train_index]
            X_test = X[test_index]
            y_train = y[train_index]
            y_test = y[test_index]
            # 选择使用的分类器，参数depth为基分类器的训练深度，esimators为boosting迭代次数
            classifier = CUSBoostClassifier(depth=depth, n_estimators=estimators)
            # classifier = RusBoost(depth=depth, n_estimators=estimators)
            classifier.fit(X, y)
            predictions = classifier.predict_proba_samme(X_test)
            # auc：roc曲线下的面积，大于0.5才认为有区分正例和负例的能力
            auc = roc_auc_score(y_test, predictions[:, 1])
            # aupr：平均精确率度量
            aupr = average_precision_score(y_test, predictions[:, 1])
            current_param_auc.append(auc)
            current_param_aupr.append(aupr)
            fpr, tpr, thresholds = roc_curve(y_test, predictions[:, 1])
            tprs.append(interp(mean_fpr, fpr, tpr))
            tprs[-1][0] = 0.0
        # 计算auc和aupr的平均值
        current_mean_auc = np.mean(np.array(current_param_auc))
        current_mean_aupr = np.mean(np.array(current_param_aupr))
        # 计算平均值的最佳结果
        if top_auc < current_mean_auc:
            top_auc = current_mean_auc
            best_depth = depth
            best_estimators = estimators
            best_auc = top_auc
            best_aupr = current_mean_aupr
            best_tpr = np.mean(tprs, axis=0)
            best_fpr = mean_fpr
            best_precision, best_recall, _ = precision_recall_curve(y_test, predictions[:, 1])
            best_fpr, best_tpr, thresholds = roc_curve(y_test, predictions[:, 1])
        print('ROC: ', top_auc, ' Aupr: ', best_aupr, ' for depth= ', best_depth, ' estimators = ', best_estimators)
print('ploting', dataset)
plt.plot(best_recall, best_precision, lw=2, color='Blue',
         label='Precision-Recall Curve')
plt.plot(best_fpr, best_tpr, lw=2, color='red',
         label='ROC curve')
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.ylim([0.0, 1.05])
plt.xlim([0.0, 1.0])
plt.legend(loc="upper right")
plt.show()