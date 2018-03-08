## E.1.2. Changes

### 1. CVE-2018-1058

> 参考德哥博客地址<https://github.com/digoal/blog/blob/master/201803/20180302_02.md>

> - Document how to configure installations and applications to guard against search-path-dependent trojan-horse attacks from other users (Noah Misch)
>
>   Using a `search_path` setting that includes any schemas writable by a hostile user enables that user to capture control of queries and then run arbitrary SQL code with the permissions of the attacked user. While it is possible to write queries that are proof against such hijacking, it is notationally tedious, and it's very easy to overlook holes. Therefore, we now recommend configurations in which no untrusted schemas appear in one's search path. Relevant documentation appears in [Section 5.8.6](https://www.postgresql.org/docs/current/static/ddl-schemas.html#DDL-SCHEMAS-PATTERNS) (for database administrators and users), [Section 33.1](https://www.postgresql.org/docs/current/static/libpq-connect.html) (for application authors), [Section 37.15.1](https://www.postgresql.org/docs/current/static/extend-extensions.html#EXTEND-EXTENSIONS-STYLE) (for extension authors), and [CREATE FUNCTION](https://www.postgresql.org/docs/current/static/sql-createfunction.html) (for authors of `SECURITY DEFINER` functions). (CVE-2018-1058)
>
> - Avoid use of insecure `search_path` settings in pg_dump and other client programs (Noah Misch, Tom Lane)
>
>   pg_dump, pg_upgrade, vacuumdb and other PostgreSQL-provided applications were themselves vulnerable to the type of hijacking described in the previous changelog entry; since these applications are commonly run by superusers, they present particularly attractive targets. To make them secure whether or not the installation as a whole has been secured, modify them to include only the `pg_catalog` schema in their `search_path` settings. Autovacuum worker processes now do the same, as well.
>
>   In cases where user-provided functions are indirectly executed by these programs — for example, user-provided functions in index expressions — the tighter `search_path` may result in errors, which will need to be corrected by adjusting those user-provided functions to not assume anything about what search path they are invoked under. That has always been good practice, but now it will be necessary for correct behavior. (CVE-2018-1058)



### 2. Prevent logical replication from trying to ship changes for unpublishable relations (Peter Eisentraut)

> 物化视图与逻辑复制不兼容

#### 2.1 场景重现

```
-- 创建发布端和订阅端数据目录并初始化
mkdir pub sub 

initdb pub 
initdb sub 

echo "wal_level = logical" >> pub/postgresql.conf 
echo "wal_level = logical" >> sub/postgresql.conf 

-- 启动数据库
pg_ctl -D pub -l pub.log -o "-p 5433" start 
pg_ctl -D sub -l sub.log -o "-p 5434" start 

--发布端和订阅端创建测试用表
psql -p 5433 -d postgres -c "CREATE TABLE testtable (id int,value text);" 
psql -p 5434 -d postgres -c "CREATE TABLE testtable (id int,value text);" 

-- 创建发布端和订阅端
psql -p 5433 -d postgres -c "CREATE PUBLICATION pub FOR ALL TABLES;" 
psql -p 5434 -d postgres -c "CREATE SUBSCRIPTION sub CONNECTION 'host=localhost port=5433 dbname=postgres' PUBLICATION pub;" 

-- 插入数据
psql -p 5433 -d postgres -c "INSERT INTO testtable (id,value) VALUES (1,'string');" 
psql -p 5433 -d postgres -c "SELECT state,sent_lsn,write_lsn,flush_lsn,replay_lsn FROM pg_stat_replication;" 

-- 发布端创建物化视图
psql -p 5433 -d postgres -c "CREATE MATERIALIZED VIEW mvid AS SELECT id FROM testtable;" 
```

#### 2.2 报错日志

> 物化视图创建后复制被破坏，订阅端日志显示这些错误：

```
2018-03-06 19:17:52.642 CST [34358] ERROR:  logical replication target relation "public.mvid" does not exist
2018-03-06 19:17:52.644 CST [33784] LOG:  worker process: logical replication worker for subscription 16390 (PID 34358) exited with exit code 1
```

#### 2.3 详细讨论

<http://www.postgresql-archive.org/BUG-15044-materialized-views-incompatibility-with-logical-replication-in-postgres-10-td6004138.html#a6004141>

### 3.Fix misbehavior of concurrent-update rechecks with CTE references appearing in subplans (Tom Lane) 

> 当在查询的一部分中更新带有惟一索引的表时,在某些情况下，查询报告更新了不止一行

#### 3.1 场景重现

```
test=> create table tmp_test(id int not null, test text not null); 
CREATE TABLE 
test=> create unique index on tmp_test(id); 
CREATE INDEX 
test=> INSERT INTO tmp_test VALUES (1, 'test'); 
INSERT 0 1 
test=> create table tmp_test2(id int not null, test text not null); 
CREATE TABLE 

test=> WITH updated AS (UPDATE tmp_test SET test = 'test' WHERE id = 1 RETURNING id), inserted AS (INSERT INTO tmp_test2 (id, test) SELECT 1, 'test' WHERE NOT EXISTS (SELECT 1 FROM updated) RETURNING id) SELECT * FROM updated; 
 id 
---- 
  1 
(1 row) 

--  预期结果应该如下
test=> begin; 
BEGIN 
test=> UPDATE tmp_test SET test = 'test' WHERE id = 1; 
UPDATE 1 
test=> commit; 
COMMIT 

-- BUT实际结果是
test=> WITH updated AS (UPDATE tmp_test SET test = 'test' WHERE id = 1 RETURNING id), inserted AS (INSERT INTO tmp_test2 (id, test) SELECT 1, 'test' WHERE NOT EXISTS (SELECT 1 FROM updated) RETURNING id) SELECT * FROM updated; 

 id 
---- 
  1 
  1 
(2 rows) 
```

#### 3.2 详细讨论

<http://www.postgresql-archive.org/BUG-14870-wrong-query-results-when-using-WITH-with-UPDATE-td5989125.html#a6006245>

### 4. Fix planner failures with overlapping mergejoin clauses in an outer join (Tom Lane)

#### 4.1 场景重现

```
CREATE TABLE J1_TBL ( 
i integer, 
j integer, 
t text 
); 
CREATE TABLE J2_TBL ( 
i integer, 
k integer 
); 
set enable_hashjoin to off; 
explain select * from j1_tbl full join (select * from j2_tbl order by j2_tbl.i desc, j2_tbl.k) j2_tbl on j1_tbl.i = j2_tbl.i and j1_tbl.i = j2_tbl.k; 
ERROR:  left and right pathkeys do not match in mergejoin 
```

#### 4.2 详细讨论

<http://www.postgresql-archive.org/ERROR-left-and-right-pathkeys-do-not-match-in-mergejoin-td6006784.html>

### 5. Repair pg_upgrade's failure to preserve `relfrozenxid` for materialized views (Tom Lane, Andres Freund)

> 刷新物化视图可能会导致"could not access status of transaction"问题

#### 5.1 报错信息

```
2017-10-01 04:53:54 MSK 16183 @ from  [vxid:48/16835960 txid:0][] ERROR: 
could not access status of transaction 657045744 
2017-10-01 04:53:54 MSK 16183 @ from  [vxid:48/16835960 txid:0][] DETAIL: 
Could not open file "pg_clog/0272": No such file or directory. 
2017-10-01 04:53:54 MSK 16183 @ from  [vxid:48/16835960 txid:0][] CONTEXT: 
automatic vacuum of table "dbname.pg_toast.pg_toast_605700155 
```

#### 5.2 详细讨论

<http://www.postgresql-archive.org/pg-upgrade-and-materialized-views-td6006599.html>

<http://www.postgresql-archive.org/BUG-14852-Refreshing-materialized-view-might-lead-to-a-problem-quot-could-not-access-status-of-trans-td5987980.html>

### 6. Fix incorrect pg_dump output for some non-default sequence limit values (Alexey Bashtanov)

> 此bug受影响的版本为10.x稳定版本,9.4..9.6之间的版本不受影响

#### 6.1 场景重现

```
[postgres@JDu4e00u53f7 ~]$ psql -c 'select version()'
                                                 version                                                 
---------------------------------------------------------------------------------------------------------
 PostgreSQL 10.1 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 4.8.5 20150623 (Red Hat 4.8.5-16), 64-bit
(1 row)

[postgres@JDu4e00u53f7 ~]$ psql -c 'DROP SEQUENCE IF EXISTS foo'
NOTICE:  sequence "foo" does not exist, skipping
DROP SEQUENCE
[postgres@JDu4e00u53f7 ~]$ psql -c 'CREATE SEQUENCE foo INCREMENT BY -1 MINVALUE -9223372036854775808 MAXVALUE 9223372036854775807'
CREATE SEQUENCE
[postgres@JDu4e00u53f7 ~]$ pg_dump -t foo > tmp
[postgres@JDu4e00u53f7 ~]$ psql -c 'DROP SEQUENCE foo'
DROP SEQUENCE
[postgres@JDu4e00u53f7 ~]$ psql <tmp
SET
SET
SET
SET
SET
SET
SET
SET
SET
ERROR:  START value (9223372036854775807) cannot be greater than MAXVALUE (-1)
ERROR:  relation "foo" does not exist
ERROR:  relation "foo" does not exist
LINE 1: SELECT pg_catalog.setval('foo', 9223372036854775807, false);
```

```
[postgres@clickhost_db_11 ~]$ psql -c 'select version()'
                                                 version                                                 
---------------------------------------------------------------------------------------------------------
 PostgreSQL 10.3 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 4.8.5 20150623 (Red Hat 4.8.5-11), 64-bit
(1 row)

[postgres@clickhost_db_11 ~]$ psql -c 'DROP SEQUENCE IF EXISTS foo'
DROP SEQUENCE
[postgres@clickhost_db_11 ~]$ psql -c 'CREATE SEQUENCE foo INCREMENT BY -1 MINVALUE -9223372036854775808 MAXVALUE 9223372036854775807'
CREATE SEQUENCE
[postgres@clickhost_db_11 ~]$ pg_dump -t foo > tmp
[postgres@clickhost_db_11 ~]$ psql -c 'DROP SEQUENCE foo'
DROP SEQUENCE
[postgres@clickhost_db_11 ~]$ psql <tmp
SET
SET
SET
SET
SET
 set_config 
------------
 
(1 row)

SET
SET
SET
CREATE SEQUENCE
ALTER TABLE
       setval        
---------------------
 9223372036854775807
(1 row)
```

#### 6.2 详细讨论

<https://www.postgresql.org/message-id/cb85a9a5-946b-c7c4-9cf2-6cd6e25d7a33@imap.cc>

### 7. Fix pg_dump's mishandling of `STATISTICS` objects (Tom Lane)

> 修复pg_dump处理扩展统计信息的对象的各种错误。
>
> pg_dump统计信息的对象必须在相同的模式表上
>
> pg_dump统计信息的对象必须是相同的所有者

#### 7.2 详细讨论

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5c9f2564fabbc770ead3bd92136fdafc43654f27>

<http://www.postgresql-archive.org/Bogosities-in-pg-dump-s-extended-statistics-support-td6005336.html>

### 8. Fix incorrect reporting of PL/Python function names in error `CONTEXT` stacks (Tom Lane)

#### 8.1 场景重现

> 环境信息: SunOS, Release 5.10, KernelID Generic_141444-09. 

```
./configure CC="ccache gcc" CFLAGS="-m64 -I/opt/csw/include" 
PKG_CONFIG_PATH="/opt/csw/lib/pkgconfig:/usr/local/lib/pkgconfig" 
LDFLAGS="-L/opt/csw/lib/sparcv9 -L/usr/local/lib/64" --enable-cassert 
--enable-debug --enable-nls --enable-tap-tests --with-perl --with-tcl 
--with-python --with-gssapi --with-openssl --with-ldap --with-libxml 
--with-libxslt --with-icu 
gmake > make_results.txt 
gmake -C src/pl/plpython check 

Binary search has shown that this failure begins with commit 
8561e4840c81f7e345be2df170839846814fa004 (Transaction control in PL 
procedures.). On the previous commit 
(b9ff79b8f17697f3df492017d454caa9920a7183) there's no 
plpython_transaction test and plpython check passes. 
```

#### 8.2 详细讨论

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e748e902def40ee52d1ef0b770fd24aa0835e304>

<http://www.postgresql-archive.org/master-plpython-check-fails-on-Solaris-10-td6005563.html>

### 9. Allow `contrib/auto_explain`'s `log_min_duration` setting to range up to `INT_MAX`, or about 24 days instead of 35 minutes (Tom Lane) 

> 10.3版本之前 auto_explain.log_min_duration最大值只能为2147483,对于用PG做数仓,此值不能设置过大

#### 9.1 场景重现

```
-- 设置 auto_explain.log_min_duration 超过2147483,例如设置为2147484
vim $PGDATA/postgresql.conf

shared_preload_libraries = 'auto_explain'
auto_explain.log_min_duration = 2147484

-- 日志报错信息如下
[postgres@JDu4e00u53f7 pgdata]$ pg_ctl -mf restart
waiting for server to shut down.... done
server stopped
waiting for server to start....2018-03-07 12:10:06.414 CST [26388] WARNING:  2147484 is outside the valid range for parameter "auto_explain.log_min_duration" (-1 .. 2147483)
```

#### 9.2 详细讨论

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8af87f411c151537b6e3315c2a191110c3fec494>

<http://www.postgresql-archive.org/maximum-for-auto-explain-log-min-duration-doesn-t-seem-to-make-sense-td6007160.html#a6007173>

### 10. Mark assorted GUC variables as `PGDLLIMPORT`, to ease porting extension modules to Windows (Metin Doslu) 

> 增加windows平台上相关参数

#### 10.1 详细讨论

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=935dee9ad5a8d12f4d3b772a6e6c99d245e5ad44>

<http://www.postgresql-archive.org/Add-PGDLLIMPORT-to-enable-hashagg-td6004487.html>
