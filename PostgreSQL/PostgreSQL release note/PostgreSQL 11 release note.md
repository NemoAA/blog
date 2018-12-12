E.1.3. Changes

Below you will find a detailed account of the changes between PostgreSQL 11 and the previous major release.
下面将详细介绍PostgreSQL 11和以前的主要版本之间的修改
E.1.3.1. Server

E.1.3.1.1. Partitioning

●Allow faster partition elimination during query processing (Amit Langote, David Rowley, Dilip Kumar)
允许在查询处理期间更快地消除分区
This speeds access to partitioned tables with many partitions.
这加快了对具有多个分区的分区表的访问。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9fdb675fc5d2de825414e05939727de8b120ae81

●Allow partition elimination during query execution (David Rowley, Beena Emerson)
允许在查询执行期间消除分区
Previously partition elimination could only happen at planning time, meaning many joins and prepared queries could not use partition elimination.
以前分区消除只能在计划时间发生，这意味着许多连接和已准备的查询不能使用分区消除。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=499be013de65242235ebdde06adb08db887f0ea5

●Allow the creation of partitions based on hashing a key (Amul Sul)
允许基于散列键创建分区
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1aba8e651ac3e37e1d2d875842de1e0ed22a651e

●Allow updated rows to automatically move to new partitions based on the new row contents (Amit Khandekar)
允许更新的行根据新的行内容自动移动到新的分区
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2f178441044be430f6b4d626e4dae68a9a6f6cec

●Allow partitioned tables to have a default partition (Jeevan Ladhe, Beena Emerson, Ashutosh Bapat, Rahila Syed, Robert Haas)
允许分区表具有默认分区
The default partition can store rows that don't match any of the other defined partitions, and is searched accordingly.
默认分区可以存储与其他已定义分区不匹配的行，并相应地进行搜索。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6f6b99d1335be8ea1b74581fc489a97b109dd08a

●Allow UNIQUE indexes on partitioned tables if the partition key guarantees uniqueness (Álvaro Herrera, Amit Langote)
如果分区键保证惟一性，则允许分区表上建立唯一索引
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=eb7ed3f3063401496e4aa4bd68fa33f0be31a72f

●Allow indexes on a partitioned table to be automatically created in any child partitions (Álvaro Herrera)
允许在任何子分区中自动创建分区表上的索引
The new command ALTER INDEX ATTACH PARTITION allows indexes to be attached to partitions. This does not behave as a global index since the contents are private to each index. WARN WHEN USING AN EXISTING INDEX?
新的命令ALTER INDEX ATTACH分区允许将索引附加到分区上。这并不表现为全局索引，因为每个索引的内容都是私有的。在使用现有索引时发出警告?
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8b08f7d4820fd7a8ef6152a9dd8c6e3cb01e5f99

●Allow foreign keys on partitioned tables (Álvaro Herrera)
允许在分区表上建立外键
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3de241dba86f3dd000434f70aebba725fb928032

●Allow INSERT, UPDATE, and COPY on partitioned tables to properly route rows to foreign partitions (Etsuro Fujita, Amit Langote)
允许在分区表上插入、更新和复制，以正确地将行路由到外部分区
This is supported by postgres_fdw foreign tables.
这是由postgres_fdw外表支持的
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3d956d9562aa4811b5eaaaf5314d361c61be2ae0

●Allow FOR EACH ROW triggers on partitioned tables (Álvaro Herrera)
允许分区表上创建行触发器
Creation of a trigger on partitioned tables automatically creates triggers on all partition tables, and on newly-created ones. This also allows deferred unique constraints on partitioned tables.
在分区表上创建触发器可以自动地在所有分区表和新创建的表上创建触发器。这也允许对分区表进行延迟惟一约束
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=86f575948c773b0ec5b0f27066e37dd93a7f0a96

●Allow equality joins between partitioned tables with identically partitioned child tables to join the child tables directly (Ashutosh Bapat)
允许具有相同分区子表的已分区表之间的连接相等，以便直接连接子表
This features is disabled by default but can be enabled by changing enable_partitionwise_join.
默认情况下禁用此特性，但是可以通过更改enable_partitionwise_join来启用
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e139f1953f29db245f60a7acb72fccb1e05d2442
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f49842d1ee31b976c681322f76025d7732e860f3

●Perform aggregation on each partition, and then merge the results (Jeevan Chalke, Ashutosh Bapat, Robert Haas)
对每个分区执行聚合，然后合并结果
This features is disabled by default but can be enabled by changing enable_partitionwise_aggregate.
这个特性在默认情况下是禁用的，但是可以通过更改enable_partitionwise_aggregate来启用。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e2f1eb0ee30d144628ab523432320f174a2c8966

●Allow postgres_fdw to push down aggregates to foreign tables that are partitions (Jeevan Chalke)
允许postgres_fdw向下推入分区的外部表。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e9f2703ab7b29f7e9100807cfbd19ddebbaa0b12

E.1.3.1.2. Parallel Queries

●Allow btree indexes to be built in parallel (Peter Geoghegan, Rushabh Lathia, Heikki Linnakangas)
允许并行构建btree索引
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9da0cc35284bdbe8d442d732963303ff0e0a40bc

●Allow hash joins to be performed in parallel using a shared hash table (Thomas Munro)
允许使用共享哈希表并行执行哈希连接
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1804284042e659e7d16904e7bbb0ad546394b6a3

●Allow UNION to run each SELECT in parallel if the individual SELECTs cannot be parallelized (Amit Khandekar, Robert Haas, Amul Sul)
如果单个的选择不能并行化，允许UNION并行运行每个选择
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ab72716778128fb63d54ac256adf7fe6820a1185

●Allow partition scans to more efficiently use parallel workers (Amit Khandekar, Robert Haas, Amul Sul)
允许分区扫描更有效地使用并行工作进程
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ab72716778128fb63d54ac256adf7fe6820a1185

●Allow LIMIT to be passed to parallel workers (Robert Haas, Tom Lane)
允许将限制传递给并行工作进程
This allows workers to reduce returned results and use targeted index scans.
这允许工作进程减少返回的结果并使用有针对性的索引扫描
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3452dc5240da43e833118484e1e9b4894d04431c

●Allow single-evaluation queries, e.g. WHERE clause aggregate queries, and functions in the target list to be parallelized (Amit Kapila, Robert Haas)
允许对单值查询进行并行处理，例如WHERE子句聚合查询和目标列表中的函数
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e89a71fb449af2ef74f47be1175f99956cf21524
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3f90ec8597c3515e0d3190613b31491686027e4b
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=11cf92f6e2e13c0a6e3f98be3e629e6bd90b74d5

●Add server option parallel_leader_participation to control if the leader executes subplans (Thomas Munro)
添加服务器选项parallel_leader_participation来控制领导者是否执行子计划
The default is enabled, meaning the leader will execute subplans.
默认是启用的，这意味着领导将执行子计划。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e5253fdc4f5fe2f38aec47e08c6aee93f934183d

●Allow parallelization of commands CREATE TABLE .. AS, SELECT INTO, and CREATE MATERIALIZED VIEW (Haribabu Kommi)
允许并行命令CREATE TABLE .. AS, SELECT INTO, 和 CREATE MATERIALIZED VIEW
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e9baa5e9fa147e00a2466ab2c40eb99c8a700824

●Improve performance of sequential scans with many parallel workers (David Rowley)
提高与许多并行工作进程的顺序扫描的性能。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3cda10f41bfed7e34b0db7013b66dd40a5f75926

●Add reporting of parallel worker sort activity to EXPLAIN (Robert Haas, Tom Lane)
添加并行worker排序活动的解释报告
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=bf11e7ee2e3607bb67d25aec73aa53b2d7e9961b

E.1.3.1.3. Indexes

●Allow indexes to INCLUDE columns that are not part of the unique constraint but are available for index-only scans (Anastasia Lubennikova, Alexander Korotkov, Teodor Sigaev)
允许索引包含不属于唯一约束的列，但仅用于索引扫描的列
This is also useful for including columns that don't have btree support.
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8224de4f42ccf98e08db07b43d52fed72f962ebb

●Remember the highest btree index page to optimize future monotonically increasing index additions (Pavan Deolasee, Peter Geoghegan)
记住最高的btree索引页，以优化未来单调递增的索引添加
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=074251db6740a9abfbd922d13d39b27c4f338a20

●Allow entire hash index pages to be scanned (Ashutosh Sharma)
允许扫描整个哈希索引页
Previously for each hash index entry, we need to refind the scan position within the page. This cuts down on lock/unlock traffic.
在此之前，对于每个散列索引条目，我们需要重新找到页面中的扫描位置。这减少了锁定/解锁的流量。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7c75ef571579a3ad7a1d3ee909f11dba5e0b9440

●Add predicate locking for hash, GiST and GIN indexes (Shubham Barai)
为哈希、GiST和GIN索引添加谓词锁定
This reduces the likelihood of serialization conflicts. ACCURATE?
这减少了序列化冲突的可能性。准确?
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b508a56f2f3a2d850e75a14661943d6b4dde8274
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=43d1ed60fdd96027f044e152176c0d45cd6bf443
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3ad55863e9392bff73377911ebbf9760027ed405

●Allow heap-only-tuple (HOT) updates for expression indexes when the values of the expressions are unchanged (Konstantin Knizhnik)
当表达式的值不变时，允许对表达式索引进行heap- tuple (HOT)更新
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c203d6cf81b4d7e43edb2b75ec1b741ba48e04e0

E.1.3.1.3.1. SP-Gist

●Add TEXT prefix operator ^@ which is supported by SP-GiST (Ildus Kurbangaliev)
添加SP-GiST支持的文本前缀操作符^@ 
This is similar to using LIKE 'word%' with btree indexes, but is more efficient.
这与使用btree索引的“word%”类似，但更有效。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=710d90da1fd8c1d028215ecaf7402062079e99e9

●Allow polygons to be indexed with SP-GiST (Nikita Glukhov, Alexander Korotkov)
允许用SP-GiST索引多边形
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ff963b393ca93a71d2f398c4c584b322cd351c2c

●Allow SP-GiST indexes to optionally use compression (Teodor Sigaev, Heikki Linnakangas, Alexander Korotkov, Nikita Glukhov)
允许SP-GiST索引可选地使用压缩
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=854823fa334cb826eed50da751801d0693b10173

E.1.3.1.4. Optimizer
优化器
●Improve the selection of the optimizer statistics' most-common-values (Jeff Janes, Dean Rasheed)
改进优化器统计信息最常用值的选择
Previously most-common-values (MCV) were chosen based on their significance compared to all column values. Now, MCV are chosen based on their significance compared to the non-MCV values. This improves the statistics for uniform (fewer) and non-uniform (more) distributions.
之前最常用的值(MCV)是根据它们相对于所有列值的重要性来选择的。现在，选择MCV是基于其相对于非MCV值的重要性。这改进了均匀分布(更少)和非均匀分布(更多)的统计数据。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b5db1d93d2a6e2d3186f8798a5d06e07b7536a1d

●Improve selectivity estimates for >= and <= when the constants are not common values (Tom Lane)
当常量不是公共值时，改进对>=和<=的选择性估计
Previously such cases used the same selectivity as > and <, respectively. This change is particularly useful for BETWEEN with small ranges.
以前这类情况分别使用与>和<相同的选择性。这种变化对于小范围的用户来说特别有用。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7d08ce286cd5854d58152e428c28636a616bdc42

●Optimize var = var to var IS NOT NULL where equivalent (Tom Lane)
在等价的地方，将var = var优化为var不是NULL

This leads to better selectivity estimates.
这将导致更好的选择性估计
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8ec5429e2f422f4d570d4909507db0d4ca83bbac

●Improve row count optimizer estimates for EXISTS and NOT EXISTS queries (Tom Lane)
改进行计数优化器对现有查询和不存在查询的估计
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7ca25b7de6aefa5537e0dbe56541bc41c0464f97

●Add optimizer selectivity costs for HAVING clauses (Tom Lane)
添加具有子句的优化器选择性成本
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7b6c07547190f056b0464098bb5a2247129d7aa2

E.1.3.1.5. General Performance
常规性能
●Add Just-In-Time (JIT) compilation of some parts of query plans to improve execution speed (Andres Freund)
添加即时(JIT)编译查询计划的某些部分，以提高执行速度
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2a0faed9d7028e3830998bd6ca900be651274e27

●Allow bitmap scans to perform index-only scans when possible (Alexander Kuzmenkov)
允许位图扫描在可能的情况下只执行索引扫描
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7c70996ebf0949b142a99c9445061c3c83ce62b3

●Update the free space map during vacuum (Claudio Freire)
在执行vacuum期间更新自由空间地图
This allows free space to be reused more quickly.
这允许更快速地重用自由空间
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c79f6df75dd381dbc387326f8155402992524124

●Allow vacuum to avoid unnecesary index scans (Masahiko Sawada, Alexander Korotkov)
允许执行vacuum时避免不必要的索引扫描
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=857f9c36cda520030381bd8c2af20adf0ce0e1d4

●Improve performance of committing multiple concurrent transactions (Amit Kapila)
提高提交多个并发事务的性能
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=baaf272ac908ea27c09076e34f62c45fa7d1e448

●Reduce memory usage for queries using set-returning functions in their target lists (Andres Freund)
使用目标列表中的set-returning函数减少查询的内存使用
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=84ad4b036d975ad1be0f52251bac3a06463c9811

●Allow postgres_fdw to push UPDATEs and DELETEs using joins to foreign servers (Etsuro Fujita)
允许postgres_fdw使用与外部服务器的连接来推动更新和删除。
Previously only non-join UPDATEs and DELETEs were pushed.
以前只推送非连接的更新和删除
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1bc0100d270e5bcc980a0629b8726a32a497e788

E.1.3.1.6. Monitoring

●Show memory usage in log_statement_stats, log_parser_stats, log_planner_stats, log_executor_stats (Justin Pryzby, Peter Eisentraut)
在log_statement_stats、log_parser_stats、log_planner_stats、log_executor_stats中显示内存使用情况
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c039ba0716383ccaf88c9be1a7f0803a77823de1

●Add pg_stat_activity.backend_type now shows the type of background worker (Peter Eisentraut)
添加pg_stat_activity。backend_type现在显示了后台工作程序的类型
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5373bc2a0867048bb78f93aede54ac1309b5e227

●Add bgw_type to the background worker C structure (Peter Eisentraut)
向后台worker C结构中添加bgw_type
This is displayed to the user in pg_stat_activity.backend_type and ps output.
这将在pg_stat_activity中显示给用户。backend_type和ps输出。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5373bc2a0867048bb78f93aede54ac1309b5e227

●Have log_autovacuum_min_duration log skipped tables that are concurrently being dropped (Nathan Bossart)
是否有log_autoabstrum_min_duration跳过的同时被删除的表
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ab6eaee88420db58a948849d5a735997728d73a9

E.1.3.1.6.1. Information Schema
信息结构视图
●Add information_schema columns related to table constraints and triggers (Peter Eisentraut)
添加与表约束和触发器相关的information_schema列
Specifically, table_constraints.enforced, triggers.action_order, triggers.action_reference_old_table, and triggers.action_reference_new_table.
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=32ff2691173559e5f0ca3ea9cd5db134af6ee37d
E.1.3.1.7. Authentication

●Add libpq option to support channel binding when using SCRAM authentication (Michael Paquier)
添加libpq选项以支持使用SCRAM身份验证时的通道绑定
While SCRAM always prevents the replay of transmitted hashed passwords in a later session, SCRAM with channel binding also prevents man-in-the-middle attacks. The options are scram_channel_binding=tls-unique and scram_channel_binding=tls-server-end-point.
虽然SCRAM总是防止在会话中重播传输的散列密码，但是带有通道绑定的SCRAM也可以防止中间人攻击。这些选项是scram_channel_binding=tls-unique 和 scram_channel_binding=tls-server-end-point.
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d3fb72ea6de58d285e278459bca9d7cdf7f6a38b

●Allow the server to specify more complex LDAP specifications in search+bind mode (Thomas Munro)
允许服务器在search+bind模式中指定更复杂的LDAP规范
Specifically, "ldapsearchfilter" allows pattern matching using combinations of LDAP attributes.
具体来说，“ldapsearchfilter”允许使用LDAP属性的组合进行模式匹配。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=83aaac41c66959a3ebaec7daadc4885b5f98f561

●Allow LDAP authentication to use ldaps (Thomas Munro)
允许LDAP身份验证使用ldaps
We already supported LDAP over TLS by using ldaptls=1. This new TLS LDAP method of encrypted LDAP is enabled with ldapscheme=ldaps or ldapurl=ldaps://.
我们已经通过使用ldaptls=1来支持LDAP。这个新的TLS LDAP方法使用ldapscheme=ldaps或ldapurl=ldaps://。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=35c0754fadca8010955f6b10cb47af00bdbe1286

●Improve LDAP logging of errors (Thomas Munro)
改进LDAP错误日志记录
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=cf1238cd9763f0a6e3454ddf75ac56ff722f18ee

E.1.3.1.8. Permissions
权限
●Add default roles which controls file system access (Stephen Frost)
添加控制文件系统访问的默认角色
Specifically, the new roles are: pg_read_server_files, pg_write_server_files, pg_execute_server_program. These roles now also control who can use COPY and extension file_fdw. Previously only super-users could use these functions, and that is still the default behavior.
具体来说，新角色是:pg_read_server_files、pg_write_server_files、pg_execute_server_program。这些角色现在还控制谁可以使用COPY和extension file_fdw。以前只有超级用户可以使用这些功能，这仍然是默认行为
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0fdc8495bff02684142a44ab3bc5b18a8ca1863a

●Allow access to file system functions to be controlled by GRANT/REVOKE permissions, rather than super-user checks (Stephen Frost)
允许通过授予/撤销权限控制对文件系统函数的访问，而不是超级用户检查
Specifically, these functions were modified: pg_ls_dir(), pg_read_file(), pg_read_binary_file(), pg_stat_file().
具体地说，这些函数被修改了:pg_ls_dir()、pg_read_file()、pg_read_binary_file()、pg_stat_file()
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e79350fef2917522571add750e3e21af293b50fe

●Use GRANT/REVOKE to control access to lo_import() and lo_export() (Michael Paquier, Tom Lane)
使用GRANT/REVOKE控制对lo_import()和lo_export()的访问
Previously super users were exclusively granted to access these functions.
以前的超级用户只被授予访问这些功能
Compile-time option ALLOW_DANGEROUS_LO_FUNCTIONS has been removed.
编译时选项ALLOW_DANGEROUS_LO_FUNCTIONS已被删除。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5ecc0d738e5864848bbc2d1d97e56d5846624ba2

●Use view owner not session owner when preventing non-password access to postgres_fdw tables (Robert Haas)
当阻止对postgres_fdw表的非密码访问时，使用视图所有者而不是会话所有者
PostgreSQL only allows super-users to access postgres_fdw tables without passwords, e.g. via peer. Previously the session owner had to be a super-user to allow such access; now the view owner is checked instead.
PostgreSQL只允许超级用户在没有密码的情况下访问postgres_fdw表，例如通过peer。以前，会话所有者必须是超级用户才能允许这样的访问;现在检查视图所有者。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ab3f008a2dc364cf7fb75de0a691fb0c61586c8e

●Fix invalid locking permission check in SELECT FOR UPDATE on views (Tom Lane)
在SELECT中修复无效的锁定权限检查，以更新视图
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=50c6bb022475bd9ad9c73e3b68b5152db5163b22

E.1.3.1.9. Server Configuration
服务器配置
●Add server setting ssl_passphrase_command to allow supplying of the the passphrase for SSL key files (Peter Eisentraut)
添加服务器设置ssl_passphrase_command以允许为SSL密钥文件提供密码
Also add ssl_passphrase_command_supports_reload to specify whether the the SSL configuration should be reloaded and ssl_passphrase_command called during a server configuration reload.
还可以添加ssl_passphrase_command_supports_reload，以指定是否应该重新加载SSL配置，以及在服务器配置重载期间调用ssl_passphrase_command。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8a3d9425290ff5f6434990349886afae9e1c6008

●Add storage parameter toast_tuple_target to control the minimum length before TOAST storage will be considered for new rows (Simon Riggs)
添加存储参数toast_tuple_target以控制最小长度，然后考虑新的行。
The default TOAST threshold has not been changed.
未更改默认的TOAST阈值。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c2513365a0a85e77d3c21adb92fe12cfbe0d1897

●Allow server options related to memory and file sizes to be specified as number of bytes (Beena Emerson)
允许将与内存和文件大小相关的服务器选项指定为字节数
The new unit is "B". This is in addition to "kB", "MB", "GB" and "TB", which were accepted previously.
新的单位是“B”。这是除了“kB”、“MB”、“GB”和“TB”之外的，这些都是以前被接受的。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6e7baa322773ff8c79d4d8883c99fdeff5bfa679

E.1.3.1.10. Write-Ahead Log (WAL)
预写日志
●Allow the WAL file size to be set via initdb (Beena Emerson)
允许通过initdb设置WAL文件大小
Previously the 16MB default could only be changed at compile time.
以前16MB的默认值只能在编译时修改
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=fc49e24fa69a15efacd5b8958115ed9c43c48f9a

●No longer retain WAL that spans two checkpoints (Simon Riggs)
不再保留跨越两个检查点的WAL
The retention of WAL records for only one checkpoint is required.
只需要保留一个检查点的WAL记录。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4b0d28de06b28e57c540fca458e4853854fbeaf8

●Fill the unused portion of force-switched WAL segment files with zeros for improved compressibility (Chapman Flack)
用0填充强制交换的WAL段文件的未使用部分，以提高压缩能力
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4a33bb59dfc33566f04e18ab5e1f90b8e7461052

E.1.3.2. Base Backup and Streaming Replication
基本备份和流复制
●Replicate TRUNCATE activity when using logical replication (Simon Riggs, Marco Nenciarini, Peter Eisentraut)
使用逻辑复制时复制截断活动
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=039eb6e92f20499ac36cc74f8a5cef7430b706f6
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5dfd1e5a6696b271a2cdee54143fbc209c88c02f

●Pass prepared transaction information to logical replication subscribers (Nikhil Sontakke, Stas Kelvich)
将准备好的事务信息传递给逻辑复制订阅者
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1eb6d6527aae264b3e0b9c95aa70bb7a594ad1cf

●Exclude unlogged, temporary tables, and pg_internal.init files from streaming base backups (David Steele)
排除未登录的临时表和pg_internal。初始化文件，从流媒体基础备份
There is no need to copy such files.
没有必要拷贝这些文件
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8694cc96b52a967a49725f32be7aa77fd3b6ac25

●Allow heap pages checksums to be checked during streaming base backup (Michael Banck)
允许在流基备份期间检查堆页校验和
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4eb77d50c21ddd35b77421c27e0d7853eb4f9202

●Allow replication slots to be advanced programatically, rather than be consumed by subscribers (Petr Jelinek)
允许复制槽以编程方式进行高级处理，而不是由订阅者使用
This allows efficient advancement replication slots when the contents do not need to be consumed. This is performed by pg_replication_slot_advance().
当不需要消耗内容时，这就允许高效的进程复制槽。这是由pg_replication_slot_advance()执行的
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9c7d06d60680c7f00d931233873dee81fdb311c6

●Add timeline information to the backup_label file (Michael Paquier)
向backup_label文件添加时间轴信息
Also add a check that the WAL timeline matches the backup_label file's timeline.
还要添加一个检查，检查WAL时间轴是否匹配backup_label文件的时间轴
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6271fceb8a4f07dafe9d67dcf7e849b319bb2647

●Add host and port connection information to the pg_stat_wal_receiver system view (Haribabu Kommi)
向pg_stat_wal_receiver系统视图添加主机和端口连接信息
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9a895462d940c0694042059f90e5f63a0a517ded

E.1.3.3. Window Functions
窗口函数
●Add window function features to complete SQL:2011 compliance (Oliver Ford, Tom Lane)
添加窗口功能特性以完成SQL:2011遵从性
Specifically, allow RANGE mode to use PRECEDING and FOLLOWING to specify peer groups with values plus or minus the specified offset. Add GROUPS mode to include plus or minus the number of peer groups. Frame exclusion syntax was also added.
具体地说，允许RANGE模式使用前向和后向来指定具有值加减指定偏移量的对等组。添加组模式，包括加或减去对等组的数量。还添加了框架排除语法
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0a459cec96d3856f476c2db298c6b52f592894e8

E.1.3.4. Utility Commands
实用程序命令
●Allow ALTER TABLE to add a column with a non-null default without a table rewrite (Andrew Dunstan, Serge Rielau)
允许ALTER TABLE添加具有非空默认值的列，而无需重写表
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=16828d5c0273b4fe5f10f42588005f16b415b2d8

●Allow views to be locked by locking the underlying tables (Yugo Nagata)
允许通过锁定底层表来锁定视图
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=34c20de4d0b0ea8f96d0c518724d876c7b984cf5

●Allow ALTER INDEX to set statistics-gathering targets for expression indexes (Alexander Korotkov, Adrien nayrat)
允许ALTER INDEX为表达式索引设置统计数据收集目标
In psql, \d+ now shows the statistics target for indexes.
在psql中，\d+现在显示了索引的统计目标
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5b6d13eec72b960eb0f78542199380e49c8583d4

●Allow multiple tables to be specified in one VACUUM or ANALYZE command (Nathan Bossart)
允许在一个VACUUM 或 ANALYZE命令中指定多个表
Also, if any table mentioned in VACUUM uses a column list, then ANALYZE keyword must be supplied; previously ANALYZE was implied in such cases.
此外，如果VACUUM中提到的任何表使用列列表，则必须提供ANALYZE关键字;先前的分析在这种情况下是隐含的
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=11d8d72c27a64ea4e30adce11cf6c4f3dd3e60db

●Add parenthesized options syntax to ANALYZE (Nathan Bossart)
添加括号选项语法进行分析
This is similar to the syntax supported by VACUUM.
这类似于VACUUM支持的语法
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=854dd8cff523bc17972d34772b0e39ad3d6d46a4

●Add CREATE AGGREGATE option to specify the behavior of the aggregate finalization function (Tom Lane)
添加创建聚合选项来指定聚合终结函数的行为
This is useful for allowing aggregate functions be optimized and to work as window functions.
这对于允许优化聚合函数和作为窗口函数工作非常有用。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4de2d4fba38f4f7aff7f95401eb43a6cd05a6db4
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=be0ebb65f51225223421df6e10eb6e87fc8264d7

E.1.3.5. Data Types
数据类型
●Allow the creation of arrays of domains (Tom Lane)
允许创建域数组
This also allows array_agg() to be used on domains.
这也允许在域上使用array_agg()
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c12d570fa147d0ec273df53de3a2802925d551ba

●Support domains over composite types (Tom Lane)
支持域胜过复合类型
Also allow PL/PL/Perl, PL/Python, and PL/Tcl to handle composite-domain function arguments and results. Also improve PL/Python domain handling.
还允许PL/PL/Perl、PL/Python和PL/Tcl处理复合域函数参数和结果。还可以改进PL/Python域处理
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=37a795a60b4f4b1def11c615525ec5e0e9449e05
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=820c0305f64507490f00b6220f9175a303c821dd
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=60651e4cddbb77e8f1a0c7fc0be6a7e7bf626fe0
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=687f096ea9da82d267f1809a5f3fdfa027092045

●Add casts from jsonb scalars to numeric and boolean data types (Anastasia Lubennikova)
将来自jsonb标量的数据类型转换添加到数字和布尔数据类型中
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c0cbe00fee6d0a5e0ec72c6d68a035e674edc4cc

E.1.3.6. Functions
函数
●Add SHA-2 family of hash functions (Peter Eisentraut)
添加SHA-2家族的哈希函数
Specifically, sha224(), sha256(), sha384(), sha512() were added.
具体添加了sha224()、sha256()、sha384()、sha512()。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=10cfce34c0fe20d2caed5750bbc5c315c0e4cc63

●Add support for 64-bit non-cryptographic hash functions (Robert Haas, Amul Sul)
添加对64位非加密散列函数的支持
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=81c5e46c490e2426db243eada186995da5bb0ba7

●Allow to_char() and to_timestamp() to specify the time zone's hours and minutes from UTC (Nikita Glukhov, Andrew Dunstan)
允许to_char()和to_timestamp()指定时区距离UTC的小时和分钟
This is done with format specifications TZH and TZM.
这是使用格式规范TZH和TZM完成的
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=11b623dd0a2c385719ebbbdd42dd4ec395dcdc9d

●Improve the speed of aggregate computations (Andres Freund)
提高聚合计算的速度
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=69c3936a1499b772a749ae629fc59b2d72722332

●Add text search function websearch_to_tsquery() that supports a queries syntax similar to that used by web search engines (Victor Drobny, Dmitry Ivanov)
添加文本搜索函数websearch_to_tsquery()，它支持与web搜索引擎使用的查询语法类似的查询语法
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1664ae1978bf0f5ee940dc2fc8313e6400a7e7da

●Add function json(b)_to_tsvector() to create text search query for matching JSON/JSONB values (Dmitry Dolgov)
添加函数json(b)_to_tsvector()来创建匹配json /JSONB值的文本搜索查询
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1c1791e00065f6986f9d44a78ce7c28b2d1322dd

E.1.3.7. Server-Side Languages
服务器端语言
●Add SQL procedures, which can start and commit their own transactions (Peter Eisentraut)
添加SQL过程，它可以启动和提交自己的事务。
They are created with the new CREATE PROCEDURE command and invoked via CALL. The new ALTER/DROP ROUTINE commands allows altering/dropping of procedures, functions, and aggregates.
它们使用新的CREATE PROCEDURE命令创建，并通过调用调用。新的ALTER/DROP例程命令允许改变/DROP过程、函数和聚合
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e4128ee767df3c8c715eb08f8977647ae49dfb59
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=76b6aa41f41db66004b1c430f17a546d4102fbe7
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=33803f67f1c4cb88733cce61207bbf2bd5b599cc
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a8677e3ff6bb8ef78a9ba676faa647bba237b1c4

●Add transaction control to PL/pgSQL, PL/Perl, PL/Python, PL/Tcl, and SPI server-side languages (Peter Eisentraut)
向PL/pgSQL、PL/Perl、PL/Python、PL/Tcl和SPI服务器端语言添加事务控制
Transaction control is only available to top-transaction-level CALLs or in nested PL/pgSQL DO and CALL blocks that only contain other PL/pgSQL DO and CALL blocks. ACCURATE?
事务控制只适用于顶级事务级别的调用或嵌套的PL/pgSQL DO和调用块，这些调用块只包含其他PL/pgSQL DO和调用块。准确?
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8561e4840c81f7e345be2df170839846814fa004
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d92bc83c48bdea9888e64cf1e2edbac9693099c9
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=056a5a3f63f1a29d9266165ee6e25c6a51ddd63c
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b981275b6531df5a4c4f069571bcb39fc4dee770

●Add the ability to define PL/pgSQL record types as not null, constant, or with initial values (Tom Lane)
添加将PL/pgSQL记录类型定义为非null、常量或具有初始值的能力
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f9263006d871d127794a402a7bef713fdd882156

●Add extension jsonb_plpython to transform JSONB to/from PL/Python types (Anthony Bykov)
添加扩展jsonb_plpython来将JSONB转换为/从PL/Python类型
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3f44e3db72ad4097aae078c075a9b3cb3d6b761b

●Add extension jsonb_plperl to transform JSONB to/from PL/Perl types (Anthony Bykov)
添加扩展jsonb_plperl来将JSONB转换为/从PL/Perl类型
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=341e1661805879db958dde0a9ed1dc44b1bb10c3

E.1.3.8. Client Interfaces
客户端接口
●Change libpq to disable compression by default (Peter Eisentraut)
更改libpq以在默认情况下禁用压缩
Compression is already disabled in modern OpenSSL versions and the libpq setting had no effect in that case.
在现代的OpenSSL版本中，压缩已经被禁用，在这种情况下，libpq设置没有作用
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e3bdb2d92600ed45bd46aaf48309a436a9628218

●Add DO CONTINUE action to the ECPG WHENEVER statement (Vinayak Pokale)
每当语句时，向ECPG添加DO CONTINUE动作
This generates a C 'continue' statement, causing a return to the top of the contained loop when the specified condition occurs.
这将生成一个C 'continue'语句，当指定的条件发生时，返回到所包含循环的顶部。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d22e9d530516f7c9c56d00eff53cf19e45ef348c

●Add ecpg mode to enable Oracle Pro*C handling of char arrays.
添加ecpg模式以启用Oracle Pro*C处理char数组
This mode is enabled with -C.
使用-C启用此模式
E.1.3.9. Client Applications
客户应用程序
E.1.3.9.1. psql

●Add psql command \gdesc to display the column names and types of the query output (Pavel Stehule)
添加psql命令\gdesc来显示查询输出的列名和类型
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=49ca462eb165dea297f1f110e8eac064308e9d51

●Add psql variables to report query activity and errors (Fabien Coelho)
添加psql变量来报告查询活动和错误
Specifically, the new variables are ERROR, SQLSTATE, ROW_COUNT, LAST_ERROR_MESSAGE, and LAST_ERROR_SQLSTATE.
具体来说，新的变量是ERROR、SQLSTATE、ROW_COUNT、LAST_ERROR_MESSAGE和LAST_ERROR_SQLSTATE。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=69835bc8988812c960f4ed5aeee86b62ac73602a

●Allow psql to test for the existence of a variable (Fabien Coelho)
允许psql测试变量的存在性
Specifically , the syntax :{?variable_name} allows a variable's existence to be tested in an \if statement.
具体来说，语法:{?variable_name}允许在\if语句中测试变量的存在。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d57c7a7c506276597af619bdb8c62fa5b592745a

●Add PSQL_PAGER to control psql's pager (Pavel Stehule)
添加PSQL_PAGER来控制psql的用户
This allows psql's default pager to be specified as a separate environment variable from the pager for other applications. PAGER is still honored if PSQL_PAGER is not set.
这允许将psql的默认分页器指定为与其他应用程序的分页器分离的环境变量。如果PSQL_PAGER没有设置，PAGER仍然是受尊敬的。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5e8304fdce2d5c41ef7a648ed0a622480f8f0a07

●Have psql \d+ always show the partition information (Amit Langote, Ashutosh Bapat)
是否psql \d+总是显示分区信息
Previously partition information would not be displayed for a partitioned table if it had no partitions. Also indicate which partitions are themselves partitioned.
以前，如果分区表没有分区，则不会显示分区信息。还要指出哪些分区本身是分区的
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=05b6ec39d72f7065bb5ce770319e826f1da92441

●Have psql report the proper user name before the password prompt (Tom Lane)
在密码提示符之前有psql报告用户名
Previously, combinations of -U and a user name embedded in a URI caused incorrect reporting. Also suppress the user name before the password prompt when --password is specified.
以前，在URI中嵌入-U和用户名的组合会导致不正确的报告。还可以在指定密码时，在密码提示符前抑制用户名。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=15be27460191a9ffb149cc98f6fbf97c369a6b1e

●Allow quit and exit to exit psql when used in an empty buffer (Bruce Momjian)
在空缓冲区中使用时，允许退出和退出psql
Also add hints of how to exit when quit and exit are used alone on a line in a non-empty buffer. Add a similar hint for help.
在非空缓冲区的行中单独使用退出和退出时，还要添加如何退出的提示。添加类似的帮助提示
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=df9f599bc6f14307252ac75ea1dc997310da5ba6

●Have psql hint at using control-D when \q is entered alone on a line but ignored (Bruce Momjian)
当只在一行中输入一个\q但被忽略时，psql是否暗示要使用control-D
For example, \q does not exit when supplied in character strings.
例如，当在字符串中提供时，\q不会退出。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=91389228a1007fa3845e29e17568e52ab1726d5d

●Improve tab-completion for ALTER INDEX RESET/SET (Masahiko Sawada)
改进修改索引重置/设置的表完成
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2b8c94e1b4a86907fceef87840c32d3703f7e161

●Add infrastructure to allow psql to customize tab completion queries based on the server version (Tom Lane)
添加基础设施以允许psql根据服务器版本定制选项卡完成查询
Previously tab completion queries could fail.
以前的选项卡完成查询可能会失败
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=722408bcd1bde0b007f73b41135382af11b0282d

E.1.3.9.2. pgbench

●Add pgbench expressions support for NULLs, booleans, and some functions and operators (Fabien Coelho)
添加对null、布尔值和一些函数和操作符的pgbench表达式支持
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=bc7fa0c15c590ddf4872e426abd76c2634f22aca

●Add \if conditional support to pgbench (Fabien Coelho)
向pgbench添加\if条件支持
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f67b113ac62777d18cd20d3c4d05be964301b936

●Allow the use of non-ASCII characters in pgbench variable names (Fabien Coelho)
允许在pgbench变量名称中使用非ascii字符
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9d36a386608d7349964e76120e48987e3ec67d04

●Add pgbench option --init-steps to control the initialization steps performed (Masahiko Sawada)
添加pgbench选项--init-steps用于控制执行的初始化步骤的单元步骤。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=591c504fad0de88b559bf28e929d23672179a857

●Add approximated Zipfian-distributed random generator to pgbench (Alik Khilazhev)
在pgbench中添加近似的zipfian分布的随机生成器。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1fcd0adeb38d6ef36066134bb3b44acc5a249a98

●Allow the random seed to be set in pgbench (Fabien Coelho)
允许在pgbench中设置随机种子
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=64f85894ad2730fb1449a8e81dd8026604e9a546

●Allow pgbench to do exponentiation with pow() and power() (Raúl Marín Rodríguez)
允许pgbench使用pow()和power()进行指数处理
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7a727c180aa3c3baba12957d4cbec7b022ba4be5

●Add hashing functions to pgbench (Ildar Musin)
向pgbench添加哈希函数
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e51a04840a1c45db101686bef0b7025d5014c74b

●Make pgbench statistics more accurate when using --latency-limit and --rate (Fabien Coelho)
使pgbench统计数据在使用延迟限制和速率时更加准确
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c23bb6badfa2048d17c08ebcfd81adf942292e51
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=16827d442448d1935ed644e944a4cb8213345351

E.1.3.10. Server Applications
服务器应用
●Add pg_basebackup option to create a named replication slot (Michael Banck)
添加pg_basebackup选项以创建一个指定的复制槽。
The option --create-slot creates the named replication slot (--slot) when the WAL streaming method (-wal-method=stream) is used.
选项——create-slot在使用WAL - WAL - mart方法=stream时创建指定的复制slot(—slot)
IS IT CLEAR FROM THE DOCS THAT THE REPLICATION SLOT IS NOT TEMPORARY?
从文档中可以清楚地看出复制槽不是临时的吗?
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3709ca1cf069cee24ef8000cb6a479813b5537df

●Allow initdb to set group read access to the data directory (David Steele)
允许initdb设置对数据目录的组读访问
This is accomplished with the initdb --allow-group-access flag. Administrators can also set group permissions on the empty data directory before running initdb. Server variable data_directory_mode allows reading of data directory group permissions.
这是通过initdb—允许的组访问标志实现的。管理员还可以在运行initdb之前在空数据目录上设置组权限。服务器变量data_directory_mode允许读取数据目录组权限。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c37b3d08ca6873f9d4eaf24c72a90a550970cbb8

●Add pg_verify_checksums tool to verify database checksums while offline (Magnus Hagander)
添加pg_verify_checksum工具，在脱机时验证数据库校验和
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1fde38beaa0c3e66c340efc7cc0dc272d6254bb0
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a228cc13aeabff308d6dfc98a1015865f5393fce

●Allow pg_resetwal to change the WAL segment size via --wal-segsize (Nathan Bossart)
允许pg_resetwal改变WAL segment的大小--wal-segsize
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=bf4a8676c316c177f395b54d3305ea4ccc838a66

●Add long options to pg_resetwal and pg_controldata (Nathan Bossart, Peter Eisentraut)
向pg_resetwal和pg_controldata添加长选项
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e22b27f0cb3ee03ee300d431997f5944ccf2d7b3

●Add pg_receivewal option --no-sync to prevent synchronous WAL writes, for testing (Michael Paquier)
添加pg_receivewal选项--no-sync以防止同步写，用于测试
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5f3971291fc231bb65a38198b1bcb1c29ef63108

●Add pg_receivewal option --endpos to specify when WAL receiving should stop (Michael Paquier)
添加pg_receivewal选项——endpos来指定WAL接收何时停止
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6d9fa52645e71711410a66b5349df3be0dd49608

●Allow pg_ctl to send the SIGKILL signal to processes (Andres Freund)
允许pg_ctl向进程发送SIGKILL信号
This was originally unsupported due to concerns over its misuse.
由于对其滥用的担心，这最初是不支持的
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2e83db3ad2da9b073af9ae12916f0b71cf698e1e

●Reduce the number of files copied by pg_rewind (Michael Paquier)
减少pg_rewind复制的文件的数量。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=266b6acb312fc440c1c1a2036aa9da94916beac6

●Prevent pg_rewind from running as root (Michael Paquier)
防止pg_rewind用root用户运行
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5d5aeddabfe0b6b21f556c72a71e0454833d63e5

E.1.3.10.1. pg_dump, pg_dumpall, pg_restore

●Add pg_dumpall option --encoding to control encoding (Michael Paquier)
添加pg_dumpall选项--encoding来控制编码
pg_dump already had this option.
pg_dump已经有这个选项。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=84be67181aab22ea8723ba0625ee690223cd8785

●Add pg_dump option --load-via-partition-root to force loading of data into the partition's root table, rather than the original partitions (Rushabh Lathia)
添加pg_dump选项--load-via-partition-root，以强制将数据加载到分区的根表中，而不是原始分区
This is useful if the system to be loaded has a different collation definitions or endianness, requiring the rows to be stored in different partitions.
如果要加载的系统具有不同的排序定义或endianness，需要将行存储在不同的分区中，那么这将非常有用。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=23d7680d04b958de327be96ffdde8f024140d50e

●Add ability to suppress dumping and restoring of comments (Robins Tharakan)
增加抑制倾倒和恢复评论的能力
The new pg_dump, pg_dumpall, and pg_restore option is --no-comments.
新的pg_dump、pg_dumpall和pg_restore选项是——无注释
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1368e92e16a098338e39c8e540bdf9f6cf35ebf4

E.1.3.11. Source Code
源代码
●Add support for large pages on Windows (Takayuki Tsunakawa, Thomas Munro)
增加对Windows上大页面的支持
This is controlled by the huge_pages configuration parameter.
这由huge_pages配置参数控制。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1cc4f536ef86928a241126ca70d121873594630e

●Add support for ARMv8 hardware CRC calculations (Yuqi Gu, Heikki Linnakangas)
增加对ARMv8硬件CRC计算的支持
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f044d71e331d77a0039cec0a11859b5a3c72bc95

●Convert documentation to DocBook XML (Peter Eisentraut, Alexander Lakhin, Jürgen Purtz)
将文档转换为DocBook XML
The file names still use an sgml extension for compatibility with back branches.
为了与后分支的兼容性，文件名仍然使用sgml扩展名
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1c53f612bc8c9dbf97aa5a29910654a66dcdd307
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c29c578908dc0271eeb13a4014e54bff07a29c05
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1ff01b3902cbf5b22d1a439014202499c21b2994
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3c49c6facb22cdea979f5d1465ba53f972d32163

●Overhaul the way system tables are defined for bootstrap use (John Naylor)
修改系统表的定义方式以供引导使用
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a351679c806ec9591ef4aaf5534d642e35140b9d
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=372728b0d49552641f0ea83d9d2e08817de038fa
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a0854f10722b20a445f5e67a357bd8809b32f540

●Allow background workers to attach to databases that normally disallow connections (Magnus Hagander)
允许后台工作人员连接到通常不允许连接的数据库
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=eed1ce72e1593d3e8b7461d7744808d4d6bf402b

●Speed up lookups of builtin function names matching oids (Andres Freund)
加快查找与oid匹配的内建函数名
The previous binary search now uses a lookup array.
以前的二进制搜索现在使用查找数组
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=212e6f34d55c910505f87438d878698223d9a617

●Speed up construction of query results (Andres Freund)
加快查询结果的构建
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1de09ad8eb1fa673ee7899d6dfbb2b49ba204818

●Improve access speed to system caches (Andres Freund)
提高系统缓存的访问速度
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=141fd1b66ce6e3d10518d66d4008bd368f1505fd

●Add a generational memory allocator which is optimized for serial allocation/deallocation (Tomas Vondra)
添加为串行分配/释放而优化的分代内存分配器
This reduces memory usage for logical decoding.
这减少了逻辑解码的内存使用
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a4ccc1cef5a04cc054af83bc4582a045d5232cb3

●Make the computation of system column pg_class.reltuples consistent (Tomas Vondra)
计算系统列pg_class.reltuples一致
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7c91a0364fcf5d739a09cc87e7adb1d4a33ed112

●Update to use perltidy version 20170521 (Tom Lane)
更新使用perltidy版本20170521
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=46cda5bf7bc209554b3c1bbb3040b45735387e0c

E.1.3.12. Additional Modules
附加模块
●Allow extension pg_prewarm to restore the previous shared buffer contents on startup (Mithun Cy, Robert Haas)
允许扩展pg_prewarm在启动时恢复之前的共享缓冲区内容
This is accomplished by having pg_prewarm store the shared buffer relation/offset values to disk occasionally during server operation and shutdown.
这是通过让pg_prewarm在服务器操作和关闭期间偶尔将共享缓冲区关系/偏移值存储到磁盘来实现的。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=79ccd7cbd5ca44bee0191d12e9e65abf702899e7

●Add pgtrgm function strict_word_similarity() to compute the similarity of whole words (Alexander Korotkov)
添加pgtrgm函数strict_word_similarity()来计算整个单词的相似度
The function word_similarity() already existed for this purpose, but it was designed to find similar parts of words, while strict_word_similarity() computes the similarity to whole words.
函数word_similarity()已经为此目的而存在，但它设计用于查找单词的相似部分，而strict_word_similarity()则计算与整个单词的相似度。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=be8a7a6866276b228b4ffaa3003e1dc2dd1d140a

●Allow creation of indexes on citext extension columns that can be used by LIKE comparisons (Alexey Chernyshov)
允许在citext扩展列上创建索引，类似比较可以使用这些索引
Specifically, indexes must be created using the citext_pattern_ops operator class.
特别是，必须使用citext_pattern_ops运算符类来创建索引
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f2464997644c64b5dec93ab3c08305f48bfe14f1

●Allow btree_gin to index bool, bpchar, name and uuid data types (Matheus Oliveira)
允许btree_gin索引bool、bpchar、name和uuid数据类型
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f4cd7102b5a6097fb603c789728fbfd5d6fd43c5

●Allow cube and seg extensions using GiST indexes to perform index-only scans (Andrey Borodin)
允许使用GiST索引进行多维数据集和seg扩展，以执行仅索引的扫描
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=de1d042f5979bc1388e9a6d52a4d445342b04932

●Allow retrieval of negative cube coordinates using the ~> operator (Alexander Korotkov)
允许使用~>操作符检索负立方体坐标
This is useful for KNN-GiST searches. HOW?
这对于KNN-GiST搜索是有用的。如何?
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f50c80dbb17efa39c169f6c510e9464486ff5edc

●Add Vietnamese letter detection to the unaccent extension (Dang Minh Huong, Michael Paquier)
在非重音扩展中添加越南字母检测
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ec0a69e49bf41a37b5c2d6f6be66d8abae00ee05

●Enhance amcheck to check that each heap tuple has an index entry (Peter Geoghegan)
增强amcheck检查每个堆tuple是否有一个索引条目。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7f563c09f8901f6acd72cb8fba7b1bd3cf3aca8e

●Have adminpack use the new default file system access roles (Stephen Frost)
adminpack是否使用新的默认文件系统访问角色
Previously only super-users could call adminpack functions; now role permissions are checked.
以前只有超级用户可以调用adminpack函数;现在检查角色权限
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=11523e860f8fe29f9142fb63c44e01cd0d5e7375

●Increase pg_stat_statement's query id to 64 bits (Robert Haas)
将pg_stat_statement的查询id增加到64位
This greatly reduces the chance of query id hash collisions. The query id can now potentially display as a negative value.
这大大减少了查询id哈希冲突的机会。查询id现在可能显示为负值。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=cff440d368690f94fbda1a475277e90ea2263843

●Install errcodes.txt to provide access to the error codes reported by PostgreSQL (Thomas Munro)
安装errcodes.txt提供对PostgreSQL报告的错误代码的访问
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1fd8690668635bab9dfa16b2885e6e474f8451ba

●Prevent extensions from creating custom server variables that take a quoted list of values (Tom Lane)
防止扩展创建接受引用的值列表的自定义服务器变量
This was never intended to be supported.
这从来都不是为了得到支持。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=846b5a525746b83813771ec4720d664408c47c43

●Remove contrib/start-scripts/osx since they are no longer recommended (Tom Lane)
删除contrib/start-scripts/osx，它们不再被推荐
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=527878635030489e464d965b3b64f6caf178f641

●Remove extension chkpass (Peter Eisentraut)
删除扩展chkpass
This extension no longer served as a usable security tool or example of how to write an extension.
这个扩展不再是一个可用的安全工具或如何编写扩展的示例。
https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5d3cad564729f64d972c5c803ff34f0eb40bfd0c