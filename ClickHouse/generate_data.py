#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import datetime
import time
import string
from random import Random
import multiprocessing

dataCount = 10000
# dataCount = 1000000000
# codeRange = range(ord('a'), ord('z'))
# alphaRange = [chr(x) for x in codeRange]
alphaRange = list(string.ascii_lowercase)
alphaMax = len(alphaRange)
daysMax = 180
theDay = datetime.date(2017, 1, 1)
CPU_COUNT = multiprocessing.cpu_count()

def genRandomName(nameLength):
    global alphaRange, alphaMax
    length = random.randint(1, nameLength)
    name = ''
    for i in range(length):
        name += alphaRange[random.randint(0, alphaMax - 1)]
    return name

def genRandomDeviceId():
    return random.randint(0, 400000000)

def genRandomTemperature():
    return str(round(random.random() * 100, 2))

def genRandomDeviceState():
    return random.randint(0, 3)

def genRandomDay():
    global daysMax, theDay
    mDays = random.randint(0, daysMax)
    mDate = theDay + datetime.timedelta(days=mDays)
    return mDate.isoformat()

def random_str(randomlength=5):
    str_s = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz'
    length = len(chars) - 1
    random = Random()
    str_list = []
    for i in range(randomlength):
        str_s = chars[random.randint(0, length)]
        str_list.append(str_s)
    return str(str_list)


# def genDataBase1(fileName,logName, dataCount):
def genDataBase1(dictargs):
    fileName = dictargs.setdefault('fileName')
    dataCount = dictargs.setdefault('dataCount')
    i = 0
    now_str = '2018-04-19 09:00:00'
    with open(fileName, 'w') as outp:
        while i < dataCount:
            UserID = genRandomDeviceId()
            UserName = genRandomName(20)
            IP = "10.1." + str(random.randint(1, 255)) + "." + str(random.randint(1, 10))
            accessType = genRandomDeviceState()
            LogDate = (
                    datetime.datetime.strptime(now_str, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(seconds=i)).strftime(
                '%Y-%m-%d')
            logTime = (
                    datetime.datetime.strptime(now_str, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(seconds=i)).strftime(
                '%Y-%m-%d %H:%M:%S')
            full_address = genRandomName(30)
            province = genRandomName(20)
            city = genRandomName(20)
            county = genRandomName(20)
            phone = str('138' + str(random.randint(1000, 9999)) + str(random.randint(1000, 9999)))
            LoginCnt = genRandomDeviceId()
            int_col_1 = genRandomDeviceId()
            int_col_2 = genRandomDeviceId()
            int_col_3 = genRandomDeviceId()
            int_col_4 = genRandomDeviceId()
            int_col_5 = genRandomDeviceId()
            int_col_6 = genRandomDeviceId()
            int_col_7 = genRandomDeviceId()
            int_col_8 = genRandomDeviceId()
            int_col_9 = genRandomDeviceId()
            int_col_10 = genRandomDeviceId()
            int_col_11 = genRandomDeviceId()
            int_col_12 = genRandomDeviceId()
            int_col_13 = genRandomDeviceId()
            int_col_14 = genRandomDeviceId()
            int_col_15 = genRandomDeviceId()
            int_col_16 = genRandomDeviceId()
            int_col_17 = genRandomDeviceId()
            int_col_18 = genRandomDeviceId()
            int_col_19 = genRandomDeviceId()
            str_col_1 = genRandomName(20)
            str_col_2 = genRandomName(20)
            str_col_3 = genRandomName(20)
            str_col_4 = genRandomName(20)
            str_col_5 = genRandomName(20)
            str_col_6 = genRandomName(20)
            str_col_7 = genRandomName(20)
            str_col_8 = genRandomName(20)
            str_col_9 = genRandomName(20)
            str_col_10 = genRandomName(20)
            str_col_11 = genRandomName(20)
            str_col_12 = genRandomName(20)
            str_col_13 = genRandomName(20)
            str_col_14 = genRandomName(20)
            str_col_15 = genRandomName(20)
            str_col_16 = genRandomName(20)
            str_col_17 = genRandomName(20)
            str_col_18 = genRandomName(20)
            str_col_19 = genRandomName(20)
            tag_key = "\"" + str(range(1, 5)) + "\""
            tag_values = "\"" + str(random_str(4)) + "\""
            mLine = "%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', %s, %s\n" % (
            UserID, UserName, IP, accessType, LogDate, logTime, full_address, province, city, county, phone, LoginCnt,
            int_col_1, int_col_2, int_col_3, int_col_4, int_col_5, int_col_6, int_col_7, int_col_8, int_col_9,
            int_col_10, int_col_11, int_col_12, int_col_13, int_col_14, int_col_15, int_col_16, int_col_17, int_col_18,
            int_col_19, str_col_1, str_col_2, str_col_3, str_col_4, str_col_5, str_col_6, str_col_7, str_col_8,
            str_col_9, str_col_10, str_col_11, str_col_12, str_col_13, str_col_14, str_col_15, str_col_16, str_col_17,
            str_col_18, str_col_19, tag_key, tag_values)
            outp.write(mLine)
            i += 1

def argsIterable(process_value):
    for i in range(1, process_value + 1):
        filename = 'clikchouse_%d.txt' % i
        yield filename, dataCount

if __name__ == "__main__":
    random.seed()
    start = time.time()
    pool = multiprocessing.Pool(CPU_COUNT)
    pool.map(genDataBase1,
             [{"fileName": "clikchouse_%d" % i, "dataCount": dataCount / CPU_COUNT} for i in range(1, CPU_COUNT + 1)])
    pool.close()
    pool.join()
    end = time.time()
    print('use time:%d' % (end - start))
    print('Ok')

# print UserID,UserName,IP,accessType,LogDate,logTime,full_address,province,city,county,phone,LoginCnt,int_col_1,int_col_2,int_col_3,int_col_4,int_col_5,int_col_6,int_col_7,int_col_8,int_col_9,int_col_10,int_col_11,int_col_12,int_col_13,int_col_14,int_col_15,int_col_16,int_col_17,int_col_18,int_col_19,str_col_1,str_col_2,str_col_3,str_col_4,str_col_5,str_col_6,str_col_7,str_col_8,str_col_9,str_col_10,str_col_11,str_col_12,str_col_13,str_col_14,str_col_15,str_col_16,str_col_17,str_col_18,str_col_19,tag_key,tag_values
