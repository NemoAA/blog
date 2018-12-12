# PostgreSQL锁介绍第2部分：重量级锁

本文翻译自[PostgreSQL locking, part 2: heavyweight locks](https://www.percona.com/blog/2018/10/24/postgresql-locking-part-2-heavyweight-locks/)

对应用程序开发者和DBA来说PostgreSQL可见性锁在大部分场景下都与重量级锁相关。数据库复杂的锁操作需要使用系统视图来进行完全检测，因此应该清楚哪些对象被特定的数据库后端进程给锁定了。锁的别称是‘瓶颈’。为了使数据库操作并行，我们应该将单个’瓶颈‘分割成多个特定操作的任务。

这是发表的三篇与表锁相关的博客中的第二部分。前一篇博客是关于行锁，随后的下一篇博客会回顾保护内部数据库结构的latches。

## 1.示例环境

创建一个包含两行的单列表

```sql
CREATE TABLE locktest (c INT);
INSERT INTO locktest VALUES (1), (2);
```

## 2.辅助视图

为了检查这些不同类型的锁，我们需要创建一个辅助视图。

```sql
CREATE VIEW lockview AS SELECT pid, virtualtransaction AS vxid, locktype AS lock_type,
mode AS lock_mode, granted,
CASE
WHEN virtualxid IS NOT NULL AND transactionid IS NOT NULL
THEN virtualxid || ' ' || transactionid
WHEN virtualxid::text IS NOT NULL
THEN virtualxid
ELSE transactionid::text                                                                                                                                                                                           END AS xid_lock, relname,
page, tuple, classid, objid, objsubid
FROM pg_locks LEFT OUTER JOIN pg_class ON (pg_locks.relation = pg_class.oid)
WHERE -- do not show our view’s locks
pid != pg_backend_pid() AND
-- no need to show self-vxid locks                                                                                                                                                                                 virtualtransaction IS DISTINCT FROM virtualxid
-- granted is ordered earlier
ORDER BY 1, 2, 5 DESC, 6, 3, 4, 7;
```

## 3.行级共享锁

许多应用程序使用[read-modify-write](https://en.wikipedia.org/wiki/Read-modify-write) 范例。例如，应用程序从表里取到一个单独的对象属性，修改它，然后把更改回写到数据库。在多用户环境下，不同的用户能够在一个事务执行的过程中去修改同一行记录，此时我们使用简单查询会得到不一致的数据。为了响应用户需求，几乎所有的SQL数据库都有`select ... for share` 锁，这个特性能阻止应用端去修改数据直到持有锁用户的事务提交或者回滚。

例如：

1. 在一个账户表里有存储多个银行账户，在银行客户端表里存储总资产的用户
2. 为了更新总资产，我们需要阻止所有与这个特定银行客户端相关的行的修改
3. 使用单独的更新语句去计算总资产然后从账户表里查询它会更好。如果更新需要外部数据，或者一些用户操作，那么需要多条语句。

```sql
START TRANSACTION;
SELECT * FROM accounts WHERE client_id = 55 FOR SHARE;
SELECT * FROM bank_clients WHERE client_id=55 FOR UPDATE;
UPDATE bank_clients SET total_amount=38984.33, client_status='gold' WHERE client_id=55;
COMMIT;
```

`select for share`语句在`locktest`表上创建了行级共享锁.

这里使用了一条SQL语句创建了同样的锁

```sql
BEGIN;
LOCK TABLE locktest IN ROW SHARE MODE;
```

不管查询会锁定多少行记录，它都需要一个重量级的行级共享锁。

下面的例子展示了一个未完成的事务。先开启一个未提交的事务，然后在新的数据库连接上查询`lockview`

```sql
BEGIN;
SELECT * FROM locktest FOR SHARE;
-- In second connection:
postgres=# SELECT pid,vxid,lock_type,lock_mode,granted,xid_lock,relname FROM lockview;
  pid  | vxid |   lock_type   |   lock_mode   | granted | xid_lock | relname
-------+------+---------------+---------------+---------+----------+----------
 21144 | 3/13 | transactionid | ExclusiveLock | t       | 586      |
 21144 | 3/13 | relation      | RowShareLock  | t       |          | locktest
```

## 4.行级排他锁

对行进行修改的实际查询也需要在每张表上添加一个重量级锁。

接下来的例子使用了一个`delete`查询，但即使是`update`也会产生同样的效果。

所有去修改表数据的命令都会去申请一个行级排他锁。

```sql
BEGIN;
DELETE FROM locktest;
-- second connection
postgres=# SELECT pid,vxid,lock_type,lock_mode,granted,xid_lock,relname FROM lockview;
  pid  | vxid |   lock_type   |    lock_mode     | granted | xid_lock | relname
-------+------+---------------+------------------+---------+----------+----------
 10997 | 3/6  | transactionid | ExclusiveLock    | t       | 589      |
 10997 | 3/6  | relation      | RowExclusiveLock | t       |          | locktest
```

这种新锁和前面例子里提到的行级共享锁`for share`是不兼容的，`select * from locktest for share`语句会等待`delete`事务的结束或者异常退出。

```sql
postgres=# SELECT pid,vxid,lock_type,lock_mode,granted,xid_lock,relname,page,tuple FROM lockview;
  pid  | vxid |   lock_type   |    lock_mode     | granted | xid_lock | relname  | page | tuple
-------+------+---------------+------------------+---------+----------+----------+------+-------
 10997 | 3/6  | transactionid | ExclusiveLock    | t       | 589      |          |      |
 10997 | 3/6  | relation      | RowExclusiveLock | t       |          | locktest |      |
 11495 | 5/9  | relation      | RowShareLock     | t       |          | locktest |      |
 11495 | 5/9  | tuple         | RowShareLock     | t       |          | locktest |    0 |     1
 11495 | 5/9  | transactionid | ShareLock        | f       | 589      |          |      |
```

修改表数据的查询同时还锁住了所有的索引，即使这个索引不包含被修改的字段。

```sql
-- preparation
CREATE INDEX c_idx2 ON locktest (c);
ALTER TABLE locktest ADD COLUMN c2 INT;
CREATE INDEX c2_idx ON locktest(c2);
-- unfinished example transaction
BEGIN;
UPDATE locktest SET c=3 WHERE c=1;
-- second connection
postgres=# SELECT * FROM lockview;
 pid  |  vxid  | lock_type  |    lock_mode     | granted | xid_lock | relname  | page | tuple | classid | objid | objsubid
------+--------+------------+------------------+---------+----------+----------+------+-------+---------+-------+----------
 3998 | 3/7844 | virtualxid | ExclusiveLock    | t       | 3/7844   |          |      |       |         |       |
 3998 | 3/7844 | relation   | RowExclusiveLock | t       |          | c2_idx   |      |       |         |       |
 3998 | 3/7844 | relation   | RowExclusiveLock | t       |          | c_idx    |      |       |         |       |
 3998 | 3/7844 | relation   | RowExclusiveLock | t       |          | c_idx2   |      |       |         |       |
 3998 | 3/7844 | relation   | RowExclusiveLock | t       |          | locktest |      |       |         |       |
```

## 5.共享锁

`create index`的`non-concurrent`版本使用共享锁阻止了表的一些更新操作，例如`drop table`或者`insert`或者`delete`

```sql
BEGIN;
CREATE INDEX c_idx ON locktest (c);
-- second connection
postgres=# SELECT * FROM lockview;
 pid  |  vxid  |   lock_type   |      lock_mode      | granted | xid_lock | relname  | page | tuple | classid | objid | objsubid
------+--------+---------------+---------------------+---------+----------+----------+------+-------+---------+-------+----------
 3998 | 3/7835 | virtualxid    | ExclusiveLock       | t       | 3/7835   |          |      |       |         |       |
 3998 | 3/7835 | transactionid | ExclusiveLock       | t       | 564      |          |      |       |         |       |
 3998 | 3/7835 | relation      | AccessExclusiveLock | t       |          |          |      |       |         |       |
 3998 | 3/7835 | relation      | ShareLock           | t       |          | locktest |      |       |         |       |
```

你可以并行的执行多条`create index`查询除非索引名字重复，在`pg_class `表的行锁上(`transactionid` 类型的共享锁)发生锁等待。

注意有一个`relation`类型的访问排他锁，但它并不是一个表级别的锁。

## 6.共享更新排他锁

下列数据库维护操作需要持有共享更新排他锁：

​	●	ANALYZE table

​	●	VACUUM (without full) runs

​	●	CREATE INDEX CONCURRENTLY

`ANALYZE tablename`语句更新表的统计信息，只有当统计信息是实时的查询计划器和查询优化器才能提供最优的执行计划给查询执行器。

```sql
BEGIN;
ANALYZE locktest;
-- in second connection
postgres=# SELECT pid,vxid,lock_type,lock_mode,granted,xid_lock,relname FROM lockview;
  pid  | vxid |   lock_type   |        lock_mode         | granted | xid_lock | relname
-------+------+---------------+--------------------------+---------+----------+----------
 10997 | 3/7  | transactionid | ExclusiveLock            | t       | 591      |
 10997 | 3/7  | relation      | ShareUpdateExclusiveLock | t       |          | locktest
```

	行级排他锁和共享更新排他锁是没有冲突的，在执行`ANALYZE`操作期间`UPDATE/DELETE/INSERT` 操作仍然可以修改行记录。

	`VACUUM 和 CREATE INDEX CONCURRENTLY`在一个事务外可以被执行。为了在`lockview ` 视图看这些语句的影响，首先执行一个冲突的事务，例如，在一个事务中运行`ANALYZE`,或者对一个大表执行`VACUUM` .

	`CREATE INDEX CONCURRENTLY`锁操作可能有点令人困惑。共享更新排他锁与被用于`DELETES,INSERT和UPDATES` 操作的行级排他锁不会冲突。遗憾的是，`CREATE INDEX CONCURRENTLY`操作会等待直到活动的事务结束由于两次全表扫描。

	“在并发索引构建中，索引实际上在一个事务中被录入到系统目录， 然后在两个或更多事务中发生两次表扫描。在每一次表扫描之前， 索引构建必须等待已经修改了表的现有事务终止。”

[[PostgreSQL Documentation](https://www.postgresql.org/docs/9.1/static/sql-createindex.html)]

## 7.访问排他锁

此锁与被用于以下操作的其他锁冲突

	●	CREATE RULE

	●	DROP TABLE

	●	DROP INDEX

	●	TRUNCATE

	●	VACUUM FULL

	●	LOCK TABLE(default mode)

	●	CLUSTER

	●	REINDEX

	●	REFRESH MATERIALIZED VIEW(without CONCURRENTLY)

```sql
BEGIN;
CREATE RULE r_locktest AS ON INSERT TO locktest DO INSTEAD NOTHING;
-- second connection
postgres=# select pid,vxid,lock_type,lock_mode,granted,xid_lock,relname from lockview;
  pid  | vxid |   lock_type   |      lock_mode      | granted | xid_lock | relname
-------+------+---------------+---------------------+---------+----------+----------
 10997 | 3/19 | transactionid | ExclusiveLock       | t       | 596      |
 10997 | 3/19 | relation      | AccessExclusiveLock | t       |          | locktest
```

更重要的是，删除索引时需要持有表和索引上的访问排他锁:

```sql
BEGIN;
DROP INDEX c_idx;
-- second connection
postgres=# SELECT * FROM lockview;
 pid  |  vxid  |   lock_type   |      lock_mode      | granted | xid_lock | relname  | page | tuple | classid | objid | objsubid
------+--------+---------------+---------------------+---------+----------+----------+------+-------+---------+-------+----------
 3998 | 3/7839 | virtualxid    | ExclusiveLock       | t       | 3/7839   |          |      |       |         |       |
 3998 | 3/7839 | transactionid | ExclusiveLock       | t       | 569      |          |      |       |         |       |
 3998 | 3/7839 | relation      | AccessExclusiveLock | t       |          | c_idx    |      |       |         |       |
 3998 | 3/7839 | relation      | AccessExclusiveLock | t       |          | locktest |      |       |         |       |
```

注意：这是最危险的一种锁，避免在生产中运行需要访问排他锁的查询，或者至少将应用至于维护模式。

## 8.排他锁

	同时， SQL命令不使用排他锁，除了 通用的`LOCK TABLE` 语句。这种锁会阻止所有的请求除了不需要加锁的 `SELECT`操作( 即没有`FOR SHARE/UPDATE`)  

	

```sql
BEGIN;
LOCK TABLE locktest IN EXCLUSIVE MODE;
-- second connection
postgres=# SELECT pid,vxid,lock_type,lock_mode,granted,xid_lock,relname FROM lockview;
  pid  | vxid | lock_type |   lock_mode   | granted | xid_lock | relname
-------+------+-----------+---------------+---------+----------+----------
 10997 | 3/21 | relation  | ExclusiveLock | t       |          | locktest
```

## 9.保存点

	保存点产生一个额外的具有新xid值的`transactionid` 类型的排他锁。

```sql
BEGIN;
SELECT * FROM locktest FOR SHARE;
SAVEPOINT s1;
SELECT * FROM locktest FOR UPDATE;
-- second connection
postgres=# SELECT pid,vxid,lock_type,lock_mode,granted,xid_lock,relname FROM lockview;
  pid  | vxid |   lock_type   |    lock_mode    | granted | xid_lock | relname
-------+------+---------------+-----------------+---------+----------+----------
 10997 | 3/37 | transactionid | ExclusiveLock   | t       | 602      |
 10997 | 3/37 | transactionid | ExclusiveLock   | t       | 603      |
 10997 | 3/37 | relation      | AccessShareLock | t       |          | c_idx
 10997 | 3/37 | relation      | RowShareLock    | t       |          | locktest
```

## 10.咨询锁

有时候应用开发人员会需要在进程间同步通信。在这类系统上，应用会频繁的创建和删除锁，基于行锁的系统实现往往会导致表膨胀的问题。

有许多和咨询锁相关的功能：

●	每个会话或者每个事务

●	阻塞锁或者非阻塞锁

●	排他或者共享

●	64位或者两个32位整型资源标识符

	假设我们有几个定时作业，应用程序应该阻止同一个脚本的同时运行。接下来，每个脚本可以检查PostgreSQL中用于特定的整型作业标识符的锁是否可用。

	

``` sql
postgres=# SELECT pg_try_advisory_lock(10);
 pg_try_advisory_lock
----------------------
 t
-- second connection
postgres=# SELECT * FROM lockview;
 pid  | vxid | lock_type |   lock_mode   | granted | xid_lock | relname | page | tuple | classid | objid | objsubid
------+------+-----------+---------------+---------+----------+---------+------+-------+---------+-------+----------
 3998 | 3/0  | advisory  | ExclusiveLock | t       |          |         |      |       |       0 |    10 |        1
-- other connections
SELECT pg_try_advisory_lock(10);
 pg_try_advisory_lock
----------------------
 f
```

咨询锁类型的查询产生了排他锁。

## 11.死锁

当查询永不结束的时候，具有多种类型锁的系统往往会出现死锁的场景。解决这类问题的唯一方法是杀掉阻塞的查询语句。更重要的是，在`PostgreSQL`中死锁检测是一个开销很大的操作。死锁的检查只会发生在一个事务被阻塞了`deadlock_timeout`微秒后-默认是1秒钟后。

这里是一个由两个不同的连接A和B引起死锁场景的例子：

任何的死锁都始于锁阻塞。

```sql
A: BEGIN; SELECT c FROM locktest WHERE c=1 FOR UPDATE;
B: BEGIN; SELECT c FROM locktest WHERE c=2 FOR UPDATE; SELECT c FROM locktest WHERE c=1 FOR UPDATE;
```

识别死锁不只靠你自己，因为`pg_stat_activity`系统视图可以帮助你找到导致锁等待的语句和事务。

```sql
postgres=# SELECT pg_stat_activity.pid AS pid,
query, wait_event, vxid, lock_type,
lock_mode, granted, xid_lock
FROM lockview JOIN pg_stat_activity ON (lockview.pid = pg_stat_activity.pid);
  pid  |          query             |  wait_event   | vxid |   lock_type   |      lock_mode      | granted | xid_lock
-------+----------------------------+---------------+------+---------------+---------------------+---------+----------
 10997 | SELECT ... c=1 FOR UPDATE; | ClientRead    | 3/43 | transactionid | ExclusiveLock       | t       | 605
 10997 | SELECT ... c=1 FOR UPDATE; | ClientRead    | 3/43 | advisory      | ExclusiveLock       | t       |
 10997 | SELECT ... c=1 FOR UPDATE; | ClientRead    | 3/43 | relation      | AccessShareLock     | t       |
 10997 | SELECT ... c=1 FOR UPDATE; | ClientRead    | 3/43 | relation      | RowShareLock        | t       |
 11495 | SELECT ... c=1 FOR UPDATE; | transactionid | 5/29 | transactionid | ExclusiveLock       | t       | 606
 11495 | SELECT ... c=1 FOR UPDATE; | transactionid | 5/29 | advisory      | ExclusiveLock       | t       |
 11495 | SELECT ... c=1 FOR UPDATE; | transactionid | 5/29 | relation      | AccessShareLock     | t       |
 11495 | SELECT ... c=1 FOR UPDATE; | transactionid | 5/29 | relation      | RowShareLock        | t       |
 11495 | SELECT ... c=1 FOR UPDATE; | transactionid | 5/29 | tuple         | AccessExclusiveLock | t       |
 11495 | SELECT ... c=1 FOR UPDATE; | transactionid | 5/29 | transactionid | ShareLock           | f       | 605
```

`SELECT FOR UPDATE on c=2` 语句导致死锁：

```sql
SELECT c FROM locktest WHERE c=2 FOR UPDATE;
```

在此之后，`PostgreSQL`   在数据库日志中报出：

```sql
2018-08-02 08:46:07.793 UTC [10997] ERROR:  deadlock detected
2018-08-02 08:46:07.793 UTC [10997] DETAIL:  Process 10997 waits for ShareLock on transaction 606; blocked by process 11495.
Process 11495 waits for ShareLock on transaction 605; blocked by process 10997.
Process 10997: select c from locktest where c=2 for update;
Process 11495: select c from locktest where c=1 for update;
2018-08-02 08:46:07.793 UTC [10997] HINT:  See server log for query details.
2018-08-02 08:46:07.793 UTC [10997] CONTEXT:  while locking tuple (0,3) in relation "locktest"
2018-08-02 08:46:07.793 UTC [10997] STATEMENT:  SELECT c FROM locktest WHERE c=2 FOR UPDATE;
ERROR:  deadlock detected
DETAIL:  Process 10997 waits for ShareLock on transaction 606; blocked by process 11495.
Process 11495 waits for ShareLock on transaction 605; blocked by process 10997.
HINT:  See server log for query details.
CONTEXT:  while locking tuple (0,3) in relation "locktest"
```

正如你所见，数据库服务端自动的中止了一个阻塞的事务。

## 12.多事务死锁

正常情况下产生死锁仅仅只需要有两个事务。但是，在复杂的场景下，一个应用可能产生形成了依赖环的多事务死锁。

第一步：

A：锁住第一行，B：锁住第二行 C：锁住第三行

第二步：

A：试图拿到第三行 B：试图拿到第一行 C：试图拿到第二行

## 总结

●	不要在长事务中执行DDL语句

●	尽量避免在高负载、频繁更新的表上执行DDL 操作

●	`CLUSTER`命令需要持有排他锁来访问表和表上的所有索引。

●	监控postgresql数据库日志中死锁相关的信息。

