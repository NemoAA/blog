### E.1.2. Changes

- Ensure proper quoting of transition table names when pg_dump emits `CREATE TRIGGER ... REFERENCING` commands (Tom Lane)

  当pg_dump发出 CREATE TRIGGER ... REFERENCING 命令时确保适当地引用转换表名称

  This oversight could be exploited by an unprivileged user to gain superuser privileges during the next dump/reload or pg_upgrade run. (CVE-2018-16850)

  在下一次转储/重新加载或pg_upgrade运行时，非特权用户可以利用这种疏忽获得超级用户特权

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=350410be459ccda7eeeea35b56b5f2d24391f90c

- Apply the tablespace specified for a partitioned index when creating a child index (Álvaro Herrera)

  在创建子索引时，应用为分区索引指定的表空间

  Previously, child indexes were always created in the default tablespace.

  之前，子索引总是在默认表空间中创建。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=dfa6081419829ef60d6bc02691616337eeb7f988

- Fix NULL handling in parallel hashed multi-batch left joins (Andrew Gierth, Thomas Munro)

  修正在使用`LEFT JOIN`的并行化Hash Join时对`NULL`值的处理方式；

  Outer-relation rows with null values of the hash key were omitted from the join result.

  连接结果中省略了具有散列键null值的外部关系行。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=1ce4a807e25bcd726e34b8d3ba0338e9299f9a87

- Fix incorrect processing of an array-type coercion expression appearing within a `CASE` clause that has a constant test expression (Tom Lane)

  修正在执行`CASE`查询时，表达式转变数组类型的问题；

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=14a158f9bff132f26873c08f9f13946379d42994

- Fix incorrect expansion of tuples lacking recently-added columns (Andrew Dunstan, Amit Langote)

  修正了元组不正确的扩展，缺少最近添加的列

  This is known to lead to crashes in triggers on tables with recently-added columns, and could have other symptoms as well.

  众所周知，这会导致最近添加列的表的触发器崩溃，还可能有其他问题。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=040a1df6149f852c3b8de96d9d13258af8a39e23

- Fix bugs with named or defaulted arguments in `CALL` argument lists (Tom Lane, Pavel Stehule)

  修复调用参数列表中命名参数或默认参数的bug

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=15c7293477a6de03234f58898da7fb29f3ab5b94

- Fix strictness check for strict aggregates with `ORDER BY` columns (Andrew Gierth, Andres Freund)

  修正对严谨聚合函数（指聚合时不接受`NULL`值输入）中含有ORDER BY的列时，会导致对数据扫描的操作；

  The strictness logic incorrectly ignored rows for which the `ORDER BY` value(s) were null.

  忽略按值排序为空的行有严重的逻辑错误。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4c640f4f38d5d68cbe33ddfabbdc56eea8f1e173

- Disable `recheck_on_update` optimization (Tom Lane)

  禁用recheck_on_update优化

  This new-in-v11 feature turns out not to have been ready for prime time. Disable it until something can be done about it.

  这个新的v11特性并没有在黄金时间准备好。禁用它，直到可以做些什么。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5d28c9bd73e29890cccd3f6b188b86f81031f671

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

- Ensure that the server will process already-received `NOTIFY` and `SIGTERM` interrupts before waiting for client input (Jeff Janes, Tom Lane)

  确保服务器将在等待客户端输入之前处理已经收到的通知和SIGTERM中断

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=2ddb9149d14de9a2e7ac9ec6accf3ad442702b24

- Fix memory leak in repeated SP-GiST index scans (Tom Lane)

  修正在使用特定条件下的SP-GiST而造成的内存泄漏；

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=696b0c5fd0a8765fe6dfd075a30be06b448fd615

- Prevent starting the server with `wal_level` set to too low a value to support an existing replication slot (Andres Freund)

  当`wal_level`设置为一个不支持当前已有复制slot的参数时，禁止PostgreSQL的启动；

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=691d79a0793328a45b01348675ba677aa7623bec

- Fix psql, as well as documentation examples, to call `PQconsumeInput()` before each `PQnotifies()` call (Tom Lane)

  修复psql以及文档示例，以便在每次PQnotifies()调用之前调用PQconsumeInput()

  This fixes cases in which psql would not report receipt of a `NOTIFY` message until after the next command.

  这修复了psql直到下一个命令之后才报告接收到通知消息的情况。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=4247db62522fafd1d4c045c5a432f50f2f05c0e0

- Fix pg_verify_checksums's determination of which files to check the checksums of (Michael Paquier)

  修正`pg_verify_checksums`不正确的对文件的结果反馈；

  In some cases it complained about files that are not expected to have checksums.

  在某些情况下，它不希望有校验和的文件。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=d55241af705667d4503638e3f77d3689fd6be31d

- In `contrib/pg_stat_statements`, disallow the `pg_read_all_stats` role from executing `pg_stat_statements_reset()` (Haribabu Kommi)

  在contrib/pg_stat_statements中，禁止pg_read_all_stats角色执行pg_stat_statements_reset()

  `pg_read_all_stats` is only meant to grant permission to read statistics, not to change them, so this grant was incorrect.

  pg_read_all_stats仅用于授予读取统计信息的权限，而不是更改它们，因此该授权是不正确的。

  To cause this change to take effect, run `ALTER EXTENSION pg_stat_statements UPDATE` in each database where `pg_stat_statements` has been installed. (A database freshly created in 11.0 should not need this, but a database upgraded from a previous release probably still contains the old version of `pg_stat_statements`. The `UPDATE` command is harmless if the module was already updated.)

  要使此更改生效，请在安装了pg_stat_statements的每个数据库中运行ALTER EXTENSION pg_stat_statements UPDATE。(11.0中新创建的数据库不需要这样做，但是从以前版本升级的数据库可能仍然包含旧版本的pg_stat_statements。如果模块已经更新，那么UPDATE命令是无害的。)

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=edb9797660541b217d23ae7c02b96b496d34fec4

- Rename red-black tree support functions to use `rbt` prefix not `rb` prefix (Tom Lane)

  重命名红黑树支持函数，使用rbt前缀而不是rb前缀

  This avoids name collisions with Ruby functions, which broke PL/Ruby. It's hoped that there are no other affected extensions.

  这避免了名称与Ruby函数的冲突。希望没有其他受影响的扩展。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=003c68a3b45d0d135b874acfe04cf3fb79a6f172

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

- Update time zone data files to tzdata release 2018g for DST law changes in Chile, Fiji, Morocco, and Russia (Volgograd), plus historical corrections for China, Hawaii, Japan, Macau, and North Korea.

  本次更新也包含2018g版本的时区数据，包括智利、斐济、摩洛哥和俄罗斯时区的更新，加上对中国、夏威夷、日本、澳门和北朝鲜等历史数据的更新。

  https://git.postgresql.org/gitweb/?p=postgresql.git;a=commit;h=5c2e0ca5f0be780c5fa9c85f4cd4b1106ff747ab