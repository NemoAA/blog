

## PostgreSQL锁介绍第3部分: 轻量级锁

> 文章翻译自:<https://www.percona.com/blog/2018/10/30/postgresql-locking-part-3-lightweight-locks/>

PostgreSQL轻量级锁，简称`LWLocks`，控制着对内存结构的访问。PostgreSQL使用多进程架构并并且应该只允许一致性的读和写到共享内存结构。`LWLocks`锁有两种类别：共享锁和排他锁。为了简化清理过程会尽可能释放所有获取到的`LWLocks`锁。一些别的数据库经常把类似`LWLocks`的原子锁称做`latches`。因为`LWLocks`锁是一种实现细节，所以应用开发者不应该在这种锁上投入太多的关注。

这是第三篇也是PostgreSQL锁系列的最后一部分，关于保护内部数据库结构的`latches`锁介绍。在这里是之前的部分：[行级锁](https://www.percona.com/blog/2018/10/16/postgresql-locking-part-1-row-locks/)和[表级锁](https://www.percona.com/blog/2018/10/24/postgresql-locking-part-2-heavyweight-locks/) 

## 视图

从PostgreSQL 9.6 开始，可以通过`pg_stat_activity`系统视图来审查`LWLocks`锁的动态。在`CPU`利用率较高的场景下是非常有用的。有些系统设置可以帮助解决特定的轻量级锁争用问题。

在PostgreSQL 9.5  之前，`LWLocks`使用操作系统`spin-locks`锁实现。这是一个瓶颈。在9.5版本使用原子状态变量修复了。

## 可能存在严重的锁争用的地方

- WALInsertLock: 保护预写日志的缓冲区，你可以增加预写日志的缓冲区的数量来得到轻微的改进。顺便提一下，`synchronous_commit=off`会进一步增加锁争用的压力，但这并不是一件坏事。`full_page_writes=off` 会减少锁争用的问题，但通常并不推荐这么做。
- WALWriteLock:当`WAL`记录被刷到硬盘或者在`WAL`段文件切换期间 PostgreSQL进程会累积等待。 `synchronous_commit=off`会关闭刷到硬盘的等待。`full_page_writes=off`可以减少刷到硬盘的数据量。
- LockMgrLock:在一个只读的工作环境下会出现在等待的顶部。它使用latches锁住表不管表的大小。它不是一个单独的锁，至少有16个部分，因此在压力测试时使用多张表和避免生产环境上单个表反模式持有锁上很重要。
- ProcArrayLock: 保护进程数组结构。在PostgreSQL 9.0之前。每个事务在提交前都需要独占此锁。
- CLogControlLock:保护CLogControl结构。如果它出现在`pg_stat_activity `视图的顶部，你应该检查下`$PGDATA/pg_clog`的位置——它应该在文件系统的缓冲区。
- SInvalidReadLock:保护信号数组。读取使用共享锁。`SICleanupQueue`，和其他类型数组更新需要使用排他锁。当共享缓冲区拥堵的时候它出现在`pg_stat_activity`视图的顶部。使用更多的[共享缓冲区](https://www.postgresql.org/docs/current/static/runtime-config-resource.html#GUC-SHARED-BUFFERS)有助于减少锁的争用。
- BufMappingLocks:保护缓冲区域。设置128个缓冲区域（在9.5版本前是16个）处理整个缓冲池。

## 自旋锁（Spinlocks）

最低等级的锁就是`spinlocks`。因此，它使用指定的CPU指令来实现。`PostgreSQL` 尝试在一个循环里去更改原子变量值。如果值被从0改成1——进程获得了`spinlock`.如果不能够立即获得`spinlock`锁，进程会呈指数级的增加它的等待延迟时间。`spinlock`上没有监控并且进程不能够一次释放所有累积的`spinlocks `锁。由于是单独的状态改变，也算是一种排他锁。为了简化`PostgreSQL`到其他`CPU`和`OS`平台的移植过程，`PostgreSQL`使用`OS`的信号量作为它的自旋锁实现。当然，与原生CPU指令端口相比，它的速度要慢得多。

## 总结

- 使用`pg_stat_activity` 视图去找到哪个查询或者`LWLocks`导致了锁等待。
- Use fresh branches of PostgreSQL, as developers have been working on performance improvements and trying to reduce locking contention on hot mutexes.
- 使用最新的 `PostgreSQL`分支，因为开发人员一直在努力提高性能，并努力减少热互斥上的锁争用问题。

## 参考

- <https://www.postgresql.org/docs/10/static/explicit-locking.html>
- <https://nordeus.com/blog/engineering/postgresql-locking-revealed/>
- <https://www.postgresql.org/docs/current/static/sql-createindex.html>
- <https://www.postgresql.org/docs/current/static/runtime-config-locks.html>
- <https://www.postgresql.org/docs/current/static/monitoring-stats.html#PG-STAT-ACTIVITY-VIEW>
- <https://www.slideshare.net/jkshah/understanding-postgresql-lw-locks>
- <https://www.postgresql.org/message-id/flat/559D4729.9080704@postgrespro.ru>
- [PostgreSQL Scalability by Dmitry Vasilyev](https://it-events.com/system/attachments/files/000/001/098/original/PostgreSQL_%D0%BC%D0%B0%D1%81%D1%88%D1%82%D0%B0%D0%B1%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.pdf?1448975472)
- <https://momjian.us/main/writings/pgsql/locking.pdf>
- <https://momjian.us/main/writings/pgsql/mvcc.pdf>
- <https://vladmihalcea.com/how-do-postgresql-advisory-locks-work/>
- <https://blog.2ndquadrant.com/create-index-concurrently/>
