# POSTGRESQL中的HOT_STANDBY_FEEDBACK真正做了什么

> 本文翻译自：<https://www.cybertec-postgresql.com/en/what-hot_standby_feedback-in-postgresql-really-does/>

很多使用PostgreSQL流复制的用户可能想知道在postgresql.conf配置文件中参数`hot_standby_feedback`的作用是什么。因为支持客户不断的咨询这个问题，所以共享这块知识可能对广大的PostgreSQL用户有用。

## 1. VACUUM作用

VACUUM是PostgreSQL的一个基本命令，它的目标是清理不再被需要的`dead tuples`。其思路是当新数据进入表后可以重用这部分空间。重要的是：`VACUUM`的目的是重用表的空间——但是这并不意味着表的大小会减少。同样请记住：`VACUUM`只会清理PostgreSQL服务上运行事务不再需要的`dead tuples`。

参考下图：

![](https://www.cybertec-postgresql.com/wp-content/uploads/2018/08/vacuum_cleanup-01-939x1024.jpg)

`hot_standby_feedback`和`VACUUM`在PostgreSQL中如何协同工作？

从上图大家可以看到有两个连接。左边的第一个连接运行一条很长的SELECT语句。现在请记住：SQL语句基本上会“冻结”其数据视图。在SQL语句中，世界不会“改变”——查询将始终看到相同的数据集，而不会去考虑并发更改。这一点很重要。

让我们看一下第二个事务。它将删除一些数据并提交。问题是：PostgreSQL什么时候才能真正从磁盘上删除这一行？DELETE它本身并不会真正从磁盘上删除数据，因为仍然可能会ROLLBACK而不是COMMIT。换句话说，数据不能被DELETE删除。PostgreSQL只能在当前事务中将这些数据标记为`dead tuple`。正如你所见，其他事务仍然可以看到这些删除的数据。

然而，即使COMMIT也无权真正地清理该行。记住：左侧的事务仍然可以看到`dead row`，因为SELECT语句在运行时不会更改其快照。COMMIT太早了，因此不能清除这行。

当VACUUM进入此场景时。 VACUUM用于清理其他任何事务都无法看到的这些行。在我的图片中有两个VACUUM操作正在进行。第一个还不能清除dead行，因为左侧的事务仍然可以看到它。

但是，第二个VACUUM可以清除此行，因为此时它不再被读取事务使用。

VACUUM可以清理那些对任何事务都不可见的行在单个服务上这种情况非常明晰的。 

## 2. PostgreSQL中的复制冲突

主备之间交互的过程是怎样的？过程有点复杂，因为主节点需要知道某个备节点上发生的一些奇怪的事务。

以下为一个典型的过程：

![PostgreSQL VACUUM and table bloat](https://www.cybertec-postgresql.com/wp-content/uploads/2018/08/hot_standby_feedback-01-939x1024.jpg)在PostgreSQL中避免表膨胀

以在运行了一段时间的复制场景中的SELECT语句为例。假设主节点上发生了改变（例如UPDATE，DELETE）。不会发生任何问题。注意：DELETE不会真正删除行——它只是被标记为已经dead，但同时对其他允许访问“dead”行的事务还可见。致命的情况发生在主节点上的VACUUM操作真正删除磁盘数据的时候。VACUUM被允许这么做是因为它无法知道备节点还需要这些行。结果就会发生复制冲突。默认情况下，复制冲突会在30秒钟后被解决：

```
ERROR: canceling statement due to conflict with recovery``Detail: User query might have needed to see row versions that must be removed`
```

如果你看到过这样的消息——这就是我们在这里将讨论的问题。

## hot_standby_feedback能避免这类复制冲突

要解决这类问题，我们可以让备节点定期告知主节点在备节点上正在运行的最老事务。如果主节点知道了备节点上最老的事务，它可以让VACUUM保留这些行，直到备节点上的事务完成。

这就是 [hot_standby_feedback](https://www.postgresql.org/docs/11/static/runtime-config-replication.html) 的功能。它从备节点上的视角上避免了行被过早删除。实现方法是将备节点上最老的事务编号通知到主节点，因而[VACUUM](https://www.postgresql.org/docs/current/static/sql-vacuum.html)可以延迟清理这些行。

好处很明显：hot_standby_feedback会显著降低复制冲突的数量。不过也存在缺点：记住，VACUUM 将推迟它的清理工作。如果备节点永不完成一个查询，它将导致主节点上的表膨胀，这对于长时间运行的服务非常有害。