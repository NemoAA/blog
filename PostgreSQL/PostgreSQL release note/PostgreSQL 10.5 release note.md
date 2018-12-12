## E.1.2. Changes

### 1.Fix failure to reset libpq's state fully between connection attempts (Tom Lane)

修复连接尝试之间完全重置libpq状态的失败

An unprivileged user of dblink or postgres_fdw could bypass the checks intended to prevent use of server-side credentials, such as a ~/.pgpass file owned by the operating-system user running the server. Servers allowing peer authentication on local connections are particularly vulnerable. Other attacks such as SQL injection into a postgres_fdw session are also possible. Attacking postgres_fdw in this way requires the ability to create a foreign server object with selected connection parameters, but any user with access to dblink could exploit the problem. In general, an attacker with the ability to select the connection parameters for a libpq-using application could cause mischief, though other plausible attack scenarios are harder to think of. Our thanks to Andrew Krasichkov for reporting this issue. (CVE-2018-10915)

dblink或postgres_fdw的非特权用户可以绕过旨在防止使用服务器端凭证(如~/)的检查。运行服务器的操作系统用户拥有的pgpass文件。允许本地连接进行对等认证的服务器尤其容易受到攻击。其他攻击，例如对postgres_fdw会话的SQL注入，也可能发生。以这种方式攻击postgres_fdw需要能够创建具有选定连接参数的外部服务器对象，但任何访问dblink的用户都可能利用这个问题。一般来说，能够为使用libpq的应用程序选择连接参数的攻击者可能会造成损害，尽管其他可信的攻击场景很难想象。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d1c6a14bacfa5fe7690e2c71b1626dbc87a57355>

### 2.Fix INSERT ... ON CONFLICT UPDATE through a view that isn't just SELECT * FROM ... (Dean Rasheed, Amit Langote)

解决INSERT ... ON CONFLICT UPDATE通过一个不只是SELECT * FROM...视图的问题

Erroneous expansion of an updatable view could lead to crashes or “attribute ... has the wrong type” errors, if the view's SELECT list doesn't match one-to-one with the underlying table's columns. Furthermore, this bug could be leveraged to allow updates of columns that an attacking user lacks UPDATE privilege for, if that user has INSERT and UPDATE privileges for some other column(s) of the table. Any user could also use it for disclosure of server memory. (CVE-2018-10925)

可更新视图的错误扩展可能导致崩溃或“类型错误”如果视图的选择列表与底层表的列不匹配。此外，如果攻击用户具有表中其他列的插入和更新特权，则可以利用此错误更新攻击用户缺乏更新特权的列。任何用户都可以使用它来公开服务器内存。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b8a1247a34e234be6becf7f70b9f1e8e9369db64>

### 3.Ensure that updates to the relfrozenxid and relminmxid values for “nailed” system catalogs are processed in a timely fashion (Andres Freund)

确保及时处理对“固定”系统目录的relfrozenxid和relminmxid值的更新

Overoptimistic caching rules could prevent these updates from being seen by other sessions, leading to spurious errors and/or data corruption. The problem was significantly worse for shared catalogs, such as pg_authid, because the stale cache data could persist into new sessions as well as existing ones.

过于乐观的缓存规则可能会阻止这些更新被其他会话看到，从而导致错误和/或数据损坏。对于共享目录(如pg_authid)来说，问题要严重得多，因为陈旧的缓存数据可以持久化到新会话和现有会话中。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a54e1f1587793b5bf926630ec9ce142e4578d7a0>

### 4.Fix case where a freshly-promoted standby crashes before having completed its first post-recovery checkpoint (Michael Paquier, Kyotaro Horiguchi, Pavan Deolasee, Álvaro Herrera)

修复在完成第一个恢复后检查点之前，新提升的备用服务器崩溃的情况

This led to a situation where the server did not think it had reached a consistent database state during subsequent WAL replay, preventing restart.

这导致服务器认为在随后的WAL重做期间没有达到一致的数据库状态，从而导致无法重新启动。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3c64dcb1e35dccbfce531182fa9b9f48bec414ad>

### 5.Avoid emitting a bogus WAL record when recycling an all-zero btree page (Amit Kapila)

当回收一个全零btree页面时，避免发出虚假的WAL记录

This mistake has been seen to cause assertion failures, and potentially it could result in unnecessary query cancellations on hot standby servers.

这个错误会导致定义失败，并且可能会导致热备用服务器上不必要的查询取消

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0905fe8911ea06df17a3ba3f086e98ca5c7b560c>

### 6.During WAL replay, guard against corrupted record lengths exceeding 1GB (Michael Paquier)

在回放过程中，防止记录长度超过1GB

Treat such a case as corrupt data. Previously, the code would try to allocate space and get a hard error, making recovery impossible.

将这种情况视为损坏的数据。以前，代码会尝试分配空间并得到一个硬错误，使恢复不可能。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=70b4f82a4b5cab5fc12ff876235835053e407155>

### 7.When ending recovery, delay writing the timeline history file as long as possible (Heikki Linnakangas)

当结束恢复时，尽可能延迟写入时间轴历史文件

This avoids some situations where a failure during recovery cleanup (such as a problem with a two-phase state file) led to inconsistent timeline state on-disk.

这可以避免在恢复清理期间出现故障(例如两阶段状态文件出现问题)导致磁盘上的时间轴状态不一致的情况

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=cbc55da556bbcb649e059804009c38100ee98884>

### 8.Improve performance of WAL replay for transactions that drop many relations (Fujii Masao)

对于那些丢失了许多对象的事务，提高WAL恢复的性能

This change reduces the number of times that shared buffers are scanned, so that it is of most benefit when that setting is large.

这一更改减少了扫描共享缓冲区的次数，因此当设置较大时，它将获得最大的好处

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b41669118c00e25376a6c9ac991e0d074990484a>

### 9.Improve performance of lock releasing in standby server WAL replay (Thomas Munro)

提高备用服务器的锁释放性能

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a40cff8956e842f737739d93a7b160f0b4a03d13>

### 10.Make logical WAL senders report streaming state correctly (Simon Riggs, Sawada Masahiko)

使逻辑WAL发送者报告正确的流状态

The code previously mis-detected whether or not it had caught up with the upstream server.

之前的代码错误检测到它是否赶上了上游服务器。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9a7b7adc130a197e5c993a99e6aaa981f9341a35>

### 11.Ensure that a snapshot is provided when executing data type input functions in logical replication subscribers (Minh-Quan Tran, Álvaro Herrera)

确保在逻辑复制订阅端中执行数据类型输入函数时提供快照

This omission led to failures in some cases, such as domains with constraints using SQL-language functions.

这种遗漏在某些情况下会导致失败，例如使用sql语言函数具有约束的域。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4f10e7ea7b2231f453bb18b6e710ac333eaf121b>

### 12.Fix bugs in snapshot handling during logical decoding, allowing wrong decoding results in rare cases (Arseny Sher, Álvaro Herrera)

修复了在逻辑解码期间快照处理中的错误，允许在罕见情况下出现错误的解码结果

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f49a80c481f74fa81407dce8e51dea6956cb64f8>

### 13.Add subtransaction handling in logical-replication table synchronization workers (Amit Khandekar, Robert Haas)

在逻辑复制表同步工作者中添加子事务处理

Previously, table synchronization could misbehave if any subtransactions were aborted after modifying a table being synchronized.

在此之前，如果在同步表中修改了一个表后，任何子事务被中止，那么表同步就会发生错误。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=32df1c9afa5a11e37b154fe50df7a4f016f289e4>

### 14.Ensure a table's cached index list is correctly rebuilt after an index creation fails partway through (Peter Geoghegan)

确保在创建索引失败之后，正确地重新构建表的缓存索引列表

Previously, the failed index's OID could remain in the list, causing problems later in the same session.

在此之前，失败的索引的OID可能会留在列表中，导致相同会话的稍后部分出现问题

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b3f919da07540d7c968e8495482336304badcef7>

### 15.Fix mishandling of empty uncompressed posting list pages in GIN indexes (Sivasubramanian Ramasubramanian, Alexander Korotkov)

修复在GIN索引中处理空未压缩的发布列表页的错误

This could result in an assertion failure after pg_upgrade of a pre-9.4 GIN index (9.4 and later will not create such pages).

这可能导致在前9.4 GIN索引(9.4及更高版本将不会创建此类页面)的pg_upgrade之后出现定义失败。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=309765fa1e317597bfd341fa99dfa97ea5722890>

### 16.Pad arrays of unnamed POSIX semaphores to reduce cache line sharing (Thomas Munro)

用未命名的POSIX信号量填充阵列来减少高速缓存线路共享

This reduces contention on many-CPU systems, fixing a performance regression (compared to previous releases) on Linux and FreeBSD.

这减少了在多cpu系统上的争用，提升了Linux和FreeBSD上的性能(与以前的版本相比)

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2d3067595299d2ac1f29bbc26a83a99d59b33d4e>

### 17.Ensure that a process doing a parallel index scan will respond to signals (Amit Kapila)

确保进行并行索引扫描的进程将对信号作出响应

Previously, parallel workers could get stuck waiting for a lock on an index page, and not notice requests to abort the query.

以前，并行工作人员可能会在索引页上等待锁，而不会注意到终止查询的请求。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8ce29bb4f0df0806cf1995594b6390e9a9997665>

### 18.Ensure that VACUUM will respond to signals within btree page deletion loops (Andres Freund)

确保VACUUM将响应btree页面删除循环中的信号

Corrupted btree indexes could result in an infinite loop here, and that previously wasn't interruptible without forcing a crash.

损坏的btree索引可能会导致这里出现无限循环，而这在以前是不可中断的，不会导致崩溃。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3a01f68e35a3584431ac5381c6ed75b1b39aaf2a>

### 19.Fix hash-join costing mistake introduced with inner_unique optimization (David Rowley)

修正了inner_unique优化引入的散列连接成本错误

This could lead to bad plan choices in situations where that optimization was applicable.

这可能导致在适用优化的情况下的糟糕计划选择。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1007b0a126c608b530fd2914825f1e6d133cb649>

### 20.Fix misoptimization of equivalence classes involving composite-type columns (Tom Lane)

修正了包含复合类型列的等价类的错误优化

This resulted in failure to recognize that an index on a composite column could provide the sort order needed for a mergejoin on that column.

这导致无法识别复合列上的索引

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a11b3bd37f14386310f25e89529bd3de8cd64383>

### 21.Fix planner to avoid “ORDER/GROUP BY expression not found in targetlist” errors in some queries with set-returning functions (Tom Lane)

修复计划,以避免某些带有set-return函数的查询中出现错误“ORDER/GROUP BY expression not found in targetlist”

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=57cd2b6e6dc571cf65983d2aa86065d6d006f152>

### 22.Fix handling of partition keys whose data type uses a polymorphic btree operator class, such as arrays (Amit Langote, Álvaro Herrera)

修复数据类型使用多态btree操作符类(如数组)的分区键的处理

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b6e3a3a492dbf2043e4b149221007716ba9e364e>

### 23.Fix SQL-standard FETCH FIRST syntax to allow parameters ($n), as the standard expects (Andrew Gierth)

修复sql标准FETCH FIRST语法以允许参数($n)，正如标准所期望的那样

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1da162e1f5a783bd0ce26e6a07c0138dc8a47d44>

### 24.Remove undocumented restriction against duplicate partition key columns (Yugo Nagata)

删除对重复分区键列的无文档说明限制

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=24097167558bafbc1ea32f67ea5840e5650ad4e7>

### 25.Disallow temporary tables from being partitions of non-temporary tables (Amit Langote, Michael Paquier)

不允许将临时表作为非临时表的分区

While previously allowed, this case didn't work reliably.

虽然以前允许这样做，但这种情况并不可靠。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1c7c317cd9d1e5647454deed11b55dae764c83bf>

### 26.Fix EXPLAIN's accounting for resource usage, particularly buffer accesses, in parallel workers (Amit Kapila, Robert Haas)

修复EXPLAIN资源的使用，特别是并行工作进程中的缓冲区访问

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=85c9d3475e4f680dbca7c04fe096af018f3b8760>

### 27.Fix SHOW ALL to show all settings to roles that are members of pg_read_all_settings, and also allow such roles to see source filename and line number in the pg_settings view (Laurenz Albe, Álvaro Herrera) Fix SHOW ALL

显示所有角色的设置，这些角色是pg_read_all_settings的成员，并且允许这些角色在pg_settings视图中查看源文件名和行号

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0c8910a0cab7c1e439bf5f5850122c36359e6799>

### 28.Fix failure to schema-qualify some object names in getObjectDescription and getObjectIdentity output (Kyotaro Horiguchi, Tom Lane)

修正了模式错误——在getObjectDescription和getObjectIdentity输出中限定一些对象名

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1a31baf61ed81a13d034bd50db19473ad67acc52>

### 29.Fix CREATE AGGREGATE type checking so that parallelism support functions can be attached to variadic aggregates (Alexey Bashtanov)

修复创建聚合类型检查，以便并行性支持函数可以附加到可变聚合

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=05ca21b878a9e483a4635ba4b23e0f45d5442fc3>

### 30.Widen COPY FROM's current-line-number counter from 32 to 64 bits (David Rowley)

将当前行号计数器的拷贝从32位扩大到64位

This avoids two problems with input exceeding 4G lines: COPY FROM WITH HEADER would drop a line every 4G lines, not only the first line, and error reports could show a wrong line number.

这避免了输入超过4G行时出现的两个问题:从HEADER中复制会在每一行的4G行中留下一行，而不仅仅是第一行，错误报告可能显示错误的行号

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ecac23511e04d96b94705731873fa3d238c41f8d>

### 31.Allow replication slots to be dropped in single-user mode (Álvaro Herrera)

允许在单用户模式下删除复制槽 This use-case was accidentally broken in release 10.0. 这个用例在10.0版中被意外地破坏了

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0ce5cf2ef24f638ff05569d027135fa1c7683a71>

### 32.Fix incorrect results from variance(int4) and related aggregates when run in parallel aggregation mode (David Rowley)

修正在并行聚合模式下运行时不正确的方差(int4)和相关聚合结果

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ec4719cd155d1d58c8aa7c06c7ef24aef6e67622>

### 33.Process TEXT and CDATA nodes correctly in xmltable() column expressions (Markus Winand)

正确处理xmltable()列表达式中的文本和CDATA节点

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b7f0be9a7e7ec1eb7b9780b169366495f24bf975>

### 34.Cope with possible failure of OpenSSL's RAND_bytes() function (Dean Rasheed, Michael Paquier)

处理OpenSSL的RAND_bytes()函数可能出现的故障

Under rare circumstances, this oversight could result in “could not generate random cancel key” failures that could only be resolved by restarting the postmaster.

在很少的情况下，这种疏忽可能会导致“无法生成随机取消键”失败，而这些失败只能通过重新启动postmaster来解决。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8f6ce7fb090a674f18b72e89a2b868fe1343fe8f>

### 35.Fix libpq's handling of some cases where hostaddr is specified (Hari Babu, Tom Lane, Robert Haas)

修复指定hostaddr的一些情况下libpq的处理

PQhost() gave misleading or incorrect results in some cases. Now, it uniformly returns the host name if specified, or the host address if only that is specified, or the default host name (typically /tmp or localhost) if both parameters are omitted.

PQhost()在某些情况下给出了误导或不正确的结果。现在，如果指定了主机名，它将统一返回主机名;如果只指定了主机地址，它将统一返回主机名;如果省略了这两个参数，它将统一返回默认主机名(通常是/tmp或localhost)。

Also, the wrong value might be compared to the server name when verifying an SSL certificate.

此外，在验证SSL证书时，可能会将错误的值与服务器名称进行比较。

Also, the wrong value might be compared to the host name field in ~/.pgpass. Now, that field is compared to the host name if specified, or the host address if only that is specified, or localhost if both parameters are omitted.

另外，可能会将错误的值与~/.pgpass中的主机名字段进行比较。现在，如果指定了该字段，就将其与主机名进行比较;如果只指定了主机地址，则将其与主机地址进行比较;如果省略了这两个参数，则将对localhost进行比较。

Also, an incorrect error message was reported for an unparseable hostaddr value.

另外，对于不可解析的hostaddr值，报告了一条错误消息。

Also, when the host, hostaddr, or port parameters contain comma-separated lists, libpq is now more careful to treat empty elements of a list as selecting the default behavior.

此外，当主机、主机地址或端口参数包含逗号分隔的列表时，libpq现在更小心地将列表中的空元素视为选择默认行为。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1944cdc98273dbb8439ad9b387ca2858531afcf0>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=24986c95520e0761dbb3551196fda2305228557c>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c7a8f786775e073a3fa785ed2842cc24f9eb6ae8>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c1455de2af2eb06ee493f9982f060ac7e571f656>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e3f99e03e2ec65e7ddb1f3056b545f2afa57b2d0>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b90d97e081415768468295cc4d10d7ee21881964>

### 36.Add a string freeing function to ecpg's pgtypes library, so that cross-module memory management problems can be avoided on Windows (Takayuki Tsunakawa)

为ecpg的pgtypes库添加一个字符串释放函数，这样就可以避免在Windows上出现跨模块内存管理问题

On Windows, crashes can ensue if the free call for a given chunk of memory is not made from the same DLL that malloc'ed the memory. The pgtypes library sometimes returns strings that it expects the caller to free, making it impossible to follow this rule. Add a PGTYPESchar_free() function that just wraps free, allowing applications to follow this rule.

在Windows上，如果对给定内存块的免费调用不是由malloc的内存所在的DLL生成的，则会导致崩溃。pgtypes库有时会返回它希望调用者释放的字符串，因此不可能遵循这条规则。添加一个PGTYPESchar_free()函数，它只包装为free，允许应用程序遵循这个规则。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4c8156d87108fa1f245bee13775e76819cd46a90>

### 37.Fix ecpg's support for long long variables on Windows, as well as other platforms that declare strtoll/strtoull nonstandardly or not at all (Dang Minh Huong, Tom Lane)

修复了ecpg对Windows上的长时间变量的支持，以及其他声明strtoll/strtoull不标准或完全不标准的平台

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=dbccdd375b41618ca4ee3d1ea7109ab7f95d0865>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5e79405d82992efce15c27694f10fb4e1ac32657>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=06f66cff9e0b93db81db1595156b2aff8ba1786e>

### 38.Fix misidentification of SQL statement type in PL/pgSQL, when a rule change causes a change in the semantics of a statement intra-session (Tom Lane)

修正了当规则更改导致语句会话内语义的更改时PL/pgSQL中SQL语句类型的错误识别

This error led to assertion failures, or in rare cases, failure to enforce the INTO STRICT option as expected.

这个错误导致了定义失败，或者在很少的情况下，没有按照预期执行INTO STRICT选项

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9a8aa25ccc6c285cd4f02afe4718eafd20dc34c5>

### 39.Fix password prompting in client programs so that echo is properly disabled on Windows when stdin is not the terminal (Matthew Stickney)

修复客户端程序中的密码提示，以便当stdin不是终端时，在Windows上正确禁用echo

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=50485b3e201dda8498e799b769e624db20e86cff>

### 40.Further fix mis-quoting of values for list-valued GUC variables in dumps (Tom Lane)

进一步修复转储中的列表值GUC变量的错误引号

The previous fix for quoting of search_path and other list-valued variables in pg_dump output turned out to misbehave for empty-string list elements, and it risked truncation of long file paths.

之前在pg_dump输出中引用search_path和其他列表值变量的修复结果对于空字符串列表元素来说是错误的，而且可能会截断长文件路径。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f3eb76b399efb88882b2984fccdefcea540b2749>

### 41.Fix pg_dump's failure to dump REPLICA IDENTITY properties for constraint indexes (Tom Lane)

修复pg_dump未能为约束索引转储副本标识属性

Manually created unique indexes were properly marked, but not those created by declaring UNIQUE or PRIMARY KEY constraints.

手动创建的惟一索引被正确标记，但通过声明惟一或主键约束而创建的索引则没有标记

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c0a552921b0f5f22ac982b5ad24f1df4fd8ca1b1>

### 42.Make pg_upgrade check that the old server was shut down cleanly (Bruce Momjian)

让pg_upgrade检查旧服务器是否被彻底关闭

The previous check could be fooled by an immediate-mode shutdown.

之前的检查可能会被立即关闭模式所欺骗。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=244142d32afd02e7408a2ef1f249b00393983822>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b6d6488a3a7077fb2305c360c241a0789d7b657e>

### 43.Fix contrib/hstore_plperl to look through Perl scalar references, and to not crash if it doesn't find a hash reference where it expects one (Tom Lane)

修复了contrib/hstore_plperl查看Perl标量引用的错误，如果在预期的地方没有找到哈希引用，就不会崩溃

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e3b7f7cc50630dac958a48b533cce04e4222892b>

### 44.Fix crash in contrib/ltree's lca() function when the input array is empty (Pierre Ducroquet)

修复了当输入数组为空时，在contrib/ltree的lca()函数中崩溃的问题

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=28a1ae5342fe39b7c4057d3f872cb6057f5f33bf>

### 45.Fix various error-handling code paths in which an incorrect error code might be reported (Michael Paquier, Tom Lane, Magnus Hagander)

修复可能报告错误代码的各种错误处理代码路径

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=81256cd05f0745353c6572362155b57250a0d2a0>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6cb3372411fd6ed8ba0f8d36ae578a2daa517c16>

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=cfb758b6d9c1df58fb1dfd5d3f6e70393fb17869>

### 46.Rearrange makefiles to ensure that programs link to freshly-built libraries (such as [libpq.so](http://libpq.so/)) rather than ones that might exist in the system library directories (Tom Lane)

重新安排makefile，以确保程序链接到新构建的库(如[libpq.so](http://libpq.so/))，而不是系统库目录中可能存在的库

This avoids problems when building on platforms that supply old copies of PostgreSQL libraries.

这可以避免在提供PostgreSQL库旧副本的平台上构建时出现问题。

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=dddfc4cb2edcfa5497f5d50190a7fb046c51da16>

### 47.Update time zone data files to tzdata release 2018e for DST law changes in North Korea, plus historical corrections for Czechoslovakia.

更新时区数据文件到tzdata发布2018e，用于朝鲜的DST法律变更，以及捷克斯洛伐克的历史修正 This update includes a redefinition of “daylight savings” in Ireland, as well as for some past years in Namibia and Czechoslovakia. In those jurisdictions, legally standard time is observed in summer, and daylight savings time in winter, so that the daylight savings offset is one hour behind standard time not one hour ahead. This does not affect either the actual UTC offset or the timezone abbreviations in use; the only known effect is that the is_dst column in the pg_timezone_names view will now be true in winter and false in summer in these cases.

详细参考

<https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=234bb985c574d1ed9e63d382b327ac3d3e329c56>