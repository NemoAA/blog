# 在PostgreSQL 中调整Autovacuum 和Autovacuum 技术内幕

> 本文翻译自[Tuning Autovacuum in PostgreSQL and Autovacuum Internals](https://www.percona.com/blog/2018/08/10/tuning-autovacuum-in-postgresql-and-autovacuum-internals/#spu-33080)

PostgreSQL数据库的性能可能会因`dead tuple`受到影响,因为它们会持续占用空间并导致表膨胀.我们在之前的[博客](https://www.percona.com/blog/2018/08/06/basic-understanding-bloat-vacuum-postgresql-mvcc/)中介绍了VACUUM和膨胀.现在,现在是时候了解PostgreSQL的`autovacuum`内部原理,来满足应用程序要求的高性能PostgreSQL数据库.

## 1. 什么是autovacuum?

`Autovacuum`随PostgreSQL启动的后台进程之一.在下面的日志中可以看到 `pid` 为2862（PostgreSQL主进程）启动了`pid`为2868的`autovacuum launcher` 子进程。要启动`autovacuum`,必须将参数`autovacuum`设置为ON。实际上,除非您100％确定正在做什么及其影响,否则不应在生产系统中将其设置为OFF.

```
avi@percona:~$ps -eaf | egrep "/post|autovacuum"
postgres  2862     1  0 Jun17 pts/0    00:00:11 /usr/pgsql-10/bin/postgres -D /var/lib/pgsql/10/data
postgres  2868  2862  0 Jun17 ?        00:00:10 postgres: autovacuum launcher process
postgres 15427  4398  0 18:35 pts/1    00:00:00 grep -E --color=auto /post|autovacuum
```

## 2. 为什么需要autovacuum ? 

我们需要`VACUUM`来删除垃圾数据,以便之后的`INSERT/UPDATE`可以重用垃圾数据占用的空间.如果想要了解有`dead tuple`和膨胀的更多信息,请阅读我们之前的[博客](https://www.percona.com/blog/2018/08/06/basic-understanding-bloat-vacuum-postgresql-mvcc/).同样我们还需要`ANALYZE`来更新表上的统计信息,以便优化器为SQL语句选择最佳的执行计划.postgres中的autovacuum负责执行真空和分析表格.

postgres中存在另一个名为`Stats Collector`的后台进程,用于跟踪使用情况和活动信息.`autovacuum launcher`进程根据此进程收集的信息来确定需要进行VACUUM的列表发送给Postmaster.只有当autovacuum启用时,PostgreSQL才能识别哪张表需要VACUUM或者ANALYZE,这样可以确保postgres自我修复并阻止数据库产生更多的膨胀/碎片.

在PostgreSQL中启用autovacuum所需的参数是： 

```
autovacuum = on  # ( ON by default )
track_counts = on # ( ON by default )
```

`track_counts`由`Stats Collector`使用.如果没有这个,`autovacuum`无法访问候选表.

## 3. 记录autovacuum

最后,您可能希望记录`autovacuum`在哪个表上花费了更多的时间.在这种情况下,将参数`log_autovacuum_min_duration`设置一个阈值（默认单位为毫秒）,`autovacuum`运行时间超过此值都会记录到PostgreSQL的日志文件中.这可能有助于调整表级`autovacuum`设置.

```
# Setting this parameter to 0 logs every autovacuum to the log file.
log_autovacuum_min_duration = '250ms' # Or 1s, 1min, 1h, 1d
```

 下面是`autovacuum`和`analyze `的示例日志 

```
< 2018-08-06 07:22:35.040 EDT > LOG: automatic vacuum of table "vactest.scott.employee": index scans: 0
pages: 0 removed, 1190 remain, 0 skipped due to pins, 0 skipped frozen
tuples: 110008 removed, 110008 remain, 0 are dead but not yet removable
buffer usage: 2402 hits, 2 misses, 0 dirtied
avg read rate: 0.057 MB/s, avg write rate: 0.000 MB/s
system usage: CPU 0.00s/0.02u sec elapsed 0.27 sec
< 2018-08-06 07:22:35.199 EDT > LOG: automatic analyze of table "vactest.scott.employee" system usage: CPU 0.00s/0.02u sec elapsed 0.15 sec
```

## 4. PostgreSQL什么时候在表上运行autovacuum ?

从前面讨论得知,`postgres`中的`autovacuum`指的是自动VACUUM和ANALYZE,而不仅仅是VACUUM.根据以下数学公式，可以得知`autovacuum`或`ANALYZE`何时在表上运行. 

`autovacuum` 触发计算公式:

```
Autovacuum VACUUM thresold for a table = autovacuum_vacuum_scale_factor * number of tuples + autovacuum_vacuum_threshold
```

通过上面的公式可以知道当`UPDATE`和`DELETE`操作导致表中`dead tuple`的数量超过了阈值,此表将成为`autovacuum` 的候选者.

```
Autovacuum ANALYZE threshold for a table = autovacuum_analyze_scale_factor * number of tuples + autovacuum_analyze_threshold
```

上面公式表明,自上次`ANALYZE`以来插入,更新和删除的元组数量超过此阈值,都有资格进行`autovacuum analyze`

让我们详细了解这些参数.

* `autovacuum_vacuum_scale_factor`或`autovacuum_analyze_scale_factor`:添加到上面公式中的表记录的百分数,例如值为0.2等于表记录的20％.
* `autovacuum_vacuum_threshold`或者` autovacuum_analyze_threshold`:触发自动清理最小DML数量 

让我们研究一个表: `percona.employee`,包含1000条记录和以下`autovacuum`参数.

```
autovacuum_vacuum_scale_factor = 0.2
autovacuum_vacuum_threshold = 50
autovacuum_analyze_scale_factor = 0.1
autovacuum_analyze_threshold = 50
```

 参考上述数学公式

```
Table : percona.employee becomes a candidate for autovacuum Vacuum when,
Total number of Obsolete records = (0.2 * 1000) + 50 = 250
```

```
Table : percona.employee becomes a candidate for autovacuum ANALYZE when,
Total number of Inserts/Deletes/Updates = (0.1 * 1000) + 50 = 150
```

## 5. 调整PostgreSQL中的Autovacuum 

 我们需要了解这些全局设置.这些设置适用于实例中的所有数据库.意味着无论表大小如果达到达到阈值,表都有资格进行自动整理或分析 .

考虑一个包含十条记录的表与一个包含一百万条记录的表.尽管有一百万条记录的表可能进行的事务更加频繁,但是`autovacuum`或者`analyze`在仅有十条记录的表上运行的频率更大.

因此PostgreSQL允许绕过全局设置对单个表的`autovacuum`进行设置.

```
ALTER TABLE scott.employee SET (autovacuum_vacuum_scale_factor = 0, autovacuum_vacuum_threshold = 100);
```

  ```
Output Log
----------
avi@percona:~$psql -d percona
psql (10.4)
Type "help" for help.
percona=# ALTER TABLE scott.employee SET (autovacuum_vacuum_scale_factor = 0, autovacuum_vacuum_threshold = 100);
ALTER TABLE
  ```

上述设置,当`scott.employee`超过100个过期记录时才会在表上运行自动整理`vacuum`.

## 6. 我们如何识别哪一张表需要调整autovacuum 设置？ 

为了单独调整单个表的`autovacuum`设置,必须知道一个表上的插入/删除/更新的数量.可以查看`postgres`系统视图:`pg_stat_user_tables`来获取该信息.

```
percona=# SELECT n_tup_ins as "inserts",n_tup_upd as "updates",n_tup_del as "deletes", n_live_tup as "live_tuples", n_dead_tup as "dead_tuples"
FROM pg_stat_user_tables
WHERE schemaname = 'scott' and relname = 'employee';
 inserts | updates | deletes | live_tuples | dead_tuples
---------+---------+---------+-------------+-------------
      30 |      40 |       9 |          21 |          39
(1 row)
```

 如上面查询所示,每隔一定时间拍摄此查询结果的快照可以帮助您了解每个表上DML的频率.反过来,这也可以帮助您调整各个表的`autovacuum`设置. 

## 7. 一次可以运行多少个autovacuum进程？ 

在一个可能包含多个数据库的实例/集群中,一次运行的`autovacuum`进程数不能超过`autovacuum_max_workers`参数设置.后台进程` Autovacuum launcher`为需要进行`vacuum`或者`ANALYZE`的表启动autovacuum工作进程. 如果有四个数据库,其中`autovacuum_max_workers`设置为3,则第四个数据库必须等待,直到其中一个现有工作进程获得空闲.

在启动下一次autovacuum之前,它需要等待`autovacuum_naptime`设置的时间,大多数版本中默认值为1分钟.如果您有三个数据库,则下一个autovacuum需要等待60/3秒.因此,启动下一个autovacuum进程之前的等待时间始终是（autovacuum_naptime / N）,其中N是实例中数据库的总数.

**增加autovacuum_max_workers是否会增加并行运行的autovacuum进程数? **

不会.接下来会更好地解释这一点.

## 8. VACUUM IO密集吗 ?

Autovacuum可视为清理进程.如前所述,每个表有1个工作进程. Autovacuum 进程从磁盘读取表的一个页面8KB(default_block_size),并修改/写入数据页中包含的dead tuple.这涉及读写IO.因此,这可能是IO密集型操作,当高峰期时在一个包含许多dead tuple的大表上运行autovacuum时.为避免此问题,我们可以设置一些参数来最大限度地减少vacuum对IO的影响. 

以下是用于调整autovacuum IO相关的参数.

* **autovacuum_vacuum_cost_limit**:  用于自动`VACUUM`操作中的总成本限制值 (包含所有autovacuum job)
* **autovacuum_vacuum_cost_delay**: 当自动清理达到`autovacuum_vacuum_cost_limit`成本时,`autovacuum`将休眠这么多毫秒.
* **vacuum_cost_page_hit**: 清理一个在共享缓冲区中且不需要从磁盘读取页面的成本. 
* **vacuum_cost_page_miss** : 清理不在共享缓冲区中页面的成本 
* **vacuum_cost_page_dirty**: 扫描后的页面变脏需要写出到磁盘的成本.

```
Default Values for the parameters discussed above.
------------------------------------------------------
autovacuum_vacuum_cost_limit = -1 (So, it defaults to vacuum_cost_limit) = 200
autovacuum_vacuum_cost_delay = 20ms
vacuum_cost_page_hit = 1
vacuum_cost_page_miss = 10
vacuum_cost_page_dirty = 20
```

考虑在`percona.employee`表上运行自动VACUUM.

让我们想象一下1秒内会发生什么(1秒= 1000毫秒)

在读延迟为0毫秒的最佳情况下,`autovacuum  `可以唤醒并进入睡眠50次(1000毫秒/ 20毫秒),因为唤醒延迟需要20毫秒.

```
1 second = 1000 milliseconds = 50 * autovacuum_vacuum_cost_delay
```

 由于读取shared_buffers中每个页面的成本为1,因此每次唤醒都可以读取200页,并且在50次唤醒中可以读取50 * 200页.

 如果所有包含dead tuple的页面都在共享缓冲区中找到,并且`autovacuum_vacuum_cost_delay`为20ms,那么每次唤醒后它可以读取:((200 / vacuum_cost_page_hit) * 8)KB 需要等待`autovacuum_vacuum_cost_delay`时间间隔. 

 因此,在block_size视为8192字节的情况下`autovacuum`最多可以读取: 50 * 200 * 8 KB = 78.13 MB /秒(如果所有的块都在shared_buffers中).

如果块不在shared_buffers中并且需要从磁盘中获取,那么`autovacuum`最多可以读取:50 \* ( 200 / vacuum_cost_page_miss）* 8 ) KB = 7.81 MB /秒.

我们上面看到的所有信息都是针对读IO的.

现在,为了从页面/块中删除dead_tuple,写操作的成本为:`vacuum_cost_page_dirty`,默认设置为20.

`autovacuum`最多可以写/脏: 50 \*(( 200 / vacuum_cost_page_dirty) * 8)KB = 3.9 MB /秒.

通常,此成本平分给数据库实例中所有运行`autovacuum_max_workers` 进程.因此,增加`autovacuum_max_workers`可能会延迟当前运行的`autovacuum worker` 进程.增加`autovacuum_vacuum_cost_limit`可能会导致IO瓶颈.需要注意的一点是,可以通过对表单独设置参数来覆盖全局设置.

```
postgres=# alter table percona.employee set (autovacuum_vacuum_cost_limit = 500);
ALTER TABLE
postgres=# alter table percona.employee set (autovacuum_vacuum_cost_delay = 10);
ALTER TABLE
postgres=#
postgres=# \d+ percona.employee
Table "percona.employee"
Column | Type | Collation | Nullable | Default | Storage | Stats target | Description
--------+---------+-----------+----------+---------+---------+--------------+-------------
id | integer | | | | plain | |
Options: autovacuum_vacuum_threshold=10000, autovacuum_vacuum_cost_limit=500, autovacuum_vacuum_cost_delay=10
```

  因此,在繁忙的OLTP型数据库中,始终有策略在低峰窗口期对经常进行DML操作的表实施手动VACUUM.你应该尽可能的在设置`autovacuum`相关参数后并行的手动运行`VACUUM`.因此,建议定期的手动`VACUUM` 和精细调整的`autovacuum`同时存在. 
