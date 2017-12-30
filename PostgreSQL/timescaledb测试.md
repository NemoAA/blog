# timescaledb测试

## 1 环境准备

| 系统                                       | 数据库           | timescaledb | 内存   | CPU       | 磁盘               |
| ---------------------------------------- | ------------- | ----------- | ---- | --------- | ---------------- |
| Red Hat Enterprise Linux Server release 7.3 (Maipo) | PostgreSQL 10 | 0.7.1       | 16GB | 2路,24core | 10000 RPM raid 0 |

## 2 测试表及数据准备

>  创建 hypertable测试表

```
--创建数据库
postgres=# create database tsdb;
CREATE DATABASE

--创建excention
tsdb=# create extension  timescaledb ;
CREATE EXTENSION

--创建测试表 tsdb_insert_test
CREATE TABLE tsdb_insert_test (
  time        TIMESTAMPTZ       NOT NULL,
  location    TEXT              NOT NULL,
  temperature DOUBLE PRECISION  NULL,
  humidity    DOUBLE PRECISION  NULL
);
-- 转成hypertable 

SELECT create_hypertable('tsdb_insert_test', 'time');

----创建测试用表 pg_insert_test
CREATE TABLE pg_insert_test (
  time        TIMESTAMPTZ       NOT NULL,
  location    TEXT              NOT NULL,
  temperature DOUBLE PRECISION  NULL,
  humidity    DOUBLE PRECISION  NULL
);
```

### 2.1 插入性能测试

> 对比pg和tsdb插入性能

#### 2.1.1 timescaledb测试

```
--pgbench测试语句(测试4小时插入)

nohup pgbench -M prepared -n -r -P 1 -f /home/postgres/tsdb/tsdb_insert.sql tsdb -c 24 -j 24 -T 14400 >/home/postgres/tsdb/tsdb_insert.csv 2>&1 &

--测试脚本内容
vi tsdb_insert.sql
insert into tsdb_insert_test select clock_timestamp(),md5( random()::text),random()*100,random()*200;

--测试结果
transaction type: /home/postgres/tsdb/tsdb_insert.sql
scaling factor: 1
query mode: prepared
number of clients: 24
number of threads: 24
duration: 14400 s
number of transactions actually processed: 28248809
latency average = 12.234 ms
latency stddev = 2.026 ms
tps = 1961.721566 (including connections establishing)
tps = 1961.722457 (excluding connections establishing)
script statistics:
 - statement latencies in milliseconds:
        12.317  insert into tsdb_insert_test select clock_timestamp(),md5( random()::text),random()*100,random()*200;

--插入数据量
tsdb=# select count(*) from tsdb_insert_test ;
  count   
----------
 28248809

```

##### 2.1.1.1测试结果图

![](https://mmbiz.qpic.cn/mmbiz_png/EtlRsbVmOYZdH6OnuLjAPVLJUpibsMicQvvlZDgbhNqFqicmFC2g86iamltjLibiaXaAEBgFJMnXmsSCR1J0ickiaOWeMw/0?wx_fmt=png)

> 画图程序代码
>
> ```python
> # -*- coding: utf-8 -*-
> import numpy as np
> import matplotlib.pyplot as plt
> import pandas
> import csv
> import re
> import scipy
> from sklearn import linear_model
>
> '''
> 参考
> http://blog.csdn.net/aliendaniel/article/details/56479546
> http://blog.csdn.net/qiu931110/article/details/68130199
> '''
>
> x = []
> y = []
> csv_reader = csv.reader(open(r'C:\Users\Nemo\Desktop\tsdb_insert.csv'))
> for row in csv_reader:
>         if str(row[0][0:8]) == "progress":
>                 print row[0]
>                 list_x = int(re.findall(r"progress: (.*?).0 s", row[0], re.S | re.M | re.I)[0])
>                 list_y = float(re.findall(r" (.*?) tps", row[1], re.S | re.M | re.I)[0])
>                 x.append(list_x)
>                 y.append(list_y)
>                 print(row)
>         else:
>                 pass
> print x
> print y
> plt.figure(figsize=(80,6)) # 创建绘图对象
> # T=np.arctan2(x,y)
> plt.scatter(x, y, s=25, alpha=0.5, marker='.' ,color = 'r')
> # plt.scatter(x,y,c=T,s=100,alpha=0.4,marker='.')
> regr = linear_model.LinearRegression()
> #plt.plot(aa,bb,"b",linewidth=1,color='r',marker='o')   # 在当前绘图对象绘图（X轴，Y轴，蓝色虚线，线宽度）
> plt.xlabel("Time(s)") # X轴标签
> plt.ylabel("TPS")  # Y轴标签
> plt.title("TimescaleDB") # 图标题
> plt.grid('true')
> plt.style.use('ggplot')
> plt.show()  # 显示图
> plt.savefig("line.jpg") # 保存图
> ```

##### 2.1.1.2 测试结果分析

> 测试过程监控,此测试瓶颈在io
>
> ```
> Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
> sda               0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> sdb               0.00     0.00    0.00  168.00     0.00     2.76    33.62     1.02    6.12    0.00    6.12   5.83  97.90
> scd0              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-0              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-1              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-2              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-3              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-4              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
>
> avg-cpu:  %user   %nice %system %iowait  %steal   %idle
>            1.88    0.00    1.04    2.84    0.00   94.24
>
> Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
> sda               0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> sdb               0.00     0.00    0.00  165.00     0.00     1.98    24.63     0.99    6.00    0.00    6.00   5.95  98.10
> scd0              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-0              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-1              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-2              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-3              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> dm-4              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
> ```

> 接下来分析io瓶颈具体在哪
>
> 采集过去10分钟wal日志产生量
>
> ```
> tsdb=# select sum((pg_stat_file(file)).size)/1024/1024||'MB' from (select 'pg_wal/'||pg_ls_dir('pg_wal') as file)t where now()-(pg_stat_file(file)).change<=interval '10 min';
>         ?column?         
> -------------------------
>  1104.0000000000000000MB
> (1 row)
>
> ```
>
> 查看过去10分钟产生wal具体内容
>
> ```
> [postgres@localhost pg_wal]$ pg_waldump -b 0000000100000001000000D6  0000000100000001000000E6 -z
> Type                                           N      (%)          Record size      (%)             FPI size      (%)        Combined size      (%)
> ----                                           -      ---          -----------      ---             --------      ---        -------------      ---
> XLOG                                           1 (  0.00)                  106 (  0.00)                    0 (  0.00)                  106 (  0.00)
> Transaction                              1181439 ( 33.28)             40169102 ( 14.56)                    0 (  0.00)             40169102 ( 14.55)
> Storage                                        0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> CLOG                                          36 (  0.00)                 1080 (  0.00)                    0 (  0.00)                 1080 (  0.00)
> Database                                       0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> Tablespace                                     0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> MultiXact                                      0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> RelMap                                         0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> Standby                                       41 (  0.00)                 5846 (  0.00)                    0 (  0.00)                 5846 (  0.00)
> Heap2                                          2 (  0.00)                  134 (  0.00)                    0 (  0.00)                  134 (  0.00)
> Heap                                     1181450 ( 33.28)            140592432 ( 50.94)                88932 ( 76.98)            140681364 ( 50.95)
> Btree                                    1186935 ( 33.44)             95211017 ( 34.50)                26596 ( 23.02)             95237613 ( 34.49)
> Hash                                           0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> Gin                                            0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> Gist                                           0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> Sequence                                       0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> SPGist                                         0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> BRIN                                           0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> CommitTs                                       0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> ReplicationOrigin                              0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> Generic                                        0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
> LogicalMessage                                 0 (  0.00)                    0 (  0.00)                    0 (  0.00)                    0 (  0.00)
>                                         --------                      --------                      --------                      --------
> Total                                    3549904                     275979717 [99.96%]               115528 [0.04%]             276095245 [100%]
>
> ```
>
> 从上面可以看出timescaledb插入时,瓶颈在io其中heap表和索引写占据85.44,事务日志占据14.56,优化有如下
>
>     1. 将一条一条插入改成分批插入(测试语句无法模拟)
>      2. 更好iops更高的磁盘

####  2.1.2 PostgreSQL测试

> 无索引

```
--pgbench测试语句

nohup pgbench -M prepared -n -r -P 1 -f /home/postgres/tsdb/pg_insert.sql tsdb -c 25 -j 25 -t 800000 >> /home/postgres/tsdb/pg_insert.csv 2>&1 &

--测试脚本内容
vi pg_insert.sql
insert into pg_insert_test select clock_timestamp(),md5( random()::text),random()*100,random()*200;

--测试开始lsn
tsdb=# select  pg_current_wal_lsn();
 pg_current_wal_lsn 
--------------------
 2/2BF8DE90
(1 row)

--测试结果
transaction type: /home/postgres/tsdb/pg_insert.sql
scaling factor: 1
query mode: prepared
number of clients: 24
number of threads: 24
duration: 14400 s
number of transactions actually processed: 28341286
latency average = 12.194 ms
latency stddev = 1.774 ms
tps = 1968.143543 (including connections establishing)
tps = 1968.144885 (excluding connections establishing)
script statistics:
 - statement latencies in milliseconds:
        12.265  insert into pg_insert_test select clock_timestamp(),md5( random()::text),random()*100,random()*200;


```

##### 2.1.2.1测试结果图

![](https://mmbiz.qpic.cn/mmbiz_png/EtlRsbVmOYZ8tRjWN2Ow8EDCrkdXgos2ygpcB4wpsuey0IibS6yHsPINNlNheUR1DSLOwk3ytjJxrRIG6eDb23w/0?wx_fmt=png)

## 3 数据分区测试

> 参考 https://blog.timescale.com/time-series-data-postgresql-10-vs-timescaledb-816ee808bac5



### 3.1 创建测试表

```
--创建普通表
CREATE TABLE tbl_part (
  time        TIMESTAMPTZ       NOT NULL,
  location    TEXT              NOT NULL,
  temperature DOUBLE PRECISION  NULL,
  humidity    DOUBLE PRECISION  NULL
);

--创建 hypertable 表并且按照时间和地点分区
SELECT create_hypertable('tbl_part', 'time', 'location', 4);
```

### 3.2 插入数据

> 插入从今天起插入一个月的数据

```
insert into tbl_part select generate_series(now(),now()+interval '1 months','1 hours'),md5(random()::text),random()*100,random()*1000;

```

### 3.3 查看表

> 通过\d+ table 可以看到timescaledb也是利用继承的原理创建子表

```
tsdb=# \d+ tbl_part
                                             Table "public.tbl_part"
   Column    |           Type           | Collation | Nullable | Default | Storage  | Stats target | Description 
-------------+--------------------------+-----------+----------+---------+----------+--------------+-------------
 time        | timestamp with time zone |           | not null |         | plain    |              | 
 location    | text                     |           | not null |         | extended |              | 
 temperature | double precision         |           |          |         | plain    |              | 
 humidity    | double precision         |           |          |         | plain    |              | 
Indexes:
    "tbl_part_location_time_idx" btree (location, "time" DESC)
    "tbl_part_time_idx" btree ("time" DESC)
Child tables: _timescaledb_internal._hyper_4_10_chunk,
              _timescaledb_internal._hyper_4_11_chunk,
              _timescaledb_internal._hyper_4_12_chunk,
              _timescaledb_internal._hyper_4_13_chunk,
              _timescaledb_internal._hyper_4_14_chunk,
              _timescaledb_internal._hyper_4_7_chunk,
              _timescaledb_internal._hyper_4_8_chunk,
              _timescaledb_internal._hyper_4_9_chunk
--查看约束
tsdb=# SELECT b.relname,r.conname, pg_catalog.pg_get_constraintdef(r.oid, true) as check_name FROM pg_catalog.pg_constraint r ,pg_class b WHERE r.contype = 'c'  AND  r.conrelid = b.oid  and b.relname like '_hyper_4%' and b.relkind = 'r';
      relname      |   conname    |                                                                  check_name                        
                                          
-------------------+--------------+----------------------------------------------------------------------------------------------------
------------------------------------------
 _hyper_4_7_chunk  | constraint_4 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 536870911 AND _timescaledb_internal.ge
t_partition_hash(location) < 1073741822)
 _hyper_4_7_chunk  | constraint_3 | CHECK ("time" >= '2017-11-20 08:00:00+08'::timestamp with time zone AND "time" < '2017-12-20 08:00:
00+08'::timestamp with time zone)
 _hyper_4_8_chunk  | constraint_5 | CHECK (_timescaledb_internal.get_partition_hash(location) < 536870911)
 _hyper_4_8_chunk  | constraint_3 | CHECK ("time" >= '2017-11-20 08:00:00+08'::timestamp with time zone AND "time" < '2017-12-20 08:00:
00+08'::timestamp with time zone)
 _hyper_4_9_chunk  | constraint_6 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 1073741822 AND _timescaledb_internal.g
et_partition_hash(location) < 1610612733)
 _hyper_4_9_chunk  | constraint_3 | CHECK ("time" >= '2017-11-20 08:00:00+08'::timestamp with time zone AND "time" < '2017-12-20 08:00:
00+08'::timestamp with time zone)
 _hyper_4_10_chunk | constraint_7 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 1610612733)
 _hyper_4_10_chunk | constraint_3 | CHECK ("time" >= '2017-11-20 08:00:00+08'::timestamp with time zone AND "time" < '2017-12-20 08:00:
00+08'::timestamp with time zone)
 _hyper_4_11_chunk | constraint_5 | CHECK (_timescaledb_internal.get_partition_hash(location) < 536870911)
 _hyper_4_11_chunk | constraint_8 | CHECK ("time" >= '2017-12-20 08:00:00+08'::timestamp with time zone AND "time" < '2018-01-19 08:00:
00+08'::timestamp with time zone)
 _hyper_4_12_chunk | constraint_7 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 1610612733)
 _hyper_4_12_chunk | constraint_8 | CHECK ("time" >= '2017-12-20 08:00:00+08'::timestamp with time zone AND "time" < '2018-01-19 08:00:
00+08'::timestamp with time zone)
 _hyper_4_13_chunk | constraint_6 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 1073741822 AND _timescaledb_internal.g
et_partition_hash(location) < 1610612733)
 _hyper_4_13_chunk | constraint_8 | CHECK ("time" >= '2017-12-20 08:00:00+08'::timestamp with time zone AND "time" < '2018-01-19 08:00:
00+08'::timestamp with time zone)
 _hyper_4_14_chunk | constraint_4 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 536870911 AND _timescaledb_internal.ge
t_partition_hash(location) < 1073741822)
 _hyper_4_14_chunk | constraint_8 | CHECK ("time" >= '2017-12-20 08:00:00+08'::timestamp with time zone AND "time" < '2018-01-19 08:00:
00+08'::timestamp with time zone)
(16 rows)

--hash分区约束
tsdb=# select distinct on(check_name)* from (SELECT r.conname, pg_catalog.pg_get_constraintdef(r.oid, true) as check_name FROM pg_catalog.pg_constraint r WHERE r.contype = 'c'  AND  r.conrelid IN (select oid from pg_class where relname like '_hyper_4%' and relkind = 'r') ) as t where t.check_name like '%hash%';
   conname    |                                                                  check_name                                            
                      
--------------+------------------------------------------------------------------------------------------------------------------------
----------------------
 constraint_5 | CHECK (_timescaledb_internal.get_partition_hash(location) < 536870911)
 constraint_6 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 1073741822 AND _timescaledb_internal.get_partition_hash(lo
cation) < 1610612733)
 constraint_7 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 1610612733)
 constraint_4 | CHECK (_timescaledb_internal.get_partition_hash(location) >= 536870911 AND _timescaledb_internal.get_partition_hash(loc
ation) < 1073741822)
(4 rows)
```

### 3.4 分区方式

> * 从上面可以看出timescaledb自动创建的子表分别覆盖2个月的时间,其中时间分区为 11月20-12月19,另外一个为12月20到2018-01-19
> * 从测试可以得出timescaledb在创建表时,同时覆盖最小时间前半个月的时间,同时在最大时间往后创建半个月左右的时间,这样来保证每个延迟数据不会造成某一个chunk特别大
> * 同时在每个时间段内,在根据另外一个字段均匀的将记录采用hash方式均匀的分为4个子表,其分区表架构可为如下方式
> * 从这种分区方式看,hash分区数量不宜过多,因为每一个时间点都会扫描hash分区数量的表,跨时间段可能会扫描更多的子表
>
> ![](https://cdn-images-1.medium.com/max/1200/1*ZKUYWrK5709hBQFqQyBE2g.jpeg)



## 4 地铁需求

> 1. 26个车站,每个车站3w个监控设备 ,每秒上传一次数据入库(每条记录24个字节)
> 2. 查询某个时间点所有监控设备的状态
> 3. 某个设备一段时间内的状态值(趋势)

### 4.1 测试用例

```
create table subway_monitor(
	time timestamp not null,
	subway_station varchar(8) not null,
	device_id  text,
	device_state int,
	temperature NUMERIC NULL
);

---创建 hypertable 表并且按照时间和设备名分区
SELECT create_hypertable('subway_monitor', 'time', 'device_id', 16);

--测试语句
pgbench -M prepared -n -r -P 1 -f /home/postgres/tsdb/subway_insert_test_1.sql tsdb -c 30 -j 24 -T 600

--插入数据语句,每次插入1000条
vi subway_insert_test_1.sql 
insert into subway_monitor select clock_timestamp(),substr(md5(random()::text),1,8),ceil(random()*30000),random()*100 from generate_series(1,1000);
```

### 4.2 测试结果

> 如果app端能每次合并1000条批量插入,以公司目前服务器每秒可以插入30.6万行/s的数据量,理论上3台这样配置的服务器可满足插入需求

```
transaction type: /home/postgres/tsdb/subway_insert_test_1.sql
scaling factor: 1
query mode: prepared
number of clients: 24
number of threads: 24
duration: 60 s
number of transactions actually processed: 18391
latency average = 78.332 ms
latency stddev = 47.460 ms
tps = 306.207491 (including connections establishing)
tps = 306.288216 (excluding connections establishing)
script statistics:
 - statement latencies in milliseconds:
        78.648  insert into subway_monitor select clock_timestamp(),substr(md5(random()::text),1,8),ceil(random()*30000),random()*100 from generate_series(1,1000);

```





