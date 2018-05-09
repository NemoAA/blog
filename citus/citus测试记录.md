## 1. 环境

### 1.1 服务器信息

| 角色        | IP           | 系统            | 数据库      | 内存 | CPU    | 磁盘                |
| ----------- | ------------ | --------------- | ----------- | ---- | ------ | ------------------- |
| coordinator | 192.168.6.11 | oraclelinux 7.3 | citusdb 7.3 | 96GB | 2X16核 | 2X480GB SSD raid 0 |
| work        | 192.168.6.12 | oraclelinux 7.3 | citusdb 7.3 | 96GB | 2X16核 | 2X480GB SSD raid 0 |
| work        | 192.168.6.13 | oraclelinux 7.3 | citusdb 7.3 | 96GB | 2X16核 | 2X480GB SSD raid 0 |

## 2. INSERT测试

### 2.1 sysbench

#### 2.1.1 单机PG插入

> - synchronous_commit = off

```
CREATE TABLE citus_test1
(
  id integer NOT NULL,
  k integer NOT NULL DEFAULT 0,
  c character(120) NOT NULL DEFAULT ''::bpchar,
  pad character(60) NOT NULL DEFAULT ''::bpchar,
  PRIMARY KEY (id)
);

CREATE INDEX k_1 ON citus_test1(k); 

-- 测试脚本
/usr/local/sysbench/bin/sysbench --test=/home/postgres/citus/oltp_insert.lua --db-driver=pgsql --pgsql-host=192.168.6.12 --pgsql-port=5432 --pgsql-user=postgres  --pgsql-db=postgres  --auto_inc=0  --time=300 --threads=128  --report-interval=5 run
```

#### 2.1.2 citus测试

> - 瓶颈在coordinator节点cpu上
> - coordinator的cpu利用达到90%,
> - work节点cpu使用在20%,io没有压力

```
-- 建立表结构
CREATE TABLE citus_test1
(
  id integer NOT NULL,
  k integer NOT NULL DEFAULT 0,
  c character(120) NOT NULL DEFAULT ''::bpchar,
  pad character(60) NOT NULL DEFAULT ''::bpchar,
  PRIMARY KEY (id)
);

CREATE INDEX k_1 ON citus_test1(k);

set citus.shard_count = 128;
set citus.shard_replication_factor = 1;
select create_distributed_table('citus_test1','id'); 

-- 测试脚本
/usr/local/sysbench/bin/sysbench --test=/home/postgres/citus/oltp_insert.lua --db-driver=pgsql --pgsql-host=192.168.6.13 --pgsql-port=5432 --pgsql-user=postgres  --pgsql-db=postgres  --auto_inc=0  --time=300 --threads=128  --report-interval=5 run
```

#### 2.1.3 3个work节点

> - synchronous_commit  = on
> - coordinator节点 CPU使用达到95%左右成为瓶颈,增加work节点对整体TPS并无影响,甚至略有下降
> - work节点cpu使用在20%,io没有压力

```
-- 添加work节点
select * from  master_add_node('192.168.6.11',5432);
select * from  master_add_node('192.168.6.12',5432);
select * from  master_add_node('192.168.6.13',5432);

-- 查看work节点
SELECT * FROM master_get_active_worker_nodes();

-- 建立表结构
CREATE TABLE citus_test1
(
  id integer NOT NULL,
  k integer NOT NULL DEFAULT 0,
  c character(120) NOT NULL DEFAULT ''::bpchar,
  pad character(60) NOT NULL DEFAULT ''::bpchar,
  PRIMARY KEY (id)
);

CREATE INDEX k_1 ON citus_test1(k);

set citus.shard_count = 128;
set citus.shard_replication_factor = 1;
select create_distributed_table('citus_test1','id'); 

-- 测试脚本
/usr/local/sysbench/bin/sysbench --test=/home/postgres/citus/oltp_insert.lua --db-driver=pgsql --pgsql-host=192.168.6.12 --pgsql-port=5433 --pgsql-user=postgres  --pgsql-db=postgres  --auto_inc=0  --time=300 --threads=128  --report-interval=5 run
```

#### 2.1.4 测试结果

##### 1) 关闭同步提交

|    batch size 1    |    TPS    | RT(min/avg/max/95%)  |
| :----------------: | :-------: | :------------------: |
|    citusdb 7.3     | 135785.63 | 0.23/0.94/76.28/1.21 |
|  PostgreSQL 10.3   | 173255.81 | 0.10/0.74/69.47/1.52 |

##### 2) 开启同步提交


|  batch size 1   |    TPS    | RT(min/avg/max/95%)  |
| :-------------: | :-------: | :------------------: |
|   citusdb 7.3   | 119208.93 | 0.33/1.07/76.35/1.64 |
| PostgreSQL 10.3 | 115446.29 | 0.25/1.11/51.56/1.70 |

#####  3) 3个work节点测试

| work 节点数 |    TPS    | RT(min/avg/max/95%)  |
| :---------: | :-------: | :------------------: |
|   2 节点    | 108854.91 | 0.34/1.17/84.25/1.64 |
|   3 节点    | 99208.08  | 0.37/1.29/80.27/1.86 |
### 2.2 pgbench

#### 2.2.1单cn测试

```
-- 测试脚本
[postgres@clickhost_db_13 citus]$ cat citus_insert.sql 
\set nbranches :scale
\set ntellers 10 * :scale
\set naccounts 100000 * :scale
\set aid random(1, :naccounts)
\set bid random(1, :nbranches)
\set tid random(1, :ntellers)
\set delta random(-5000, 5000)
INSERT INTO pgbench_history (tid, bid, aid, delta, mtime) VALUES (:tid, :bid, :aid, :delta, CURRENT_TIMESTAMP);

-- coordinator
su - postgres
pgbench -i
psql -c "SELECT create_distributed_table('pgbench_history', 'aid');"

-- 执行pgbench测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_insert.sql -c 256 -j 64 -T 30
```

#### 2.2.2 masterless测试 

> - masterless 在work节点和coordinator节点都执行pgbench插入,错开数据避免冲突
> - 每个work节点64个client
> - coordinator节点256个client
> - 此时每个节点cpu都在80%以上

```
-- coordinator节点执行,创建表结构并,创建分布表

-- work节点创建表结构,执行如下命令
copy pg_dist_node from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_node to STDOUT"';
copy pg_dist_partition from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_partition to STDOUT"';
copy pg_dist_shard from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_shard to STDOUT"';
copy pg_dist_shard_placement from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy (select * from pg_dist_shard_placement) to STDOUT"';
copy pg_dist_colocation from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_colocation to STDOUT"';
```

#### 2.2.3 测试结果

| 架构       | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| ---------- | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 1.901        | 134,325              |
| 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 128   | 1.894        | 134,701              |
| masterless | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 128   | 1.89         | 197,500              |


## 3. UPDATE 测试

### 3.1 pgbench

#### 3.1.1 单cn测试

```
-- 测试脚本
[postgres@clickhost_db_13 citus]$ cat citus_update.sql 
\set naccounts 100000 * :scale
\set aid random(1 ,:naccounts)
\set delta random(-5000, 5000)
UPDATE pgbench_accounts SET abalance = abalance + :delta WHERE aid = :aid;

-- coordinator
su - postgres
pgbench -i
psql -c "SELECT create_distributed_table('pgbench_accounts', 'aid');"

-- 执行pgbench测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_update.sql -c 256 -j 64 -T 30

```

#### 3.2 masterless测试

> 在用pgbench生成测试数据,会在本地和分布上都存在一份数据,执行如下命令可删除本地数据只保留分布数据
>
> - 1. 备份pg_dist_partition数据
>   2. 删除 pg_dist_partition 数据
>   3. 清空本地表
>   4. 恢复 pg_dist_partition
>
>   2-4操作步骤在一个事务中进行

```
-- coordinator节点执行,创建表结构,创建分布表

-- work节点创建表结构,执行如下命令 work节点操作
copy pg_dist_node from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_node to STDOUT"';
copy pg_dist_partition from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_partition to STDOUT"';
copy pg_dist_shard from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_shard to STDOUT"';
copy pg_dist_shard_placement from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy (select * from pg_dist_shard_placement) to STDOUT"';
copy pg_dist_colocation from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_colocation to STDOUT"';

-- 备份pg_dist_partition数据 coordinator节点操作
CREATE TABLE pg_dist_partition_tmp AS SELECT * FROM pg_catalog.pg_dist_partition;

-- 以下操作在一个事务中进行 coordinator节点操作
begin ;
delete from pg_catalog.pg_dist_partition where logicalrelid = 'pgbench_accounts'::regclass;
delete from pgbench_accounts;
insert into pg_catalog.pg_dist_partition select * from pg_dist_partition_tmp where logicalrelid = 'pgbench_accounts'::regclass;
end;
```

#### 3.3 测试结果

> - 数据量1亿
> - masterless的架构 work节点上分别64个客户端,coordinator上256个客户端,其中coordinator和work节点cpu分别达到80%以上

| 架构       | Coordinator Node   | Worker Nodes           | shard | fillfactor | Latency (ms) | Transactions per sec |
| ---------- | ------------------ | ---------------------- | ----- | ---------- | :----------- | -------------------- |
| 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 100        | 2.159        | 118,177              |
| 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 80         | 2.122        | 120,210              |
| 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 128   | 80         | 2.207        | 115,610              |
| masterless | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 80         | 2.40         | 160,657              |

## 4. SELECT测试

> * 数据量1亿

### 4.1 单表

#### 4.1.1 PG单机测试

> * 数据量1亿
> * cpu使用100%

```
-- 测试脚本
[postgres@clickhost_db_13 citus]$ cat citus_select.sql 
\set aid random(1 ,100000000)
SELECT * FROM  pgbench_accounts WHERE aid = :aid;

-- 执行pgbench测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_update.sql -c 256 -j 64 -T 30
```

#### 4.1.1 单cn

> - 数据量1亿
> - coordinator节点上cpu使用100%

```
-- 测试脚本
[postgres@clickhost_db_13 citus]$ cat citus_select.sql 
\set aid random(1 ,100000000)
SELECT * FROM  pgbench_accounts WHERE aid = :aid;

-- coordinator
su - postgres
pgbench -i
psql -c "SELECT create_distributed_table('pgbench_accounts', 'aid');"

-- 执行pgbench测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_update.sql -c 256 -j 64 -T 30
```

#### 4.1.2 masterless

> - 数据量1亿
> - work节点上分别64个客户端,coordinator上256个客户端
> - coordinator上CPU达到100%
> - work节点上CPU达到95%

```
-- 所有节点创建表结构
psql -h 192.168.6.11 -p 5432 -f /home/postgres/pgbench_accounts.sql
psql -h 192.168.6.12 -p 5432 -f /home/postgres/pgbench_accounts.sql
psql -h 192.168.6.13 -p 5432 -f /home/postgres/pgbench_accounts.sql

-- coordinator节点创建分布表
set citus.shard_count = 128;
set citus.shard_replication_factor = 1;
SELECT create_distributed_table('pgbench_accounts', 'aid');

-- work节点拷贝元数据
copy pg_dist_node from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_node to STDOUT"';
copy pg_dist_partition from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_partition to STDOUT"';
copy pg_dist_shard from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_shard to STDOUT"';
copy pg_dist_shard_placement from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy (select * from pg_dist_shard_placement) to STDOUT"';
copy pg_dist_colocation from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_colocation to STDOUT"';

-- coordinator节点导入数据
copy pgbench_accounts from '/home/postgres/pgbench_accounts.csv' with csv header;

-- 测试脚本
[postgres@clickhost_db_13 citus]$ cat citus_select.sql 
\set aid random(1 ,100000000)
SELECT * FROM  pgbench_accounts WHERE aid = :aid;

-- coordinator节点执行测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_select.sql -c 256 -j 64 -T 30

-- work节点1执行测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_select.sql -c 64 -j 64 -T 30

-- work节点2执行测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_select.sql -c 64 -j 64 -T 30
```

#### 4.1.3 测试结果

##### 1) PG测试结果

| Node               | Latency (ms) | Transactions per sec |
| ------------------ | ------------ | -------------------- |
| 32cores - 96GB RAM | 1.316        | 193,522              |

##### 2) citus测试结果

| 架构       | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| ---------- | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 2.069        | 123,242              |
| 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 128   | 2.060        | 123,814              |
| masterless | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 1.53         | 224,555              |
| masterless | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 128   | 1.56         | 221,583              |

### 4.2 join

#### 4.2.1 分布表+参考表

```
-- 所有节点创建表结构
psql -h 192.168.6.11 -p 5432 -f /home/postgres/pgbench_accounts.sql
psql -h 192.168.6.12 -p 5432 -f /home/postgres/pgbench_accounts.sql
psql -h 192.168.6.13 -p 5432 -f /home/postgres/pgbench_accounts.sql

psql -h 192.168.6.11 -p 5432 -c "create table tbl1(aid bigserial primary key,bid int,user_name varchar);" postgres
psql -h 192.168.6.12 -p 5432 -c "create table tbl1(aid bigserial primary key,bid int,user_name varchar);" postgres
psql -h 192.168.6.13 -p 5432 -c "create table tbl1(aid bigserial primary key,bid int,user_name varchar);" postgres

-- coordinator节点创建分布表
set citus.shard_count = 128;
set citus.shard_replication_factor = 1;
SELECT create_distributed_table('pgbench_accounts', 'aid');

-- 创建参考表
set citus.shard_count = 128;
set citus.shard_replication_factor = 1;
SELECT create_reference_table('tbl1');

-- work节点拷贝元数据
copy pg_dist_node from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_node to STDOUT"';
copy pg_dist_partition from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_partition to STDOUT"';
copy pg_dist_shard from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_shard to STDOUT"';
copy pg_dist_shard_placement from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy (select * from pg_dist_shard_placement) to STDOUT"';
copy pg_dist_colocation from PROGRAM 'psql "host=192.168.6.13 port=5432 dbname=postgres user=postgres" -Atc "copy pg_dist_colocation to STDOUT"';

-- coordinator 导入数据
insert into tbl1(aid,bid,user_name) select id,id,substr(md5(id::text),1,30) from generate_series(1,10000000) t(id);
copy pgbench_accounts from '/home/postgres/pgbench_accounts.csv' with csv header;

-- 测试脚本
[postgres@clickhost_db_13 citus]$ cat citus_join_select.sql 
\set aid random(1 ,10000000)
select * from pgbench_accounts a,tbl1 b where a.aid = b.aid and a.aid = :aid

-- coordinator节点执行测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_join_select.sql -c 256 -j 64 -T 30

-- work节点1执行测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_join_select.sql -c 64 -j 64 -T 30

-- work节点2执行测试
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_join_select.sql -c 64 -j 64 -T 30

```

#### 4.2.3 测试结果

##### 1) PG测试结果

> - 数据量1亿
> - cpu使用100%

| Node               | Latency (ms) | Transactions per sec |
| ------------------ | ------------ | -------------------- |
| 32cores - 96GB RAM | 1.966        | 129,665              |

##### 2) citus测试结果

> - 数据量1亿
> - work节点上分别64个客户端,coordinator上256个客户端
> - coordinator上CPU达到100%
> - work节点上CPU达到95%

| 测试项        | 架构       | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| ------------- | ---------- | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| 分布表+参考表 | 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 3.058        | 83,621               |
| 分布表+参考表 | 单cn       | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 128   | 3.042        | 83,847               |
| 分布表+参考表 | masterless | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 32    | 2.31         | 151,138              |
| 分布表+参考表 | masterless | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 128   | 2.36         | 148,567              |

#### 4.2.2 分布表+分布表

## 5. 实际场景测试

> * 以下测试涉及masterless架构均采用citus MX table beta的方法

### 5.1 建立测试表

> * 32个字段
> * 4亿记录数据

```sql
CREATE TABLE wb10_user_mx
(
user_id numeric   NOT NULL,
user_type varchar(1)   NOT NULL,
user_name varchar(30)   NOT NULL,
password varchar(32)   NOT NULL,
IVR_passwd varchar(6)   NULL,
pwd_question varchar(30)   NULL,
pwd_answer varchar(30)   NULL,
real_name varchar(30)   NOT NULL,
sex varchar(1)   NOT NULL,
born_date timestamp   NULL,
country varchar(3)   NULL,
id_type varchar(1)   NOT NULL,
id_no varchar(35)   NOT NULL,
mobile_no varchar(15)   NOT NULL,
phone_no varchar(15)   NULL,
email varchar(30)   NOT NULL,
address varchar(255)   NULL,
postalcode varchar(6)   NULL,
is_active varchar(1)   NOT NULL,
check_code varchar(4)   NOT NULL,
last_login_time timestamp   NOT NULL,
total_times int   NOT NULL,
credit_class varchar(2)   NOT NULL,
if_receive varchar(1)   NOT NULL,
regist_time timestamp   NOT NULL,
is_valid varchar(1) DEFAULT  'Y'
 NOT NULL,
sale_mode varchar(1) DEFAULT   'E'
 NOT NULL,
login_channel varchar(1) DEFAULT  'E' NULL,
member_id varchar(30) DEFAULT  '*' NULL,
member_level varchar(1) DEFAULT  '*' NULL,
encourage_flag varchar(1) DEFAULT  '*' NULL,
phone_flag varchar(1) DEFAULT  '*' NULL,
check_id_flag varchar(1)   NULL,
user_status varchar(1)   NULL,
passenger_limit varchar(1)   NULL,
flag1 varchar(8)   NULL);

-- 建立索引
create index on WB10_user(user_id);
create index on user_name(user_id);
create index on WB10_user(phone_no);
create index on WB10_user(email);

-- coordinator 节点建立分布表
set citus.shard_count = 128;
set citus.shard_replication_factor = 1;
SELECT create_distributed_table('wb10_user_mx', 'user_id');
```

### 5.2 MX架构测试

```sql
CREATE TABLE wb10_user_mx
(
user_id numeric   NOT NULL,
user_type varchar(1)   NOT NULL,
user_name varchar(30)   NOT NULL,
password varchar(32)   NOT NULL,
IVR_passwd varchar(6)   NULL,
pwd_question varchar(30)   NULL,
pwd_answer varchar(30)   NULL,
real_name varchar(30)   NOT NULL,
sex varchar(1)   NOT NULL,
born_date timestamp   NULL,
country varchar(3)   NULL,
id_type varchar(1)   NOT NULL,
id_no varchar(35)   NOT NULL,
mobile_no varchar(15)   NOT NULL,
phone_no varchar(15)   NULL,
email varchar(30)   NOT NULL,
address varchar(255)   NULL,
postalcode varchar(6)   NULL,
is_active varchar(1)   NOT NULL,
check_code varchar(4)   NOT NULL,
last_login_time timestamp   NOT NULL,
total_times int   NOT NULL,
credit_class varchar(2)   NOT NULL,
if_receive varchar(1)   NOT NULL,
regist_time timestamp   NOT NULL,
is_valid varchar(1) DEFAULT  'Y'
 NOT NULL,
sale_mode varchar(1) DEFAULT   'E'
 NOT NULL,
login_channel varchar(1) DEFAULT  'E' NULL,
member_id varchar(30) DEFAULT  '*' NULL,
member_level varchar(1) DEFAULT  '*' NULL,
encourage_flag varchar(1) DEFAULT  '*' NULL,
phone_flag varchar(1) DEFAULT  '*' NULL,
check_id_flag varchar(1)   NULL,
user_status varchar(1)   NULL,
passenger_limit varchar(1)   NULL,
flag1 varchar(8)   NULL);

-- 建立索引
create index on WB10_user_mx(user_id);
create index on WB10_user_mx(user_name);
create index on WB10_user_mx(phone_no);
create index on WB10_user_mx(email);

-- coordinator 节点建立分布表
set citus.shard_count = 64;
set citus.shard_replication_factor = 1;
SET citus.replication_model TO streaming;
SELECT create_distributed_table('wb10_user_mx', 'user_id');

-- 开启同步元数据
select start_metadata_sync_to_node('192.168.6.11',5432);
select start_metadata_sync_to_node('192.168.6.12',5432);
```


### 5.3 生成测试数据

> * 地址信息采用中文生成函数

```sql
-- 生成中文地址函数
create or replace function gen_address(int) returns text as $$  
declare  
  res text;  
begin  
  if $1 >=1 then  
    select string_agg(chr(19968+(random()*20901)::int), '') into res from generate_series(1,$1);  
    return res;  
  end if;  
  return null;  
end;  
$$ language plpgsql strict;  

-- 生成身份证号码
create or replace function gen_id_no(  
id int
)   
returns text as $$  
select lpad((random()*99)::int::text, 2, '0') ||   
       lpad((random()*99)::int::text, 2, '0') ||   
       lpad((random()*99)::int::text, 2, '0') ||   
       to_char('2012-01-01'::timestamp -((id*4::int)::varchar || 's')::INTERVAL,'yyyymmdd') ||   
       lpad((random()*99)::int::text, 2, '0') ||   
       random()::int ||   
       (case when random()*10 >9 then 'X' else (random()*9)::int::text end ) ;  
$$ language sql strict;  

-- 插入测试数据
insert into wb10_user SELECT id as user_id,
LEFT(md5(id::text),1) as user_type,
LEFT(md5(id::text),30) as user_name,
md5(id::text) as password,
LEFT(md5(id::text),6) as ivr_passwd,
LEFT(md5(id::text),30) as pwd_question,
LEFT(md5(id::text),30) as pwd_answer,
LEFT(md5(id::text),30) as real_name,
random()::int as sex,
'2012-01-01'::timestamp -((id*4::int)::varchar || 's')::INTERVAL as born_date,
LEFT(md5(id::text),3) as country,
random()::int::text as id_type,
gen_id_no(id) as id_no,
LEFT(md5(id::text),12) as mobile_no,
LEFT(md5(id::text),11) as phone_no,
LEFT(md5(id::text),20) as email,
gen_address(20) as address,
LEFT(md5(id::text),6) as postalcode,
random()::int::text as is_active,
LEFT(md5(id::text),4) as check_code,
clock_timestamp() as last_login_time,
ceil(random()*10) as total_times,
LEFT(md5(id::text),2) as credit_class,
random()::int::text as if_receive,
clock_timestamp() - ((id::int)::varchar || 's')::INTERVAL as regist_time,
random()::int::text as is_valid,
random()::int::text as sale_mode,
chr(mod(id,26)+65) as login_channel,
LEFT(md5(id::text),30) as member_id,
random()::int::text as member_level,
random()::int::text as encourage_flag,
random()::int::text as phone_flag,
random()::int::text as check_id_flag,
random()::int::text as user_status,
random()::int::text as passenger_limit,
LEFT(md5(id::text),8) as flag1
from generate_series(1,400000000) id;

-- 上面数据生成太慢用以下方式生成
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import datetime
import time
import psycopg2
import multiprocessing

def gen_data(num_1,num_2):
    conn = psycopg2.connect(database="postgres", user="postgres", password="postgres", host="192.168.6.13", port="5432")
    cur = conn.cursor()
    sql = ("insert into wb10_user_test SELECT id as user_id,"
           "LEFT(md5(id::text),1) as user_type,LEFT(md5(id::text),30) as user_name,"
           "md5(id::text) as password,LEFT(md5(id::text),6) as ivr_passwd,"
           "LEFT(md5(id::text),30) as pwd_question,LEFT(md5(id::text),30) as pwd_answer,"
           "LEFT(md5(id::text),30) as real_name,random()::int as sex,"
           "'2012-01-01'::timestamp -((id*4::int)::varchar || 's')::INTERVAL as born_date,"
           "LEFT(md5(id::text),3) as country,random()::int::text as id_type,gen_id_no(id) as id_no,"
           "LEFT(md5(id::text),12) as mobile_no,LEFT(md5(id::text),11) as phone_no,"
           "LEFT(md5(id::text),20) as email,gen_address(20) as address,"
           "LEFT(md5(id::text),6) as postalcode,random()::int::text as is_active,"
           "LEFT(md5(id::text),4) as check_code,clock_timestamp() as last_login_time,"
           "ceil(random()*10) as total_times,LEFT(md5(id::text),2) as credit_class,"
           "random()::int::text as if_receive,clock_timestamp() - ((id::int)::varchar || 's')::INTERVAL as regist_time,"
           "random()::int::text as is_valid,random()::int::text as sale_mode,"
           "chr(mod(id,26)+65) as login_channel,LEFT(md5(id::text),30)"
           " as member_id,random()::int::text as member_level,random()::int::text as encourage_flag,"
           "random()::int::text as phone_flag,random()::int::text as check_id_flag,"
           "random()::int::text as user_status,random()::int::text as passenger_limit,"
           "LEFT(md5(id::text),8) as flag1 from generate_series("+ str(num_1) + "," + str(num_2) + ") id;")
    sql2 = ("insert into wb10_user_reference SELECT id as user_id,"
           "LEFT(md5(id::text),30) as user_name,LEFT(md5(id::text),12) as mobile_no,"
           "LEFT(md5(id::text),11) as phone_no,LEFT(md5(id::text),20) as email "
           "from generate_series("+ str(num_1) + "," + str(num_2) + ") id;")
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__' :
    start = time.time()
    numList = []
    mp = 10000000
    for i in xrange(40):
        print i * mp + 1, (i + 1) * mp
        num_1 = int(i * mp + 1)
        num_2 = int((i + 1) * mp)
        p = multiprocessing.Process(target=gen_data, args=(num_1, num_2,))
        numList.append(p)
        p.start()
        # print("process %d begin to execute" % p.pid)

    for p in numList:
        p.join()
        # print("process %d executed" % p.pid)

    end = time.time()
    print('use time:%d' % (end - start))
```

### 5.3 测试

#### 5.3.1 按照用户名分片

> * 用户名做分片键
> * 数据量4亿,大小236GB
>

```
-- 按照用户名查询测试脚本
[postgres@clickhost_db_12 citus]$ cat citus_user_name.sql 
\set id random(200000001 ,400000000)
SELECT * FROM  wb10_user_mx WHERE user_name = LEFT(md5(:id::text),30);

-- 按照手机号查询测试脚本
[postgres@clickhost_db_12 citus]$ cat citus_user_phone.sql 
\set id random(200000001 ,400000000)
SELECT * FROM  wb10_user_mx WHERE phone_no = LEFT(md5(:id::text),11);

-- 按照邮箱号查询测试脚本
[postgres@clickhost_db_12 citus]$ cat citus_user_mail.sql 
\set id random(200000001 ,400000000)
SELECT * FROM  wb10_user_mx WHERE email = LEFT(md5(:id::text),20);

-- pgbench用户名查询
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_user_name.sql -c 64 -j 64 -T 300

-- pgbench手机号查询
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_user_phone.sql -c 64 -j 64 -T 300
```

##### 1) 测试结果

| 分片字段  | 查询       | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| --------- | ---------- | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| user_name | 用户名查询 | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 64    | 1.98         | 64566                |
| user_name | 手机号查询 | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 64    | 985          | 62                   |
| user_name | 邮箱号查询 | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 64    | 984          | 62                   |

##### 2) 测试异常记录

> * 在使用手机号或者邮箱查询时,出现如下告警,同时网络连接出现大量的 TIME_WAIT
>
> ```
> WARNING:  could not establish asynchronous connection after 5000 ms
> ```
>
> * 调整如下系统参数,系统中TIME_WAIT大量变少,但实际测试TPS相当低
>
> ```
> sysctl -w net.ipv4.tcp_tw_reuse=1
> sysctl -w net.ipv4.tcp_tw_recycle=1
> ```
> * 实际用psql测试,平均在30ms左右
> ```
>  postgres=#  SELECT * FROM  wb10_user_mx WHERE phone_no = LEFT(md5(40000::text),11);
>  user_id | user_type |           user_name            |             password             | ivr_passwd |          pwd_question          |           pwd_answer
>            |           real_name            | sex |      born_date      | country | id_type |       id_no        |  mobile_no   |  phone_no   |        email 
>         |                 address                  | postalcode | is_active | check_code |      last_login_time       | total_times | credit_class | if_recei
> ve |        regist_time         | is_valid | sale_mode | login_channel |           member_id            | member_level | encourage_flag | phone_flag | check_
> id_flag | user_status | passenger_limit |  flag1   
> ---------+-----------+--------------------------------+----------------------------------+------------+--------------------------------+---------------------
> -----------+--------------------------------+-----+---------------------+---------+---------+--------------------+--------------+-------------+--------------
> --------+------------------------------------------+------------+-----------+------------+----------------------------+-------------+--------------+---------
> ---+----------------------------+----------+-----------+---------------+--------------------------------+--------------+----------------+------------+-------
> --------+-------------+-----------------+----------
>    40000 | 7         | 7c77f048a2d02e784926184a82686f | 7c77f048a2d02e784926184a82686fa0 | 7c77f0     | 7c77f048a2d02e784926184a82686f | 7c77f048a2d02e784926
> 184a82686f | 7c77f048a2d02e784926184a82686f | 0   | 2011-12-30 03:33:20 | 7c7     | 0       | 483299201112309300 | 7c77f048a2d0 | 7c77f048a2d | 7c77f048a2d02
> e784926 | 摸鱱栭揪魿呟躢耦嬹悦酠诲翨耬憞嵦悵铇懝嗠 | 7c77f0     | 1         | 7c77       | 2018-05-07 16:04:56.359094 |           4 | 7c           | 0       
>    | 2018-05-07 04:58:16.359094 | 0        | 1         | M             | 7c77f048a2d02e784926184a82686f | 1            | 0              | 1          | 1     
>         | 1           | 1               | 7c77f048
> (1 row)
> 
> Time: 31.886 ms
> ```

#### 5.3.2 本地表 + 分布表关联查询测试

> * 本地表包含用户名,手机号,邮箱
> * 本地表和分布表关联查询

```
-- 在work节点建立本地表
create table wb10_user_local as select  user_id,user_name,mobile_no,phone_no,email from wb10_user_mx;

create index ON wb10_user_local(user_name);
create index ON wb10_user_local(phone_no);
create index ON wb10_user_local(email);

-- 测试脚本
[postgres@clickhost_db_12 citus]$ cat citus_user_sub.sql 
\set id random(1 ,200000000)
SELECT * FROM  wb10_user_mx WHERE user_name in(SELECT user_name FROM  wb10_user_local WHERE phone_no = LEFT(md5(:id::text),11));
```

##### 1) 测试结果

| 分片字段  | 查询   | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| --------- | ------ | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| user_name | 子查询 | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 64    | 635          | 45                   |
##### 2) 测试异常记录

> * 使用子查询是报如下错误,大量的短连接造成错误
>
> ```
> WARNING:  connection error: 192.168.6.11:5432
> DETAIL:  FATAL:  sorry, too many clients already
> ```
>
> * 实际psql测试,35ms出结果
>
> ```
> postgres=#  SELECT * FROM  wb10_user_mx WHERE user_name in(SELECT user_name FROM  wb10_user_local WHERE phone_no = LEFT(md5(100::text),11));
>  user_id | user_type |           user_name            |             password             | ivr_passwd |          pwd_question          |           pwd_answer           |  
>          real_name            | sex |      born_date      | country | id_type |       id_no        |  mobile_no   |  phone_no   |        email         |                 ad
> dress                  | postalcode | is_active | check_code |      last_login_time       | total_times | credit_class | if_receive |        regist_time         | is_valid
>  | sale_mode | login_channel |           member_id            | member_level | encourage_flag | phone_flag | check_id_flag | user_status | passenger_limit |  flag1   
> ---------+-----------+--------------------------------+----------------------------------+------------+--------------------------------+--------------------------------+--
> ------------------------------+-----+---------------------+---------+---------+--------------------+--------------+-------------+----------------------+-------------------
> -----------------------+------------+-----------+------------+----------------------------+-------------+--------------+------------+----------------------------+---------
> -+-----------+---------------+--------------------------------+--------------+----------------+------------+---------------+-------------+-----------------+----------
>      100 | f         | f899139df5e1059396431415e770c6 | f899139df5e1059396431415e770c6dd | f89913     | f899139df5e1059396431415e770c6 | f899139df5e1059396431415e770c6 | f
> 899139df5e1059396431415e770c6 | 1   | 2011-12-31 23:53:20 | f89     | 0       | 107493201112317307 | f899139df5e1 | f899139df5e | f899139df5e105939643 | 褚猽庽诔磯陝緛譂媋
> 砊軳胨碱締龎鵜蜍讥鶒恈 | f89913     | 0         | f899       | 2018-05-07 16:04:54.308512 |           8 | f8           | 0          | 2018-05-07 16:03:14.308513 | 1       
>  | 1         | W             | f899139df5e1059396431415e770c6 | 1            | 0              | 1          | 0             | 0           | 0               | f899139d
> (1 row)
> 
> Time: 34.576 ms
> ```

#### 5.3.3 本地表+分布表+存储过程

> * 先从本地表根据手机号查出用户名,在根据用户名从分布表中查出结果

```sql
-- 测试函数
CREATE OR REPLACE FUNCTION get_user_info(id int)
 RETURNS SETOF wb10_user_mx
 LANGUAGE plpgsql
AS $function$
DECLARE
v_phone_no varchar := LEFT(md5(id::text),11);
v_user_name varchar;

BEGIN
select user_name into v_user_name from wb10_user_local where wb10_user_local.phone_no = v_phone_no;
-- raise info 'v_user_name:%',v_user_name;
return query select * from wb10_user_mx where user_name = v_user_name;

END;
$function$

-- 所有节点上创建函数
SELECT run_command_on_workers($cmd$ CREATE OR REPLACE FUNCTION public.get_user_info(id integer)
 RETURNS SETOF wb10_user_mx
 LANGUAGE plpgsql
AS $function$
DECLARE
v_phone_no varchar := LEFT(md5(id::text),11);
v_user_name varchar;

BEGIN
select user_name into v_user_name from wb10_user_local where wb10_user_local.phone_no = v_phone_no;
-- raise info 'v_user_name:%',v_user_name;
return query select * from wb10_user_mx where user_name = v_user_name;
END;
$function$
$cmd$);

-- 测试脚本
[postgres@clickhost_db_12 citus]$ cat citus_user_2_query.sql 
\set id random(1 ,400000000)
SELECT * FROM  get_user_info(:id);

-- pgbench测试语句

pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_user_2_query.sql -c 64 -j 64 -T 30

```

##### 1) 测试结果

> * 一个work节点

| 分片字段  | 查询             | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| --------- | ---------------- | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| user_name | 手机号或者邮箱号 | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 64    | 2.67         | 23929                |
#### 5.3.4 参考表+分布表+存储过程

> * 本地表+分布表虽然能达到RT要求但是只能在一个work节点查询,如果每个work节点都存在一份数据则数据一致性维护比较麻烦,现采用

```sql
-- 所有节点上创建测试函数
SELECT run_command_on_workers($cmd$ CREATE OR REPLACE FUNCTION public.get_user_info_reference(id integer)
 RETURNS SETOF wb10_user_mx
 LANGUAGE plpgsql
AS $function$
DECLARE
v_phone_no varchar := LEFT(md5(id::text),11);
v_user_name varchar;

BEGIN
select user_name into v_user_name from wb10_user_reference where wb10_user_reference.phone_no = v_phone_no;
-- raise info 'v_user_name:%',v_user_name;
return query select * from wb10_user_mx where user_name = v_user_name;
END;
$function$
$cmd$);

-- 测试脚本
[postgres@clickhost_db_11 citus]$ vim citus_user_reference.sql 
\set id random(1 ,400000000)
SELECT * FROM  get_user_info_reference(:id);

-- pgbench 测试语句
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_user_reference.sql -c 64 -j 64 -T 30
```

##### 1) 测试结果
| 分片字段  | 查询             | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| --------- | ---------------- | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| user_name | 手机号或者邮箱号 | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 64    | 4.79         | 26940                |

#### 5.3.5 参考表+分布表+子查询

```sql
-- 测试脚本
[postgres@clickhost_db_11 citus]$ vim citus_user_reference_sub.sql 
\set id random(1 ,400000000)
SELECT * FROM  wb10_user_mx WHERE user_name in(SELECT user_name  FROM  wb10_user_reference WHERE phone_no = LEFT(md5(:id::text),11));

-- pgbench 测试语句
pgbench -M simple -n -r -P 1 -f /home/postgres/citus/citus_user_2_query.sql -c 64 -j 64 -T 30
```

##### 1) 测试结果

| 分片字段  | 查询   | Coordinator Node   | Worker Nodes           | shard | Latency (ms) | Transactions per sec |
| --------- | ------ | ------------------ | ---------------------- | ----- | ------------ | -------------------- |
| user_name | 子查询 | 32cores - 96GB RAM | 2*(32 core - 96GB RAM) | 64    | 990          | 61                   |
