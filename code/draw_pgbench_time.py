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
        self.csv_reader = csv.reader(open(r'C:\Users\nemo\Desktop\test_tpcb.log'))

    def draw(self, limit):
        for row in self.csv_reader:
            if str(row[0][0:8]) == "progress":

                list_x = float(re.findall(r"progress: (.*?) s", row[0], re.S | re.M | re.I)[0])
                list_y = float(re.findall(r" (.*?) tps", row[1], re.S | re.M | re.I)[0])
                if list_y < limit:
                # if list_y > limit:
                    self.x.append(list_x)
                    self.y.append(list_y)
                    self.for_num = self.for_num + 1
                    self.x2.append(self.for_num)
                    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(list_x)), list_y)
            else:
                pass

        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.x[0]))
        # 字符类型转日期类型
        start_time = dt.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        xx_list = [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(aa)) for aa in self.x]
        dates = [dt.datetime.strptime(aa, "%Y-%m-%d %H:%M:%S") for aa in xx_list]
        print 'OK'
        plt.figure(figsize=(80, 6))  # 创建绘图对象
        pylab.plot_date(pylab.date2num(dates), self.y, linestyle='', marker='.')
        regr = linear_model.LinearRegression()
        plt.ylim(ymin=0)
        # plt.ylim(ymax=200000)
        plt.xlabel("Time(s)")  # X轴标签
        plt.ylabel("TPS")  # Y轴标签
        # plt.title("PostgreSQL insert batchsize 10")  # 图标题
        # plt.title("PostgreSQL QPS")  # 图标题
        plt.title("PostgreSQL TPCB s-1000")  # 图标题
        plt.grid('true')
        plt.style.use('ggplot')
        plt.show()  # 显示图
        plt.savefig("line.jpg")  # 保存图


if __name__ == '__main__':
    pgbench = draw_pgbench()
    pgbench.draw(1000000)
    # pgbench.draw(1000)
