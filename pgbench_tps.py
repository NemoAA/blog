# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pandas
import csv
import re
import scipy
from sklearn import linear_model

'''
参考
http://blog.csdn.net/aliendaniel/article/details/56479546
http://blog.csdn.net/qiu931110/article/details/68130199
'''

x = []
y = []
csv_reader = csv.reader(open(r'C:\Users\Nemo\Desktop\tsdb_insert.csv'))
for row in csv_reader:
        if str(row[0][0:8]) == "progress":
                print row[0]
                list_x = int(re.findall(r"progress: (.*?).0 s", row[0], re.S | re.M | re.I)[0])
                list_y = float(re.findall(r" (.*?) tps", row[1], re.S | re.M | re.I)[0])
                x.append(list_x)
                y.append(list_y)
                print(row)
        else:
                pass
print x
print y
plt.figure(figsize=(80,6)) # 创建绘图对象
# T=np.arctan2(x,y)
plt.scatter(x, y, s=25, alpha=0.5, marker='.' ,color = 'r')
# plt.scatter(x,y,c=T,s=100,alpha=0.4,marker='.')
regr = linear_model.LinearRegression()
#plt.plot(aa,bb,"b",linewidth=1,color='r',marker='o')   # 在当前绘图对象绘图（X轴，Y轴，蓝色虚线，线宽度）
plt.xlabel("Time(s)") # X轴标签
plt.ylabel("TPS")  # Y轴标签
plt.title("TimescaleDB") # 图标题
plt.grid('true')
plt.style.use('ggplot')
plt.show()  # 显示图
plt.savefig("line.jpg") # 保存图
