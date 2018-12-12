## **PostgreSQL 问答：使用开源工具构建一个企业级PostgreSQL**

> 本文翻译自[PostgreSQL Q&A: Building an Enterprise-Grade PostgreSQL Setup Using Open Source Tools](https://www.percona.com/blog/2018/10/19/postgresql-building-enterprise-grade-setup-with-open-source/)

大家好，感谢上周三那些出席关于《使用开源工具构建一个企业级PostgreSQL》在线研讨会的人们。您在这儿可以找到那些记录和我们在展示中使用过的幻灯片。

在网络研讨会中，我们有超过四十个问题，但是在可用的时间里仅仅能够解决一小部分，所以大多数仍然没有答案。我们在下面的内容中处理了其余问题，并且为了更好的组织，它已经被分成了不同的类别。谢谢你们把这些问题发送过来！我们已经合并了相关的问题并保留了一些我们的简洁的回答，但是请留给我们一个评论如果您想要看一个特殊问题的进一步处理。

## **1.备份**

**Q：在我们的经验中，pg_basebackup带压缩会慢是因为单线程的gzip压缩。怎样对在线的完全备份的压缩进行加速呢？**

单线程的操作的确是一个`pg_basebackup`的限制，这不仅仅局限于压缩。[pgBackRest](https://pgbackrest.org/) 是一个有趣的替代工具，它支持多线程。

**Q: 通常我们在一个高可用的架构主库上设置数据库备份。是否可能在故障转移之后自动激活备库作为新主（或者其他高可用解决方案）。**

是的。这可以通过将备份系统指向`HAProxy`中的“master-role”端口，或者指向“replica-role”端口来透明地完成;事实上，使用备机作为流复制备份源复制是更为常见的。

**Q: 第三方备份管理器(比如NetBackup)能够对Pg进行普通备份与WAL日志备份吗?**

是的，这通常依赖于供应商的支持度有多优秀。[NetBackup](https://www.veritas.com/support/en_US/doc/129277259-129955710-0/index)支持PostgreSQL，同样，[Zmanda](https://www.zmanda.com/netbackup-postgres-backup.html) 也提到过。

## **2.安全和审计**

**Q: 你知道PostgreSQL的一个TDE解决方案吗?你能从Percona的立场上谈一点谈一点关于Postgres PCI/PII应用程序的静态加密解决方案的问题吗？**

在这一点上，PostgreSQL没有提供一个原生透明的数据加密功能(TDE)，而是 [依赖底层文件系统](https://www.postgresql.org/docs/current/static/encryption-options.html)中的数据静止加密。列级加密能够通过[pgcrypto](https://www.postgresql.org/docs/current/static/pgcrypto.html)模块实现。

另外，其他与PCI承诺相关的PostgreSQL安全特征是：

- [行级别的安全](https://www.postgresql.org/docs/current/static/ddl-rowsecurity.html)。

- 基于主机的认证 ([pg_hba.conf](https://www.postgresql.org/docs/current/static/auth-pg-hba-conf.html))。


- [利用SSL加密线上的数据](https://www.postgresql.org/docs/current/static/ssl-tcp.html)。

**Q: 在Postgres中，怎样避免超级用户账户访问原始数据？我们碰到的公司经常问到这个问题，哪怕是管理账号也不能用任何的方式访问真实的数据。**

保持一个超级用户账号能够接入数据库中任何的对象去进行维护活动是必要的。话虽如此，目前不可能拒绝一个超级用户直接访问表中原始的数据。你能做的对于超级用户接入保护敏感数据的方法就是把他加密存储。如上所述，`pgcrypto`提供了必要的功能去实现它。

另外，避免以超级用户的身份连接数据库是一个最佳做法。扩展模块 [set_user](https://github.com/pgaudit/set_user) 允许没有特权的用户为了在做急需的维护任务的时候把自己提升为超级用户，并且为了更好的审计提供附加的日志层次和控制。而且，作为在线研讨会上的讨论，使用角色和权限实现对用户的隔离是可能的。记住，最好的做法是只授予必要的特权来履行职责，包括应用程序用户。此外，应该对超级用户执行口令认证。

**Q: 在Postgres中，当那些SQL记录中有隐藏数据内容的时候你们如何让审计日志记录DML操作?**

据我们所知，目前没有一种解决方法将查询混淆应用到日志中。绑定参数总是包含在DMLs的审计和日志中，这是设计的。如果您希望避免记录绑定参数，并且希望只跟踪执行的语句，那么可以使用`pg_stat_statements`扩展。注意，虽然`pg_stat_statements`提供了执行语句的总体统计信息，但是它没有跟踪每个DML何时执行。

**Q: 当利用pgbouncer或者pgpool的时候，怎么有效的设置审计日志？**

审计的一个关键部分是在数据库中拥有独立的用户帐户，而不是一个单独的共享帐户。与数据库的连接应该由适当的用户/应用程序帐户进行。在`pgBouncer`中，我们可以建多个池为了每一个用户。来自该池连接的每个操作都将针对相应的用户进行审计。

## **3.高可用和复制**

**Q: PostgreSQL中有类似于Galera高可用集群的东西么？**

Galera复制库提供多主的支持，MySQL基于同步复制的多主拓扑结构（active-active） ，比如[Percona XtraDB Cluster](https://www.percona.com/software/mysql-database/percona-xtradb-cluster)。PostgreSQL也支持同步复制，但是仅限于单主。

然而，PostgreSQL的集群解决方案可以解决类似的业务需求或问题领域，比如可伸缩性和高可用性(HA)。我们在我们的网络研讨会上展示了其中的一个，[Patroni](https://github.com/zalando/patroni)，它主要关注HA和读扩展。对于写扩展，长期以来都有基于分片的解决方案，包括[Citus](https://www.citusdata.com/product)和PostgreSQL 10(现在是11!)，它们为分区领域带来了大量的新特性。最后，基于PostgreSQL的解决方案，如 [Greenplum](https://greenplum.org/)和 [Amazon redshift](https://aws.amazon.com/redshift/) 解决了分析处理的可扩展性问题，而[TimescaleDB](https://www.timescale.com/)则考虑了处理大量时序数据。

**Q: Pgpool能负载均衡，HAProxy比Pgpool好在哪里?**

毫无疑问`Pgpool`特性丰富，除了连接池之外，它还包括负载均衡和其他功能。它可以代替`HAProxy`和`PgBouncer`。但是特性只是选择解决方案的标准之一。在我们的评估中，我们更倾向于轻量级的、更快的、可扩展的解决方案。`HAProxy`以其轻量级连接路由能力而闻名，无需消耗大量服务器资源。

**Q: 怎样把PgBouncer和Pgpool结合起来以便我们能达到事务连接池+负载均衡？你能让我知道在这两个方案中哪个更好吗，PgBouncer 还是Pgpool-II？**

这要逐一分析，视情况而定。如果我们真正需要的只是一个连接池，`PgBouncer`将是我们的首选因为它比`PgPool`更轻量。`PgBouncer`是基于线程的，`Pgpool`像`PostgreSQL`一样是基于进程的，对于每一个入站的连接fork一个主进程是一个稍微昂贵的操作。`PgBouncer`面对这个非常有效。

然而，相对重量级的`Pgpool`带了了许多特性，包括管理PostgreSQL 流复制的能力，并且也有能力解析针对PostgreSQL发出的语句并将其重定向到某些集群节点以实现负载平衡的能力。当你的应用程序不能区分读写需求的时候，`Pgpool`能解析单个SQL语句并且能把他们重定向到主库上，如果他是写的，他将去往主库，或者如果它是读的，他将去往一个副本，就像`Pgpool`设置中配置的一样。我们在在线研讨会中演示的应用能够区分读写，并相应的应用了多连接串，所以我们在`Patroni`上使用了`HAProxy`。

我们已经看到，`Pgpool`用于其负载平衡功能，连接池的任务留给`PgBouncer`，但这不是一个很好的组合。如上所述，作为负载均衡器，`HAProxy`比`Pgpool`更高效。

最后，就像我们在在线研讨会上讨论的，当没有合适的应用层的连接池，或者应用层的连接不能很好的工作去维护连接池，导致频繁的连接和断开，就需要一些像`PgBouncer`一样的外部连接池。

**Q: Postgres会不会嵌入一个连接池进去？或者合并PgBouncer到Postgres？这将使高级身份验证机制（例如LDAP）变得更容易。**

一个很棒的想法。在许多层面，那的确是一个比利用外部的连接池更好的方法，例如：`PgBouncer`。正如我们所见，最近PostgreSQL的贡献者正在讨论相关的话题。一些补丁样品已经提交但是还没有被接受，PostgreSQL社区非常渴望保持代码的轻量和稳定。

**Q: 在PostgreSQL中，更换主库的唯一办法是重启备机吗？?**

备机升级不涉及任何的重启。

在用户的视角里，备机的升级通过`pg_ctl`命令或者建一个触发文件。在这个操作中，副本停止与恢复相关的处理，成为一个读写数据库。

一旦我们有一个新主，其他的备机开始向新主进行复制时。这涉及到改变recover.conf参数和重启，PostgreSQL目前不允许我们通过`SIGHUP`改变参数。

**Q: 外部连接池解决方案(PgBouncer, Pgpool)是否与Java Hibernate ORM兼容?**

像`PgBouncer`和`Pgpool`的外部连接池能和正规的PostgreSQL连接兼容。因此，Hibernate ORM的连接可以将`PgBouncer`视为常规`PostgreSQL`，但运行在不同的端口(或者相同的端口，取决于如何配置)。记住很重要的一点，ORM组件能够与这些连接池很好的互补。例如，c3po是一个著名的Hibernate连接池。如果一个ORM连接池能够很好地调谐避免频繁的连接和断开，像`PgBouncer`和`Pgpool`一样的外部池解决方案将变得多余并且应该被避免。

**Q:关于连接池的问题：我想知道如果一个连接从不关闭，或者说有没有相关设置一段时间后强制关闭连接。**

如果一个连接可以一次次的重复利用（回收），而不是创建一个新的连接，那就不必关掉它。这就是连接池的目的。当一个应用关掉了一个连接，那么连接池实际上是释放应用连接并把它放回连接池中。在下一个连接请求，连接池将会从池中摘一个连接并把它“借”给应用，而不是建立一个新的到数据库的连接。此外，大部分连接池包含一个参数控制在一段时间后释放连接。

**Q: 关于Patroni的问题：我们能在设置中选择不自动故障转移仅仅使用Patroni的手动故障转移/故障恢复?**

是的，`Patroni`允许用户终止他的自动化流程，让他们手动触发故障转移等操作。实现它的实际的程序将做成一个有趣的博客帖子（我们把它放在我们的待办事项里）。

**Q: 我们应该在哪里安装PgBouncer、Patroni和HAproxy：web前端，APP后端，还是数据库服务器？那etcd呢？ **

`Patroni`和`etcd`必须被安装在数据库服务器上。实际上，`etcd`最好能运行在其他服务器上，因为`etcd`作用只是形成分布式一致存储。为了简单起见，`HAProxy`和`PgBouncer`可以安装在应用服务器上，或者可以看情况安装在专用服务器上，尤其当你运行大量这些的时候。话虽如此，`HAProxy`是非常轻量的并且能维护每一台应用服务器而且没有增加的影响。如果你想在专用服务器上安装`PgBouncer`，只要通过使用主备服务器确保避免SPOF（单点故障）。

**Q: 在你的演示设置中，HAproxy如何知道怎样适当地将DML路由到主服务器和从服务器(例如写总是去主服务器，读在副本之间的负载平衡)?**

`HAProxy`不能在中间层解析SQL语句使他们重定向到主或者一个相应的从，这一定是在应用层去做的。为了实现这种功能，你的应用程序需要发读请求到合适的`HAProxy`端口，写请求也一样。在我们的演示设置中，应用程序连接到两个不同的端口，一个读，另一个写（DML）。

**Q: 集群多久轮询一个节点/从节点？很差的网络表现它可以调吗？**

`Patroni`使用一个基础分布式一致机制进行所有心跳检查。例如，可以用于此目的的`etcd`，默认心跳间隔是100ms，但它是可调的。除此之外，在堆栈的每一层，都有可调的像tcp一样的超时。对于连应用复试API的接路由`HAProxy`轮询，也允许进一步控制如何进行检查。话虽如此，但请记住，对于分布式服务来说，性能较差的网络通常是一个糟糕的选择，存在的问题超出了超时检查的范围。

## **4.其他**

**Q: 嗨，Avinash/Nando/Jobin，DDL会带来数据库的阻塞，处理DDL的最好方法是什么?在MySQL中，我们可以使用pt-online-schema-change避免大的复制延迟，在PostgreSQL中有没有方法实现相同的效果而不会阻塞/停机，或者Percona是否有一个与PostgreSQL等价的工具?期待这一切!**

目前，PostgreSQL锁定`ddl`表。一些`ddl`，比如创建触发器和索引，可能不会锁定表上的所有活动。在PostgreSQL中还没有一个像`pt-online-schema-change`这样的工具。然而，一个名为`pg_repack`的扩展，它可以帮助在线重建表。此外，增加关键字“CONCURRENTLY”创建索引语句使系统变得温和并允许在建索引时并发`DMLs`和查询。我们假设你希望重建主键或惟一键后面的索引:一个索引可以独立创建，而且键后面的索引可以用一个可能无缝的临时锁替换。

每个新版本都在这个方面添加了很多新特性。一个扩展锁的极端情况是在表上添加一个有默认值的非空列。在大多数数据库系统中，该操作可以在表上持有写锁，直到完成为止。刚刚发布的PostgreSQL 11使它成为一个简单的操作，而不管表的大小。现在通过简单的元数据更改而不是通过完全的表重建。随着PostgreSQL在处理`ddl`方面越来越好，外部工具的范围正在缩小。此外，它不会导致表重写，因此可以避免过多的I/O和复制延迟等副作用。

**Q: 在PostgreSQL中，哪些操作可以并行化执行?**

这是PostgreSQL在过去几个版本中显著改进的地方。答案取决于你的版本。PostgreSQL 9.6中引进了并行化，在版本10中添加了更多功能。在版本11中，几乎一切都可以使用并行化，包括索引构建。只要是它被正确地用于并行执行，服务器拥有的CPU内核越多，您就越能从最新版本的PostgreSQL中获益。

**Q:PostgreSQL中是否有闪回查询或闪回数据库选项?**

如果闪回查询是应用程序需求，请考虑使用临时表来更好地显现特定时间或时间段的数据。如果应用程序正在处理时序数据(如物联网设备)，那么`TimescaleDB`可能是对你的选择。

数据库的闪回可以通过多种方式实现，或者借助备份工具(和时间点恢复)，或者使用 [延迟备用](https://www.percona.com/blog/2018/06/28/faster-point-in-time-recovery-pitr-postgresql-using-delayed-standby/)副本。

**Q: 关闭pg_repack的问题:我试运行pg_repack，出于某种原因，它一直在运行;我们能简单地取消/中止它的执行吗?**

是的， [pg_repack](http://reorg.github.io/pg_repack/) 的执行可以不受损害地中止。这样做是安全的，因为该工具创建了一个辅助表，并使用它来重新排列数据，在流程结束时将其与原始表交换。如果它的执行在完成之前被中断，那么表的交换就不会发生。但是，由于它是在线工作的，并且不对目标表持有排他锁，这取决于它的大小和在此过程中对目标表所做的更改，因此可能需要相当长的时间才能完成。请研究`pg_repack`提供的并行特性。

**Q: Percona的监控工具是开源的吗?**

[Percona监控和管理(PMM)](https://www.percona.com/software/database-tools/percona-monitoring-and-management) 已经作为一个开源项目发布，其源代码可以在 [GitHub](https://github.com/percona/pmm)上使用。

**Q:很不幸，Master/Slave术语仍然在幻灯片上使用。为什么不使用leader/follower或者orchestrator node/node呢?**

我们同意你的观点，特别是关于“slave”的引用——“replica”是一个更普遍接受的术语(理由很充分)，“standby”[server|replica]在PostgreSQL中更常用。

`Patroni`通常使用“leader”和“followers者”这两个术语。

然而，在PostgreSQL中使用“cluster”(以及“node”)与通常的规范(当我们考虑传统的`beowulf`集群，甚至`Galera`和`Patroni`)形成对比，因为它表示运行在单个PostgreSQL实例/服务器上的一组数据库。
