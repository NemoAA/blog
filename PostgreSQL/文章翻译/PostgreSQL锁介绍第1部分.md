# PostgreSQL锁介绍第1部分：行级锁

> 本文翻译自[PostgreSQL locking, Part 1: Row Locks](https://www.percona.com/blog/2018/10/16/postgresql-locking-part-1-row-locks/)

理解PostgreSQL锁对于建立可扩展的应用程序和避免停机是非常重要。现代计算机和服务器有许多CPU核心，可以并行执行多个查询。数据库内包含了许多具有一致性的结构，并行查询或者后台进程所做的变动可能会导致数据库损坏，甚至破坏数据。因此，我们需要阻止并发进程的访问，同时更改共享内存的结构和行。一个线程更新结构，而其他线程都在等待(排他锁)，或者多个线程读取结构时，所有的写等待。等待的副作用是锁争用和服务器资源浪费。因此，了解为什么会发生等待的原因以及涉及到哪些锁是很重要的。在本文中，我将回顾PostgreSQL行级别的锁。

在后续文章中，我将研究保护内部数据结构的 [表级锁](https://www.percona.com/blog/2018/10/24/postgresql-locking-part-2-heavyweight-locks/) 和 [latches](https://www.percona.com/blog/2018/10/30/postgresql-locking-part-3-lightweight-locks/) 。

## 1.行级锁–概述

PostgreSQL在不同的级别上有很多锁。应用程序中最重要的锁与[MVCC](https://en.wikipedia.org/wiki/Multiversion_concurrency_control)相关——行级锁。维护任务期间出现的锁(在备份/数据库迁移期间)——表级锁。虽然很少见，在低级别的PostgreSQL锁上的等待发生等待是可能发生的。通常情况下，CPU使用率很高，有许多查询在同时运行，但与并行的查询数量相比，总体服务器性能是下降的。

## **2.示例环境**

接下来，您需要一个PostgreSQL服务器，创建一张包含几个行的单列表：

```
postgres=# CREATE TABLE locktest (c INT);
CREATE TABLE
postgres=# INSERT INTO locktest VALUES (1), (2);
INSERT 0 2
```

## **2.行锁**

场景：两个事务正在更新同一行。

在这种情况下，PostgreSQL使用行级锁。行级锁是与MVCC特性紧密联系的，并使用隐藏的`xmin`和`xmax`字段。`xmin`和`xmax`存储了事务ID。所有需要行级锁的语句都会修改`xmax`字段(甚至是`select  for  update`操作)。修改是在查询并返回结果之后进行的，因此为了查看`xmax`的变化我们需要运行两次`select  for  update`。通常`xmax`字段用于将行标记为过期（要么被某些事务提交删除或者或者被更新）但它也用于行级锁的基础结构。

如果需要更多关于`xmin`和`xmax`隐藏字段和MVCC实现的详细信息，请查看我们的 “[Basic Understanding of Bloat and VACUUM in PostgreSQL](https://www.percona.com/blog/2018/08/06/basic-understanding-bloat-vacuum-postgresql-mvcc/)” 博客帖子。

```
postgres=# BEGIN;
postgres=# SELECT xmin,xmax, txid_current(), c FROM locktest WHERE c=1 FOR UPDATE;
BEGIN
xmin | xmax | txid_current | c 
------+------+--------------+---
  579 |  581 |          583 | 1
(1 row)
postgres=# SELECT xmin,xmax, txid_current(), c FROM locktest WHERE c=1 FOR UPDATE;
xmin | xmax | txid_current | c 
------+------+--------------+---
  579 |  583 |          583 | 1
```

如果一个语句试图修改同一行，它将检查未完成事务的列表。此语句必须一直等待id=`xmax`的事务完成后修改。

没有等待特定行的基础结构，但事务可以等待事务ID。

```
-- second connection

SELECT xmin,xmax,txid_current() FROM locktest WHERE c=1 FOR UPDATE;
```

第二个连接中的`select  for  update`未完成，会等待第一个事务完成。

## 3.PG_LOCK

通过查询`pg_lock`可以看到这样的等待和锁：

```
postgres=# SELECT locktype,transactionid,virtualtransaction,pid,mode,granted,fastpath

postgres-# FROM pg_locks WHERE transactionid=583;

   locktype    | transactionid | virtualtransaction |  pid  |     mode      | granted | fastpath 

---------------+---------------+--------------------+-------+---------------+---------+----------

transactionid |           583 | 4/107              | 31369 | ShareLock     | f       | f

transactionid |           583 | 3/11               | 21144 | ExclusiveLock | t       | f
```

可以看到`locktype`=`transactionid`=583的写事务id。让我们通过`pid`(后台进程id)获取持有锁的后端进程ID：

```
postgres=# SELECT id,pg_backend_pid() FROM pg_stat_get_backend_idset() AS t(id)

postgres-# WHERE pg_stat_get_backend_pid(id) = pg_backend_pid();

id | pg_backend_pid 

----+----------------

  3 |          21144
```

这个后端进程获得了锁(`granted`=t)。每个后端进程都有一个操作系统进程标识符(`PID`)和内部PostgreSQL标识符(backend id)。PostgreSQL可以处理许多事务，但是锁只能在后端进程之间发生，并且每个后端进程执行一个单独事务。内部只需要记录一个虚拟事务标识符：一对后端ID和后端内的序列号。

不管锁住的行数是多少，PostgreSQL在`PG_LOCKS`表中只有一个相关的锁。查询可能会修改数十亿行，但PostgreSQL不会将内存浪费在冗余锁结构上。

在其事务ID上设置排它锁。所有对应等待的事物行级锁服务设置为共享锁。事务id一旦释放锁，锁管理器就会恢复以前所有锁住的后端进程的锁。

事务id的锁释放发生在提交或回滚时。

## 4.PG_STAT_ACTIVITY

获得锁信息的另一种很好的方法是从`pg_stat_activity`表中进行查看：

```
postgres=# SELECT pid,backend_xid,wait_event_type,wait_event,state,query FROM pg_stat_activity WHERE pid IN (31369,21144);

-[ RECORD 1 ]---+---------------------------------------------------------------------------------------------------------------------------

pid             | 21144

backend_xid     | 583

wait_event_type | Client

wait_event      | ClientRead

state           | idle in transaction

query           | SELECT id,pg_backend_pid() FROM pg_stat_get_backend_idset() AS t(id) WHERE pg_stat_get_backend_pid(id) = pg_backend_pid();

-[ RECORD 2 ]---+---------------------------------------------------------------------------------------------------------------------------

pid             | 31369

backend_xid     | 585

wait_event_type | Lock

wait_event      | transactionid

state           | active

query           | SELECT xmin,xmax,txid_current() FROM locktest WHERE c=1 FOR UPDATE;
```

## 5.源代码

让我们用gdb和[PT-PMP](https://www.percona.com/doc/percona-toolkit/LATEST/pt-pmp.html)工具查看：

```
# pt-pmp -p 31369

Sat Jul 28 10:10:25 UTC 2018

30 ../sysdeps/unix/sysv/linux/epoll_wait.c: No such file or directory.

      1 epoll_wait,WaitEventSetWaitBlock,WaitEventSetWait,WaitLatchOrSocket,WaitLatch,ProcSleep,WaitOnLock,LockAcquireExtended,LockAcquire,XactLockTableWait,heap_lock_tuple,ExecLockRows,ExecProcNode,ExecutePlan,standard_ExecutorRun,PortalRunSelect,PortalRun,exec_simple_query,PostgresMain,BackendRun,BackendStartup,ServerLoop,PostmasterMain,main
```

`WaitOnLock`函数造成等待。函数位于`lock.c`文件(Postgres主要锁机制文件)中。

锁表是共享内存哈希表。大多数情况下storage/lmgr/proc.c中的锁上会在冲突的进程中休眠。在大多数情况下，这段代码应该通过`lmgr.c`或其他锁管理模块调用，而不是直接调用。

接下来，在`pg_stat_activity`中被称为“lock”的锁也称为重量级锁，由锁管理器控制。重量级锁也用于许多高级操作。

顺便提一下，在这里可以找到完整的描述：https://www.postgresql.org/docs/current/static/explicit-locking.html。

## 6.总结

- 避免长事务修改频繁修改太多行。

- 下一个，不要在具有MVCC特性的数据库中使用热点(多个客户端连接并行更新的单行或多行)。这种工作负载更适合于内存中的数据库，通常可以与主要业务逻辑分离。
