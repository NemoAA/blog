# 在PostgreSQL中检测慢速查询的3种方法

> 本文翻译自：<https://www.cybertec-postgresql.com/en/3-ways-to-detect-slow-queries-in-postgresql/>

在深入研究PostgreSQL性能时，我们非常希望了解到是哪个点导致性能问题，以及服务器上究竟发生了什么。因此，找到慢查询和性能瓶颈点正是本文章目的所在。 

有许多方法可以解决性能问题。但是，已经证明有三种方法对于快速定位问题非常有用。以下是我处理性能问题的三大建议：

- 使用慢查询日志
- 使用auto_explain检查执行计划
- 依赖于pg_stat_statements中相关的统计信息

![](https://www.cybertec-postgresql.com/wp-content/uploads/2018/08/Performance_analysis-01-1024x808.jpg)

这篇文章将会就分析PostgreSQL性能及瓶颈问题的每种方法的优点和缺点进行讨论。

## 1. 利用PostgreSQL慢查询日志

传统定位慢查询的方法是利用PostgreSQL的慢查询日志。这个方法是：当查询超过一定的时间，会将此查询记录到日志中。这种方法让慢查询非常容易的被发现，同时方便开发人员和管理员可以快速响应并知道在哪里查看。

慢查询日志默认是关闭的，因此有必要打开它。打开慢日志有几种选择：如果要打开全局慢查询日志，可以更改postgresql.conf配置文件：

```
log_min_duration_statement = 5000
```

如果在postgresql.conf配置文件中将log_min_duration_statement设置为5000，PostgreSQL会认为5秒以上的查询为慢查询并将它们写入到日志文件。在postgresql.conf中更改此配置，不需要重启数据库，只需“reload”即可生效：

```
postgres=# SELECT pg_reload_conf();
 pg_reload_conf 
----------------
 t 
(1 row) 
```

可以使用`pg_ctl reload`脚本或通过调用上述SQL函数来执行reload操作。

如果修改postgresql.conf配置文件，那么会对整个实例生效，在大多数情况下可能日志量太多了。你可能想要更精确的日志。因此，针对某一个特定的用户或某一个特定数据库进行修改会更有意义：

```
postgres=# ALTER DATABASE test SET log_min_duration_statement = 5000;
ALTER DATABASE
```

`ALTER DATABASE`命令允许修改单个数据库的参数。现在让我们重新连接并运行一个慢查询：

```
postgres=# \c test
You are now connected to database "test" as user "hs".
test=# SELECT pg_sleep(10);
pg_sleep
----------
 
(1 row)
```

在我的例子中，我使用`pg_sleep`来让查询等待10秒。当检查日志时，我们可以看到期望的日志信息：

```
2018-08-20 08:19:28.151 CEST [22845] LOG: duration: 10010.353 ms statement: SELECT pg_sleep(10);
```

现在可以记录语句并分析它为什么慢。一个比较好方法是运行`explain analyze`来实际运行语句并提供执行计划。

慢查询日志的优势是可以及时的检查一个慢查询。当有超过阈值的慢查询出现时，你可以立即对单个语句做出反应。然而，这是这种方法的优点同时也是它的缺点。慢查询日志只能记录一个个单独的语句，如果糟糕的性能是由一堆不那么慢的语句造成的？我们可以认定10秒的查询是高成本的查询，但是当运行100万个查询，每个都需要500毫秒呢？所有这些查询都不会在慢查询日志中出现，因为它们仍然被认为是“快”的。但是，你可能会在慢查询日志中发现备份、创建索引、批量加载等等。如果你只依赖缓慢的查询日志，那么你可能永远无法找到根本原因。因此，慢查询日志的用途是跟踪单个慢语句。

## 2. 检查不稳定的执行计划

这同样适用于我们的下一个方法。有时候数据库性能很好，但偶尔会出现查询异常的现象。为了找到这些查询并进行修复，通常我们会使用`auto_explain`模块。

它的功能类似于慢速查询日志：当有慢查询时，就会记录在日志中。但是`auto_explain`会在日志文件中记录完整的执行计划 - 而不仅仅是查询。为什么这很重要？请看以下示例：

```
test=# CREATE TABLE t_demo AS
          SELECT * FROM generate_series(1, 10000000) AS id;
SELECT 10000000
test=# CREATE INDEX idx_id ON t_demo (id);
CREATE INDEX
test=# ANALYZE;
ANALYZE
```

我刚刚创建有1000万行记录的表。此外，还定义了一个索引。让我们来看看两个几乎完全相同的查询：

```
test=# explain SELECT * FROM t_demo WHERE id < 10;
                                    QUERY PLAN
---------------------------------------------------------------------------
Index Only Scan using idx_id on t_demo (cost=0.43..8.61 rows=10 width=4)
    Index Cond: (id < 10)
(2 rows)
 
test=# explain SELECT * FROM t_demo WHERE id < 1000000000;
QUERY PLAN
------------------------------------------------------------------
 Seq Scan on t_demo (cost=0.00..169248.60 rows=10000048 width=4)
     Filter: (id < 1000000000)
JIT:
     Functions: 2
     Inlining: false
     Optimization: false
(6 rows)
```

这两个查询基本相同，但PostgreSQL将使用完全不同的执行计划。第一个查询只获取少量数据，因此会进行索引扫描。第二个查询将会获取所有数据，因此选择顺序扫描。虽然查询看起来很相似，但运行时将完全不同。第一个查询将在毫秒级执行完，而第二个查询可能需要长达半秒甚至一秒左右的时间（取决于硬件，负载，缓存等等）。现在的麻烦是：当数据库参数配置合适，一百万个查询也可能很快 - 但是，在一些罕见的情况下，可能有些人想要进行的查询，会导致糟糕的执行计划或者返回大量数据。

要找到一个不管出于何种原因的都需要花费很长时间的查询,可以使用auto_explain模块。这里的做法是：如果查询时间超过了某个阈值，PostgreSQL可以将查询计划写入到日志文件中，以便稍后检查。

这是一个例子：

```
test=# LOAD 'auto_explain';
LOAD
test=# SET auto_explain.log_analyze TO on;
SET
test=# SET auto_explain.log_min_duration TO 500;
SET
```

LOAD命令将把auto_explain模块加载到数据库连接中。在演示中，我们可以很容易地做到这一点。在生产系统中，我们应该使用postgresql.conf配置文件或者使用ALTER DATABASE / ALTER TABLE命令加载模块。如果你想在postgresql.conf中进行修改，考虑添加以下行到配置文件:

```
session_preload_libraries = 'auto_explain';
```

默认情况下session_preload_libraries确保为每个数据库连接加载此模块（应该是数据库新连接生效，已经存在的连接不生效）。这样就不再需要LOAD命令了。一旦更改了配置(不要忘记调用`pg_reload_conf()`)，你可以尝试运行以下查询：

```
test=# SELECT count(*) FROM t_demo GROUP BY id % 2;
  count
---------
 5000000
 5000000
(2 rows)
```

查询将需要超过500毫秒，因此`auto_explain`信息会在日志文件中显示：

```
2018-08-20 09:51:59.056 CEST [23256] LOG: duration: 4280.595 ms plan:
      Query Text: SELECT count(*) FROM t_demo GROUP BY id % 2;
      GroupAggregate (cost=1605370.36..1805371.32 rows=10000048 width=12)
            (actual time=3667.207..4280.582 rows=2 loops=1)
       Group Key: ((id % 2))
       -> Sort (cost=1605370.36..1630370.48 rows=10000048 width=4)
               (actual time=3057.351..3866.446 rows=10000000 loops=1)
          Sort Key: ((id % 2))
          Sort Method: external merge Disk: 137000kB
          -> Seq Scan on t_demo (cost=0.00..169248.60 rows=10000048 width=4)
                  (actual time=65.470..876.695 rows=10000000 loops=1)
```

你可以看到一个完整的`auto_explain`信息写入到了日志文件中。

这种方法的优点是，当查询采用一个糟糕的计划时，你可以深入查看并分析某些慢查询。但是，仍然很难去收集全部的信息，因为可能有数百万个查询在系统上运行。

## 3. 检查 pg_stat_statements

第三种方法是使用pg_stat_statements。使用pg_stat_statements的思路是分组标记你的查询，也就是在一个系统视同上使用不同的参数聚集系统的运行时信息。

在我看来，pg_stat_statements就是一把瑞士军刀。它能够帮助你理解你系统当前到底运行得怎样。为了能启用pg_stat_statements，你需要在postgresql.conf中添加以下行并重启你的服务：

```
shared_preload_libraries = 'pg_stat_statements'
```

然后在数据库中运行“CREATE EXTENSION pg_stat_statements”。数据库会为你创建一个视图：

```
test=# CREATE EXTENSION pg_stat_statements;
CREATE EXTENSION
test=# \d pg_stat_statements
View "public.pg_stat_statements"
       Column        |       Type       | Collation | Nullable | Default
---------------------+------------------+-----------+----------+---------
userid               | oid              |           |          |
dbid                 | oid              |           |          |
queryid              | bigint           |           |          |
query                | text             |           |          |
calls                | bigint           |           |          |
total_time           | double precision |           |          |
min_time             | double precision |           |          |
max_time             | double precision |           |          |
mean_time            | double precision |           |          |
stddev_time          | double precision |           |          |
rows                 | bigint           |           |          |
shared_blks_hit      | bigint           |           |          |
shared_blks_read     | bigint           |           |          |
shared_blks_dirtied  | bigint           |           |          |
shared_blks_written  | bigint           |           |          |
local_blks_hit       | bigint           |           |          |
local_blks_read      | bigint           |           |          |
local_blks_dirtied   | bigint           |           |          |
local_blks_written   | bigint           |           |          |
temp_blks_read       | bigint           |           |          |
temp_blks_written    | bigint           |           |          |
blk_read_time        | double precision |           |          |
blk_write_time       | double precision |           |          |
```

这个视图会告诉我们，哪类查询被以何种频度运行，并告诉我们这类查询的总运行耗时以及每类查询的运行次数分布情况。之后我们可以分析pg_stat_statements提供的这些数据。不久前笔者的博文[a blog post about this issue](https://www.cybertec-postgresql.com/en/pg_stat_statements-the-way-i-like-it/)讨论了这块相关的用法。

这个模块先进的地方在于你还有能力找到大量的比较快速的查询，它们可能就是导致系统负载高的原因。另外，pg_stat_statements也能够告诉你不同类型的查询的I/O行为。不过缺点是它无法到底是哪些独立的通常比较快而偶尔变慢。由于pg_stat_statements不包含参数，我的一个同事（Julian Markwort）正在开发一个用于PostgreSQL 12的补丁用于修复这个问题。

## **总结**

在PostgreSQL中追踪慢速的查询和瓶颈很容易，不过我们事先假设你知道使用哪种技术。本文只是简单地让你快速知道可能的信息以及在遇到性能问题时可以做什么。