# -*- coding: utf-8 -*-

import csv
import re
import pylab
from sklearn import linear_model
import datetime as dt
# import dateutil, pylab, random
from pylab import *

'''
参考
http://blog.csdn.net/aliendaniel/article/details/56479546
http://blog.csdn.net/qiu931110/article/details/68130199
'''
warnings.filterwarnings("ignore")

reload(sys)
sys.setdefaultencoding('utf-8')

class draw_pgbench():
    def __init__(self):
        self.x = []
        self.x2 = []
        self.y = []
        self.for_num = 0
        self.csv_reader = csv.reader(open(r'C:\Users\nemo\Desktop\postgresql-2018-11-30_073600.csv'))

    def draw(self, limit):
        for row in self.csv_reader:
            if str(row[13][0:21]) == "BufferSync: processed":
                # print row[13].split('processed',1)[1].strip()
                # print row[0].split('CST',1)[0].strip()

                list_x = row[0].split('CST',1)[0].split('.',1)[0].strip()
                list_y = float(row[13].split('processed',1)[1].strip())
                if list_y < limit:
                # if list_y > limit:
                    self.x.append(list_x)
                    self.y.append(list_y)
                    self.for_num = self.for_num + 1
                    self.x2.append(self.for_num)
                    # print(list_x, list_y)
            else:
                pass
        dates = [dt.datetime.strptime(aa, "%Y-%m-%d %H:%M:%S") for aa in self.x]
        # print dates
        print 'OK'
        plt.figure(figsize=(80, 6))  # 创建绘图对象
        pylab.plot_date(pylab.date2num(dates), self.y, linestyle='', marker='.')
        regr = linear_model.LinearRegression()
        plt.xlabel("Time(s)")  # X轴标签
        plt.ylabel("TPS")  # Y轴标签
        plt.title("PostgreSQL BufferSync")  # 图标题
        # plt.title("PostgreSQL QPS")  # 图标题
        plt.grid('true')
        plt.style.use('ggplot')
        plt.show()  # 显示图
        plt.savefig("line2.jpg")  # 保存图


if __name__ == '__main__':
    pgbench = draw_pgbench()
    pgbench.draw(1000000)
    # pgbench.draw(1000)
