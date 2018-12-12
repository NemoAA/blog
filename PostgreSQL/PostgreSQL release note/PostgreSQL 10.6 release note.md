### E.3.2. Changes

- Ensure proper quoting of transition table names when pg_dump emits `CREATE TRIGGER ... REFERENCING` commands (Tom Lane)

  当pg_dump发出 CREATE TRIGGER ... REFERENCING 命令时确保适当地引用转换表名称

  This oversight could be exploited by an unprivileged user to gain superuser privileges during the next dump/reload or pg_upgrade run. (CVE-2018-16850)

  在下一次转储/重新加载或pg_upgrade运行时，非特权用户可以利用这种疏忽获得超级用户特权

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=350410be459ccda7eeeea35b56b5f2d24391f90c

- Fix corner-case failures in `has_*foo*_privilege()` family of functions (Tom Lane)

  修复了has_*foo*_privilege()函数家族中的corner-case错误

  Return NULL rather than throwing an error when an invalid object OID is provided. Some of these functions got that right already, but not all. `has_column_privilege()` was additionally capable of crashing on some platforms.

  返回NULL，而不是在提供无效对象OID时抛出错误。其中一些函数已经算对了，但不是全部。has_column_privilege()还会在某些平台上崩溃。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=3d0f68dd30612db8d8cf6529455a369ad121c521

- Fix `pg_get_partition_constraintdef()` to return NULL rather than fail when passed an invalid relation OID (Tom Lane)

  修复pg_get_partition_constraintdef()在传递无效关系OID时返回NULL而不是失败

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=aaf10f32a308bc5f53772c773edf3f345f59bb74

- Avoid O(N^2) slowdown in regular expression match/split functions on long strings (Andrew Gierth)

  避免O (N ^ 2)放缓在长字符串正则表达式匹配/分裂功能

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c8ea87e4bd950572cba4575e9a62284cebf85ac5

- Fix parsing of standard multi-character operators that are immediately followed by a comment or `+` or `-` (Andrew Gierth)

  修复了标准多字符操作符的解析，这些操作符后面紧跟着注释或+或-

  This oversight could lead to parse errors, or to incorrect assignment of precedence.

  这种疏忽可能导致解析错误，或者导致优先级分配不正确。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a40631a920accbcca1a49a909d380308d95b4674

- Avoid O(N^3) slowdown in lexer for long strings of `+` or `-` characters (Andrew Gierth)

  避免O(N ^ 3)放缓词法分析程序长时间+或-字符的字符串

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d4a63f829702cf28adb5db7e2ed44d2d9d893451

- Fix mis-execution of SubPlans when the outer query is being scanned backwards (Andrew Gierth)

  修复在向后扫描外部查询时子计划执行错误

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=520acab171244b55d816c70b9a89280b09937925

- Fix failure of `UPDATE/DELETE ... WHERE CURRENT OF ...` after rewinding the referenced cursor (Tom Lane)

  修复UPDATE/DELETE ... WHERE CURRENT OF ... 在重绕所引用的游标之后

  A cursor that scans multiple relations (particularly an inheritance tree) could produce wrong behavior if rewound to an earlier relation.

  扫描多个关系(特别是继承树)的游标如果重绕到以前的关系，可能会产生错误的行为。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=89b280e139c463c98eb33592216a123e89052d08

- Fix `EvalPlanQual` to handle conditionally-executed InitPlans properly (Andrew Gierth, Tom Lane)

  修正EvalPlanQual处理有条件执行的初始计划

  This resulted in hard-to-reproduce crashes or wrong answers in concurrent updates, if they contained code such as an uncorrelated sub-`SELECT` inside a `CASE` construct.

  这导致了并发更新中难以复制的崩溃或错误的答案，如果它们包含代码，比如案例结构中不相关的子选择。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1f4a920b7309499d2d0c4ceda5e6356e10bc51da

- Prevent creation of a partition in a trigger attached to its parent table (Amit Langote)

  防止在连接到父表的触发器中创建分区

  Ideally we'd allow that, but for the moment it has to be blocked to avoid crashes.

  理想情况下，我们会允许这样做，但目前它必须被阻止以避免崩溃。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=dc3e436b191a8f8d6f35fad952dd3dc314ccabf9

- Fix problems with applying `ON COMMIT DELETE ROWS` to a partitioned temporary table (Amit Langote)

  修复将COMMIT DELETE行应用到分区临时表的问题

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4bc772e2afa55f26734ff3fbdf27601db030b7e5

- Fix character-class checks to not fail on Windows for Unicode characters above U+FFFF (Tom Lane, Kenji Uno)

  修正在Windows平台上对U+FFFF以上编码的字符的检查。

  This bug affected full-text-search operations, as well as `contrib/ltree` and `contrib/pg_trgm`.

  它会影响全文搜索功能，以及`contrib/ltree`和`contrib/pg_trgm`模块；

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=981dc2baa8e08483bfe4b20f9e5ab3cad711ba98

- Disallow pushing sub-`SELECT`s containing window functions, `LIMIT`, or `OFFSET` to parallel workers (Amit Kapila)

  不允许推子选择包含窗口函数、限制或偏移到并行工作者

  Such cases could result in inconsistent behavior due to different workers getting different answers, as a result of indeterminacy due to row-ordering variations.

  这种情况可能会导致不同的进程得到不同的答案而导致不一致的行为，也可能会导致由于行序差异而导致的不确定性。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=14e9b2a752efaa427ce1b400b9aaa5a636898a04

- Ensure that sequences owned by a foreign table are processed by `ALTER OWNER` on the table (Peter Eisentraut)

  确保由外部表拥有的序列由表上的ALTER OWNER处理

  The ownership change should propagate to such sequences as well, but this was missed for foreign tables.

  所有权更改也应该传播到这些序列中，但是对于外部表来说，这一点被忽略了。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=0320ddaf3c08ea17d616549d0e7f45239592fc76

- Ensure that the server will process already-received `NOTIFY` and `SIGTERM` interrupts before waiting for client input (Jeff Janes, Tom Lane)

  确保服务器将在等待客户端输入之前处理已经收到的通知和SIGTERM中断

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2ddb9149d14de9a2e7ac9ec6accf3ad442702b24

- Fix over-allocation of space for `array_out()`'s result string (Keiichi Hirobe)

  修复array_out()结果字符串的空间分配过度问题

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=87d9bbca13f9c6b8f6ee986f0e399cb83bd731d4

- Avoid query-lifetime memory leak in `XMLTABLE` (Andrew Gierth)

  避免XMLTABLE中的查询生命周期内存泄漏

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=07172d5aff8f43cd6ce09f57a0b56a535d7eaf45

- Fix memory leak in repeated SP-GiST index scans (Tom Lane)

  修正在使用特定条件下的SP-GiST而造成的内存泄漏；

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=696b0c5fd0a8765fe6dfd075a30be06b448fd615

- Ensure that `ApplyLogicalMappingFile()` closes the mapping file when done with it (Tomas Vondra)

  确保ApplyLogicalMappingFile()在处理完映射文件后关闭它

  Previously, the file descriptor was leaked, eventually resulting in failures during logical decoding.

  以前，文件描述符被泄漏，最终导致逻辑解码过程中的失败。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=fa73b377ee11ced0c051fb42c29a87b5c71b79e3

- Fix logical decoding to handle cases where a mapped catalog table is repeatedly rewritten, e.g. by `VACUUM FULL` (Andres Freund)

  修复逻辑解码，以处理映射目录表被重复重写的情况，例如通过VACUUM FULL

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e9edc1ba0be21278de8f04a068c2fb3504dc03fc

- Prevent starting the server with `wal_level` set to too low a value to support an existing replication slot (Andres Freund)

  当`wal_level`设置为一个不支持当前已有复制slot的参数时，禁止PostgreSQL的启动；

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=691d79a0793328a45b01348675ba677aa7623bec

- Avoid crash if a utility command causes infinite recursion (Tom Lane)

  如果实用程序命令导致无限递归，则避免崩溃

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d48da369ab22a8326d4d3d2b05b574d581057193

- When initializing a hot standby, cope with duplicate XIDs caused by two-phase transactions on the master (Michael Paquier, Konstantin Knizhnik)

  在初始化热备份时，要处理主服务器上两阶段事务导致的重复xid

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1df21ddb19c6e764fc9378c900515a5d642ad820

- Fix event triggers to handle nested `ALTER TABLE` commands (Michael Paquier, Álvaro Herrera)

  修复处理嵌套ALTER TABLE命令的事件触发器

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ad08006ba03797fed431af87de6e66c6c0985b7a

- Propagate parent process's transaction and statement start timestamps to parallel workers (Konstantin Knizhnik)

  将父进程的事务和语句开始时间戳传播给并行工作者

  This prevents misbehavior of functions such as `transaction_timestamp()` when executed in a worker.

  这可以防止在worker中执行transaction_timestamp()等函数的错误行为。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=07ee62ce9e507c14632c0517aeeae4e60b0d1997

- Fix transfer of expanded datums to parallel workers so that alignment is preserved, preventing crashes on alignment-picky platforms (Tom Lane, Amit Kapila)

  修正了将扩展数据传输到并行进程的问题，从而保持对齐，防止在alignment-picky的平台上崩溃

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9bc9f72b28fe4d2c22244f3443af8f1b98b56474

- Fix WAL file recycling logic to work correctly on standby servers (Michael Paquier)

  修复了在备用服务器上正确工作的WAL文件回收逻辑

  Depending on the setting of `archive_mode`, a standby might fail to remove some WAL files that could be removed.

  根据archive_mode的设置，备用程序可能无法删除一些可以删除的WAL文件。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=78ea8b5daab9237fd42d7a8a836c1c451765499f

- Fix handling of commit-timestamp tracking during recovery (Masahiko Sawasa, Michael Paquier)

  修复在恢复期间对提交时间戳跟踪的处理

  If commit timestamp tracking has been turned on or off, recovery might fail due to trying to fetch the commit timestamp for a transaction that did not record it.

  如果已打开或关闭了提交时间戳跟踪，那么由于试图为没有记录它的事务获取提交时间戳，恢复可能会失败。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8d28bf500f6536e295e9c3d7b85cdfec1c4dc913

- Randomize the `random()` seed in bootstrap and standalone backends, and in initdb (Noah Misch)

  随机化bootstrap和独立后端和initdb中的random()种子

  The main practical effect of this change is that it avoids a scenario where initdb might mistakenly conclude that POSIX shared memory is not available, due to name collisions caused by always using the same random seed.

  这种更改的主要实际效果是，它避免了这样一种情况:initdb可能错误地认为POSIX共享内存不可用，因为总是使用相同的random seed会导致名称冲突。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d18f6674bd60e923bcdbf0fd916685b0a250c60f

- Fix possible shared-memory corruption in DSA logic (Thomas Munro)

  修复DSA逻辑中可能的共享内存损坏

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=38763d67784c6563d08dbea5c9f913fa174779b8

- Allow DSM allocation to be interrupted (Chris Travers)

  允许中断DSM分配

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=422952ee78220c49812b7697c7855c6230840e35

- Avoid failure in a parallel worker when loading an extension that tries to access system caches within its init function (Thomas Munro)

  在加载试图访问init函数中的系统缓存的扩展时，避免在并行工作者中发生故障

  We don't consider that to be good extension coding practice, but it mostly worked before parallel query, so continue to support it for now.

  我们不认为这是一种好的扩展编码实践，但它主要在并行查询之前工作，所以现在继续支持它。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6c3c9d418918373a9535ad3d3bd357f652a367e3

- Properly handle turning `full_page_writes` on dynamically (Kyotaro Horiguchi)

  正确处理动态打开full_page_write

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=bc153c941d2ec4e605b1e79be9478abc3d166a18

- Fix possible crash due to double `free()` during SP-GiST rescan (Andrew Gierth)

  修复SP-GiST重新扫描过程中可能出现的双free()崩溃

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=500d49794f1f61cb20f485bd5c5052c122e58cf9

- Prevent mis-linking of src/port and src/common functions on ELF-based BSD platforms, as well as HP-UX and Solaris (Andrew Gierth, Tom Lane)

  防止基于BSD平台以及HP-UX和Solaris上的src/port和src/common函数的错误链接，

  Shared libraries loaded into a backend's address space could use the backend's versions of these functions, rather than their own copies as intended. Since the behavior of the two sets of functions isn't quite the same, this led to failures.

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=e3d77ea6b4e425093db23be492f236896dd7b501

- Avoid possible buffer overrun when replaying GIN page recompression from WAL (Alexander Korotkov, Sivasubramanian Ramasubramanian)

  当从WAL重新压缩GIN页面时，避免可能的缓冲区溢出

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5f08accdad2b03e0107bdc73d48783a01fe51c8c

- Avoid overrun of a hash index's metapage when `BLCKSZ` is smaller than default (Dilip Kumar)

  当BLCKSZ小于默认值时，避免哈希索引的元索引溢出

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ac27c74def5d8544530b13d5901308a342f072ac

- Fix missed page checksum updates in hash indexes (Amit Kapila)

  修复散列索引中丢失的页面校验和更新

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=7c9e19ca9a4de6eb98582548ec6dd0d83fc5ac2d

- Fix missed fsync of a replication slot's directory (Konstantin Knizhnik, Michael Paquier)

  修复了复制槽目录的fsync丢失的问题

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=caa0c6ceba1fd6ec7b027532d68cecf5dfbbb2db

- Fix unexpected timeouts when using `wal_sender_timeout` on a slow server (Noah Misch)

  修复在慢速服务器上使用wal_sender_timeout时出现的意外超时

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ab0ed6153a58294143d6d66ec5f3471477c59d57

- Ensure that hot standby processes use the correct WAL consistency point (Alexander Kukushkin, Michael Paquier)

  确保热备份进程使用正确的WAL一致性点

  This prevents possible misbehavior just after a standby server has reached a consistent database state during WAL replay.

  这可以防止备用服务器在WAL重做期间达到一致的数据库状态后出现错误行为。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c186ba135ecafe987842920829629ef466ce6ce1

- Ensure background workers are stopped properly when the postmaster receives a fast-shutdown request before completing database startup (Alexander Kukushkin)

  当postmaster 在完成数据库启动之前收到快速关闭请求时，确保后台进程被正确停止

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=55875b6d2aa0946226e9261ee691cb519d92f8c1

- Update the free space map during WAL replay of page all-visible/frozen flag changes (Álvaro Herrera)

  在WAL日志重做时，页面 all-visible/frozen标志更改，更新空闲空间映射

  Previously we were not careful about this, reasoning that the FSM is not critical data anyway. However, if it's sufficiently out of date, that can result in significant performance degradation after a standby has been promoted to primary. The FSM will eventually be healed by updates, but we'd like it to be good sooner, so work harder at maintaining it during WAL replay.

  之前我们对此并不谨慎，认为FSM并不是关键数据。但是，如果它已经过时了，那么在将备用服务器提升到主服务器之后，可能会导致性能显著下降。FSM最终会通过更新得到修复，但我们希望它能更快地变得更好，所以在WAL重播期间要更加努力地维护它。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=ab7dbd681c54d993fc8ebf8a413668fd75a4be0b

- Avoid premature release of parallel-query resources when query end or tuple count limit is reached (Amit Kapila)

  当达到查询结束或元组计数限制时，避免过早释放并行查询资源

  It's only okay to shut down the executor at this point if the caller cannot demand backwards scan afterwards.

  只有在此时关闭执行程序，调用方才可以在调用后要求向后扫描。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2cd0acfdade82f3cab362fd9129d453f81cc2745

- Don't run atexit callbacks when servicing `SIGQUIT` (Heikki Linnakangas)

  在服务SIGQUIT时不要运行退出回调

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=8e19a82640d3fa2350db146ec72916856dd02f0a

- Don't record foreign-server user mappings as members of extensions (Tom Lane)

  不要将外部服务器用户映射为扩展的成员

  If `CREATE USER MAPPING` is executed in an extension script, an extension dependency was created for the user mapping, which is unexpected. Roles can't be extension members, so user mappings shouldn't be either.

  如果在扩展脚本中执行创建用户映射，则会为用户映射创建扩展依赖项，这是不可预料的。角色不能是扩展成员，因此用户映射也不应该是扩展成员。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=9b7c56d6cba9d23318d98af58f0c1adc85869bbf

- Make syslogger more robust against failures in opening CSV log files (Tom Lane)

  使syslogger在打开CSV日志文件时更加详细

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=bff84a547d71cd466c21f9c4625e64340aab7dd2

- When libpq is given multiple target host names, do the DNS lookups one at a time, not all at once (Tom Lane)

  当给libpq提供多个目标主机名时，一次执行一个DNS查找，而不是一次全部查找

  This prevents unnecessary failures or slow connections when a connection is successfully made to one of the earlier servers in the list.

  当成功连接到列表中较早的服务器时，这可以防止不必要的故障或减慢连接速度。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5ca00774194dc179d02867d536b73eb85fffd227

- Fix libpq's handling of connection timeouts so that they are properly applied per host name or IP address (Tom Lane)

  修复了libpq对连接超时的处理，以便每个主机名或IP地址都正确地应用这些超时

  Previously, some code paths failed to restart the timer when switching to a new target host, possibly resulting in premature timeout.

  以前，在切换到新目标主机时，一些代码路径无法重新启动计时器，可能导致提前超时。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1e6e98f7638904b2aa4df0bd87064239ce9d8fcf

- Fix psql, as well as documentation examples, to call `PQconsumeInput()` before each `PQnotifies()` call (Tom Lane)

  修复psql以及文档示例，以便在每次PQnotifies()调用之前调用PQconsumeInput()

  This fixes cases in which psql would not report receipt of a `NOTIFY` message until after the next command.

  这修复了psql直到下一个命令之后才报告接收到通知消息的情况。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4247db62522fafd1d4c045c5a432f50f2f05c0e0

- Fix pg_dump's `--no-publications` option to also ignore publication tables (Gilles Darold)

  修复pg_dump的-no-publications选项，以忽略发布表

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=08c9917e24683e36dca35201723e47cdc3fa62db

- In pg_dump, exclude identity sequences when their parent table is excluded from the dump (David Rowley)

  在pg_dump中，当其父表被从转储中排除时，排除标识序列

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=b965f2617184032687037547204e1db1c1e1a56c

- Fix possible inconsistency in pg_dump's sorting of dissimilar object names (Jacob Champion)

  修复pg_dump排序不同对象名称时可能出现的不一致

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5b5ed4756c9b3efff787f4921659a9d4d51726e5

- Ensure that pg_restore will schema-qualify the table name when emitting `DISABLE`/`ENABLE TRIGGER` commands (Tom Lane)

  当发出DISABLE/ENABLE触发器命令时，确保pg_restore将模式限定表名

  This avoids failures due to the new policy of running restores with restrictive search path.

  这避免了由于使用限制性搜索路径运行还原的新策略而导致的失败。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=6771c932cf5a8bbb8219461066987ad3b11688ff

- Fix pg_upgrade to handle event triggers in extensions correctly (Haribabu Kommi)

  修复pg_upgrade以正确处理扩展中的事件触发器

  pg_upgrade failed to preserve an event trigger's extension-membership status.

  pg_upgrade无法保存事件触发器的扩展成员状态。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=03838b804905e3fd26ec648c7df1505cf0d8e413

- Fix pg_upgrade's cluster state check to work correctly on a standby server (Bruce Momjian)

  修复pg_upgrade的集群状态检查，以便在备用服务器上正确工作

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=777e6ddf1723306bd2bf8fe6f804863f459b0323

- Enforce type `cube`'s dimension limit in all `contrib/cube` functions (Andrey Borodin)

  在所有 contrib/cube 函数中执行类型多维数据集的维数限制

  Previously, some cube-related functions could construct values that would be rejected by `cube_in()`, leading to dump/reload failures.

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f919c165ebdc2f85e4584e959e002705a5a0a774

- In `contrib/pg_stat_statements`, disallow the `pg_read_all_stats` role from executing `pg_stat_statements_reset()` (Haribabu Kommi)

  在contrib/pg_stat_statements中，禁止pg_read_all_stats角色执行pg_stat_statements_reset()

  `pg_read_all_stats` is only meant to grant permission to read statistics, not to change them, so this grant was incorrect.

  pg_read_all_stats仅用于授予读取统计信息的权限，而不是更改它们，因此该授权是不正确的。

  To cause this change to take effect, run `ALTER EXTENSION pg_stat_statements UPDATE` in each database where `pg_stat_statements` has been installed.

  要使此更改生效，请在安装了pg_stat_statements的每个数据库中运行ALTER EXTENSION pg_stat_statements UPDATE。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=edb9797660541b217d23ae7c02b96b496d34fec4

- In `contrib/postgres_fdw`, don't try to ship a variable-free `ORDER BY` clause to the remote server (Andrew Gierth)

  在contrib/postgres_fdw中，不要尝试将一个无变量ORDER BY子句发送到远程服务器

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=bf2d0462cd735f76bcf6eb8b399723674b2221ef

- Fix `contrib/unaccent`'s `unaccent()` function to use the `unaccent` text search dictionary that is in the same schema as the function (Tom Lane)

  修复了contrib/unaccent()函数，以便使用与函数相同模式下的unaccent文本搜索字典

  Previously it tried to look up the dictionary using the search path, which could fail if the search path has a restrictive value.

  在此之前，它试图使用搜索路径查找字典，如果搜索路径具有限制值，则搜索路径可能会失败。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=a5322ca10fa16bed01e3e3d6c49c0f49c68b5593

- Fix build problems on macOS 10.14 (Mojave) (Tom Lane)

  修正在macOS 10.14平台上的编译问题；

  Adjust configure to add an `-isysroot` switch to `CPPFLAGS`; without this, PL/Perl and PL/Tcl fail to configure or build on macOS 10.14. The specific sysroot used can be overridden at configure time or build time by setting the `PG_SYSROOT` variable in the arguments of configure or make.

  调整配置以将-isysroot开关添加到CPPFLAGS;如果不这样做，PL/Perl和PL/Tcl就无法在macOS 10.14上配置或编译。通过在configure或make的参数中设置PG_SYSROOT变量，可以在配置时或编译时重写使用的特定sysroot。

  It is now recommended that Perl-related extensions write `$(perl_includespec)` rather than `-I$(perl_archlibexp)/CORE` in their compiler flags. The latter continues to work on most platforms, but not recent macOS.

  现在建议与perl相关的扩展在其编译器标记中写入$(perl_includespec)，而不是-I$(perl_archlibexp)/CORE。后者继续在大多数平台上工作，但不是最近的macOS。

  Also, it should no longer be necessary to specify `--with-tclconfig` manually to get PL/Tcl to build on recent macOS releases.

  而且，不再需要手动指定-with-tclconfig来让PL/Tcl在最近的macOS版本上编译。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5e22171310f8d7c82219a6b978440e5144e88683

- Fix MSVC build and regression-test scripts to work on recent Perl versions (Andrew Dunstan)

  修复MSVC编译和回归测试脚本，以便在最新的Perl版本上工作

  Perl no longer includes the current directory in its search path by default; work around that.

  在默认情况下，Perl不再在其搜索路径中包含当前目录。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1df92eeafefac471b8bcb00244452c645e4e14fd

- On Windows, allow the regression tests to be run by an Administrator account (Andrew Dunstan)

  在Windows上，允许由管理员帐户运行回归测试

  To do this safely, pg_regress now gives up any such privileges at startup.

  为了安全起见，pg_regress现在在启动时放弃了任何此类特权

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c468bd5c087051e2edc573118a42d73a8ae3c3a4

- Allow btree comparison functions to return `INT_MIN` (Tom Lane)

  允许btree比较函数返回INT_MIN

  Up to now, we've forbidden datatype-specific comparison functions from returning `INT_MIN`, which allows callers to invert the sort order just by negating the comparison result. However, this was never safe for comparison functions that directly return the result of `memcmp()`, `strcmp()`, etc, as POSIX doesn't place any such restriction on those functions. At least some recent versions of `memcmp()` can return `INT_MIN`, causing incorrect sort ordering. Hence, we've removed this restriction. Callers must now use the `INVERT_COMPARE_RESULT()` macro if they wish to invert the sort order.

  到目前为止，我们已经禁止特定于数据类型的比较函数返回INT_MIN，这允许调用者通过否定比较结果来反转排序顺序。但是，对于直接返回memcmp()、strcmp()等结果的比较函数来说，这是不安全的，因为POSIX对这些函数没有任何这样的限制。至少最近版本的memcmp()可以返回INT_MIN，从而导致不正确的排序顺序。因此，我们去掉了这个限制。如果调用者希望反转排序顺序，那么现在必须使用INVERT_COMPARE_RESULT()宏。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=c87cb5f7a67962f4bdfb897139fff91b7d8e0d90

- Fix recursion hazard in shared-invalidation message processing (Tom Lane)

  修复共享失效消息处理中的递归风险

  This error could, for example, result in failure to access a system catalog or index that had just been processed by `VACUUM FULL`.

  例如，这个错误可能导致无法访问刚刚由VACUUM FULL处理的系统目录或索引。

  This change adds a new result code for `LockAcquire`, which might possibly affect external callers of that function, though only very unusual usage patterns would have an issue with it. The API of `LockAcquireExtended` is also changed.

  他的更改为LockAcquire添加了一个新的结果代码，这可能会影响该函数的外部调用者，不过只有非常不寻常的使用模式才会有问题。LockAcquireExtended的API也改变了。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=f868a8143a98c4172e3faaf415d9352179d5760b

- Save and restore SPI's global variables during `SPI_connect()` and `SPI_finish()` (Chapman Flack, Tom Lane)

  在SPI_connect()和SPI_finish()期间保存和恢复SPI的全局变量

  This prevents possible interference when one SPI-using function calls another.

  这可以防止使用spip的函数调用其他函数时可能出现的干扰。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=361844fe561f6898d90a10382705ad968929a4b2

- Avoid using potentially-under-aligned page buffers (Tom Lane)

  避免使用潜在的未对齐页面缓冲区

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=44cac9346479d4b0cc9195b0267fd13eb4e7442c

- Make `src/port/snprintf.c` follow the C99 standard's definition of `snprintf()`'s result value (Tom Lane)

  src/port/snprintf.c 遵循C99标准snprintf()结果值的定义

  On platforms where this code is used (mostly Windows), its pre-C99 behavior could lead to failure to detect buffer overrun, if the calling code assumed C99 semantics.

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=805889d7d23fbecf5925443deb334aaeb6beaeb0

- When building on i386 with the clang compiler, require `-msse2` to be used (Andres Freund)

  在使用clang编译器构建i386时，需要使用-msse2

  This avoids problems with missed floating point overflow checks.

  这避免了缺少浮点溢出检查的问题。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=bd1463e348fcf3a6e832092ccdeaecda2db9c117

- Fix configure's detection of the result type of `strerror_r()` (Tom Lane)

  修复了configure对strerror_r()结果类型的检测

  The previous coding got the wrong answer when building with icc on Linux (and perhaps in other cases), leading to libpqnot returning useful error messages for system-reported errors.

  以前的代码在Linux上使用icc构建时得到了错误的答案(可能在其他情况下也是如此)，导致libpqnot为系统报告的错误返回有用的错误消息。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=751f532b9766fb5d3c334758abea95b7bb085c5a

- Update time zone data files to tzdata release 2018g for DST law changes in Chile, Fiji, Morocco, and Russia (Volgograd), plus historical corrections for China, Hawaii, Japan, Macau, and North Korea.

  本次更新也包含2018g版本的时区数据，包括智利、斐济、摩洛哥和俄罗斯时区的更新，加上对中国、夏威夷、日本、澳门和北朝鲜等历史数据的更新。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5c2e0ca5f0be780c5fa9c85f4cd4b1106ff747ab

