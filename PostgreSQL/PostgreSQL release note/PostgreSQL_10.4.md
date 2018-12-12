E.1.2. Changes
1.Remove public execute privilege from contrib/adminpack's pg_logfile_rotate() function (Stephen Frost)
移除了pg_logfile_rotate()函数

何用户可以运行pg_logfile_rotate()函数,然后调用pg_rotate_logfile()切换日志文件。

这个函数应该只提供给超级用户,这是一个很小的安全问题。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7b347409fa2776fbaa4ec9c57365f48a2bbdb80c

2.Fix incorrect volatility markings on a few built-in functions (Thomas Munro, Tom Lane)
在几个内置函数中修正“不正确的函数非稳态”的问题，以确保正确的查询优化

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=11002f8afa551f4673aa6a7b62c1872c233e6052

3.Fix incorrect parallel-safety markings on a few built-in functions (Thomas Munro, Tom Lane)
在几个内置函数中修正“不正确的函数并行安全标记”的问题，以确保正确的查询优化

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=11002f8afa551f4673aa6a7b62c1872c233e6052

4.Avoid re-using TOAST value OIDs that match dead-but-not-yet-vacuumed TOAST entries (Pavan Deolasee)
修正当一条记录值可以标记为dead-but-not-yet-vacuumed（已呆死但还未清除）的 TOAST OID，这样会导致类似“unexpected chunk number 0 (expected 1) for toast value nnnnn"的错误提示；

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0408e1ed599b06d9bca2927a50a4be52c9e74bb9

5.Correctly enforce any CHECK constraints on individual partitions during COPY to a partitioned table (Etsuro Fujita)
在复制到分区表时，正确地执行任何检查约束。
Previously, only constraints declared for the partitioned table as a whole were checked.
以前，只检查为分区表声明的所有约束。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=cfbecf8100ecb83c07c2017f843b0642580416bf

6.Accept TRUE and FALSE as partition bound values (Amit Langote)
接受TRUE和FALSE作为分区绑定值。几处有关分区的修正，包括潜在的宕机以及允许布尔值TRUE 和 FALSE 作为分区边界；
Previously, only string-literal values were accepted for a boolean partitioning column. But then pg_dump would print such values as TRUE or FALSE, leading to dump/reload failures.
以前，只有string-literal值被接受为一个布尔分区列。但是，pg_dump会将这些值打印为TRUE或FALSE，从而导致转储/重新加载失败。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4df58f7ed7f9ddc5a3196fcbad35690d1b3218de

7.Fix memory management for partition key comparison functions (Álvaro Herrera, Amit Langote)
修复分区键比较函数的内存管理。
This error could lead to crashes when using user-defined operator classes for partition keys.
在使用用户定义的分区键的操作符类时，这个错误可能导致崩溃。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a4d56f583e7cff052c2699e62d867ae1c8fda4f3

8.Fix possible crash when a query inserts tuples in several partitions of a partitioned table, and those partitions don't have identical row types (Etsuro Fujita, Amit Langote)
修复一个查询对多个没有相同行类型的分区子表插入元组时可能崩溃的问题

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6666ee49f49c4a6b008591aea457becffa0df041

9.Change ANALYZE's algorithm for updating pg_class.reltuples (David Gould)
为更新 pg_class.reltuples 修改 ANALYZE 的算法

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d04900de7d0cb5b6ecb6d5bf9fdb6f3105824f81

10.Include extended-statistics objects in the set of table properties duplicated by CREATE TABLE ... LIKE ... INCLUDING ALL (David Rowley)
建表时可以在表属性的集合中增加扩展统计对象。

Also add an INCLUDING STATISTICS option, to allow finer-grained control over whether this happens.

还添加一个包含统计选项，可以更细粒度的控制

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5564c11815486bdfe87eb46ebc7c070293fa6956

11.Fix CREATE TABLE ... LIKE with bigint identity columns (Peter Eisentraut)
修正"CREATE TABLE ... LIKE"在32位平台上使用bigint identity 列的问题
在长为32位(包括64位窗口和大多数32位机器)的平台上，复制的序列参数将被截断为32位。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=377b5ac4845c5ffbf992ee95c32d7d16d38b9081

12.Avoid deadlocks in concurrent CREATE INDEX CONCURRENTLY commands that are run under SERIALIZABLE or REPEATABLE READ transaction isolation (Tom Lane)
在使用SERIALIZABLE或是REPEATABLE READ的事务模式下并发执行CREATE INDEX CONCURRENTLY指令时的更新，以避免死锁的发生；

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1dec82068b3b59b621e6b04040c150241f5060f3

13.Fix possible slow execution of REFRESH MATERIALIZED VIEW CONCURRENTLY (Thomas Munro)
修正可能的REFRESH MATERIALIZED VIEW CONCURRENTLY （并发刷新物化视图）的低效执行

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6fbd5cce22ebd2203d99cd7dcd179d0e1138599e

14.Fix UPDATE/DELETE ... WHERE CURRENT OF to not fail when the referenced cursor uses an index-only-scan plan (Yugo Nagata, Tom Lane)
修复了UPDATE/DELETE ... WHERE CURRENT OF操作当被引用的游标使用index-only-scan扫描计划失败的问题

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8f5ac440430ab1d4b0309a76df278caa87018beb

15.Fix incorrect planning of join clauses pushed into parameterized paths (Andrew Gierth, Tom Lane)
修正了不正确的连接子句计划，将其推入参数化路径
这个错误可能导致将一个条件误分类为一个“连接过滤器”，当它应该是一个普通的“过滤器”条件时，导致连接输出不正确

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e5d83995e9f88426b325a7ea8ce0770926dc64de

16.Fix possibly incorrect generation of an index-only-scan plan when the same table column appears in multiple index columns, and only some of those index columns use operator classes that can return the column value (Kyotaro Horiguchi)
修正了index-only-scan计划，当一个相同的表列出现在多个索引列中，只有一些索引列使用可以返回列值的操作符类

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b5febc1d125cac37c626cb7c96936db6839ec733

17.Fix misoptimization of CHECK constraints having provably-NULL subclauses of top-level AND/OR conditions (Tom Lane, Dean Rasheed)
修正了在顶级和/或条件下有provably-NULL子句的检查约束的错误优化。

例如，这可以允许约束排除来排除不应该被排除在查询之外的子表。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4a4e2442a7f7c1434e86dd290cdb3704cfebb24c

18.Prevent planner crash when a query has multiple GROUPING SETS, none of which can be implemented by sorting (Andrew Gierth)
防止当在查询有多个分组集，其中没有一个可以通过排序实现时的计划崩溃。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f5780935266bd72951c770396f9267366414d1b9

19.Fix executor crash due to double free in some GROUPING SET usages (Peter Geoghegan)
几处使用GROUPING SET的查询可能引起宕机的问题；

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c2d4eb1b1fa252fd8c407e1519308017a18afed1

20.Fix misexecution of self-joins on transition tables (Thomas Munro)
修正了在转换表上的自连接错误

21.Avoid crash if a table rewrite event trigger is added concurrently with a command that could call such a trigger (Álvaro Herrera, Andrew Gierth, Tom Lane)
如果一个表重写事件触发器同时添加一个可以调用该触发器的命令，避免崩溃

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b1b71f16581fb5385fa9f9a663ffee271cdfaba5

22.Avoid failure if a query-cancel or session-termination interrupt occurs while committing a prepared transaction (Stas Kelvich)
在提交一个预处理的事务时，避免当一个”查询取消“或是”会话强制终止“的中断导致的问题；

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8f9be261f43772ccee2eae94d971bac6557cbe6a

23.Fix query-lifespan memory leakage in repeatedly executed hash joins (Tom Lane)
修正一个查询在重复执行hash join时的内存泄漏

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=467963c3e9c5ba9a953959f8aebcdd7206188a18

24.Fix possible leak or double free of visibility map buffer pins (Amit Kapila)
详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0b1d1a038babff4aadf0862c28e7b667f1b12a30

http://www.postgresql-archive.org/heap-lock-updated-tuple-rec-can-leak-a-buffer-refcount-td6005538.html

25.Avoid spuriously marking pages as all-visible (Dan Wood, Pavan Deolasee, Álvaro Herrera)
避免使用伪造的标记页面

如果一些元组被锁(但不是删除)。虽然查询仍然可以正常工作,但vacuum通常会忽略这些页面,长期影响这些元组。在最近的版本中这将最终导致错误如“found multixact nnnnn from before relminmxid nnnnn”。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d2599ecfcc74fea9fad1720a70210a740c716730

26.Fix overly strict sanity check in heap_prepare_freeze_tuple (Álvaro Herrera)
修正过于严格的 heap_prepare_freeze_tuple 完整性检查
使用pg_upgrade'd从9.2或更早的版本进行更新，这可能导致错误“cannot freeze committed xmax”

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=477ad05e165c15dc9241376f0fce9664063cff46

27.Prevent dangling-pointer dereference when a C-coded before-update row trigger returns the “old” tuple (Rushabh Lathia)
防止悬空指针废弃时用before-update行触发器返回“旧”的元组

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=25b692568f429436f89ff203c1413e9670d0ad67

28.Reduce locking during autovacuum worker scheduling (Jeff Janes)
在autovacuum自动清理进程的计划中减少锁定，以防止潜在的进程并发操作的失效；
autovacuum在有许多表的数据库中造成了潜在的进程并发性的巨大损失。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=38f7831d703be98aaece8af6625faeab5123a02c

29.Ensure client hostname is copied while copying pg_stat_activity data to local memory (Edmund Horner)
之前，假定本地快照包含一个指向共享内存的指针，如果任何现有会话断开连接，则允许客户机主机名列发生意外更改。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=811969b218ac2e8030dfbbb05873344967461618

30.Handle pg_stat_activity information for auxiliary processes correctly (Edmund Horner)
正确处理辅助过程的pg统计活动信息
应用名、客户端名和查询字段可能会显示这些进程的错误数据。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a820b4c32946c499a2d19846123840a0dad071b5

31.Fix incorrect processing of multiple compound affixes in ispell dictionaries (Arthur Zakirov)
修正了ispell字典中多个复合词缀的错误处理。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8bf358c18ec930ddfb998873369e2fc38608d3e1

32.Fix collation-aware searches (that is, indexscans using inequality operators) in SP-GiST indexes on text columns (Tom Lane)
在文本列上的spe - gist索引中，修复与排序相关的搜索(即使用不等操作符的索引扫描)。
这样的搜索将在大多数非c语言环境中返回错误的行集。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b15e8f71dbf00eb18d9076302f39aa981355eb07

33.Prevent query-lifespan memory leakage with SP-GiST operator classes that use traversal values (Anton Dignös)
详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=467963c3e9c5ba9a953959f8aebcdd7206188a18

34.Count the number of index tuples correctly during initial build of an SP-GiST index (Tomas Vondra)
在spc - gist索引的初始构建过程中正确计算索引元组的数量。
以前，报告的tuple计数与底层表相同，如果索引是部分索引的话技术将是错误的。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=649f1792508fb040a9b70c68dfedd6b93897e087

35.Count the number of index tuples correctly during vacuuming of a GiST index (Andrey Borodin)
在对gist索引进行清理过程中正确计算索引元组数

之前，它报告了堆元组的估计数，这可能是不准确的，如果是部分索引，则肯定是错误的。

详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=81b9b5ce490a645bde8df203ec4a3b2903d88f31

36.Fix a corner case where a streaming standby gets stuck at a WAL continuation record (Kyotaro Horiguchi)
详细参考
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=572d6ee6d41b43b8871f42c7dbbef795523b2dbf

37.In logical decoding, avoid possible double processing of WAL data when a walsender restarts (Craig Ringer)
在逻辑解码中，当walsender重新启动时，避免对WAL数据进行双重处理。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=325f2ec5557fd1c9156c910102522e04cb42d99c

38.Fix logical replication to not assume that type OIDs match between the local and remote servers (Masahiko Sawada)
修复逻辑复制，以避免在本地服务器和远程服务器之间进行类型匹配。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=24c0a6c649768f428929e76dd7f5012ec9b93ce1

39.Allow scalarltsel and scalargtsel to be used on non-core datatypes (Tomas Vondra)
允许将scalarltsel和scalargtsel用于非核心数据类型

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=58d9acc18d38899ebc30812b4984778c7069f42c

40.Reduce libpq's memory consumption when a server error is reported after a large amount of query output has been collected (Tom Lane)
减少libpq的内存消耗，在收集了大量查询输出后，报告服务器错误。
在处理错误消息之前，不丢弃弃之前的输出。在一些平台上，特别是Linux，这与应用程序的后续的内存占用有所不同。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d25c2ee9c038969eca8080177738dddf97a2cade

41.Fix double-free crashes in ecpg (Patrick Krecker, Jeevan Ladhe)
修复在ecpg中double-free的崩溃

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=db2fc801f66a70969cbdd5673ed9d02025c70695

42.Fix ecpg to handle long long int variables correctly in MSVC builds (Michael Meskes, Andrew Gierth)
修复在MSVC构建中正确处理长时间的int变量

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=51057feaa6bd24b51e6a4715c2090491ef037534

43.Fix mis-quoting of values for list-valued GUC variables in dumps (Michael Paquier, Tom Lane)
修正在导出时，几处对使用列表值类型的GUC变量的不合适的引用，包括local_preload_libraries, session_preload_libraries, shared_preload_libraries, temp_tabl espaces；
在pg_dump输出中没有正确引用local_preload_libraries、session_preload_libraries、shared_preload_libraries和temp_tablespaces变量。如果这些变量的设置在CREATE FUNCTION ... SET 或 ALTER DATABASE/ROLE ... SET clauses中，这将导致问题。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=742869946f4ff121778c2e5923ab51a451b16497

44.Fix pg_recvlogical to not fail against pre-v10 PostgreSQL servers (Michael Paquier)
修复pg_recvlogical，以防止pre-v10 PostgreSQL服务器上失败。
先前的修复导致pg_recvlogical发出命令，没有考虑服务器版本，它只应该发布到v10和之后的服务器版本。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8d2814f274def85f39fbe997d454b01628cb5667

45.Ensure that pg_rewind deletes files on the target server if they are deleted from the source server during the run (Takayuki Tsunakawa)
确保pg_rewind在运行期间从源服务器上删除目标服务器上的文件。
如果不这样做，可能会导致目标数据不一致，特别是如果这个文件是一个WAL segment。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2f3e2340cd1b67e91cefdf45e4c915297d1034e2

46.Fix pg_rewind to handle tables in non-default tablespaces correctly (Takayuki Tsunakawa)
修复pg_rewind以正确处理非默认表空间中的表。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2f3e2340cd1b67e91cefdf45e4c915297d1034e2

47.Fix overflow handling in PL/pgSQL integer FOR loops (Tom Lane)
在PL/pgSQL整数中为循环设置溢出处理。
之前的代码没有检测到一些非gcc编译器上的循环变量溢出，这将导致了一个无限循环。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2dbee9f19f6c6ac6c013f668611492486e623807

48.Adjust PL/Python regression tests to pass under Python 3.7 (Peter Eisentraut)
调整PL/Python回归测试，以通过Python 3.7。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=fa03769e4c4bf0911da71fba2501006b05ea195a

49.Support testing PL/Python and related modules when building with Python 3 and MSVC (Andrew Dunstan)
在建立Python 3 和 MSVC时支持测试 PL/Python 及相关模块

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=966268c7621c4bca534961440b497a3270395fc2

50.Fix errors in initial build of contrib/bloom indexes (Tomas Vondra, Tom Lane)
修复在初始化建立 contrib/bloom 索引的错误
修复表的最后一个元组可能从索引中遗漏的问题。正确地计算索引元组的数量，如果它是一个部分索引

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c35b47286960d2c7885dce162ddfe26939d0d373

51.Rename internal b64_encode and b64_decode functions to avoid conflict with Solaris 11.4 built-in functions (Rainer Orth)
重命名内部的 b64_encode 和 b64_decode 函数，以避免与Solaris 11.4的内置函数冲突。

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=43e9490866386ba57c5457c6dbeedb04a51c2086

52.Sync our copy of the timezone library with IANA tzcode release 2018e (Tom Lane)
与IANA tzcode release 2018e同步我们的时区库。

这修复了zic时区数据编译器来处理负的 daylight-savings 偏移量。虽然PostgreSQL不会立即发送这样的时区数据，但是zic可能会使用从IANA直接获得的时区数据，所以现在更新zic似乎很精确。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b45f6613e0a475f908d93dbaa8612ccb9395f666

53.Update time zone data files to tzdata release 2018d for DST law changes in Palestine and Antarctica (Casey Station), plus historical corrections for Portugal and its colonies, as well as Enderbury, Jamaica, Turks & Caicos Islands, and Uruguay.
本次更新也包含2018d版本的时区数据，包括对Palestine 和Antarctica时区的更新，加上对Portugal及其殖民属地历史数据的更新，也包括Enderbury, Jamaica, Turks & Caicos Islands 和Uruguay。

详细参考

https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=df629586e89751498d741f107b418d68bccc616e

