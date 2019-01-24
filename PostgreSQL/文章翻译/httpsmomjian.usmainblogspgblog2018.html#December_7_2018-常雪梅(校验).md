## ![img](https://momjian.us/main/img/title/pgsql.png) Postgres Blog

> 文章翻译自https://momjian.us/main/blogs/pgblog/2018.html#December_7_2018 

这个博客是关于我在Postgres开源数据库上的工作的，它发表在Planet PostgreSQL上。PgLife允许监控所有Postgres社区活动。 



------

### [![Performance](https://momjian.us/main/img/pgblog/performance.png) Windows 和 Shared Buffers](https://momjian.us/main/blogs/pgblog/2018.html#December_17_2018)

*Monday, December 17, 2018*

一个在 Postgres 10中可能被忽略了的变化是删除了Windows上较小的shared_buffers的建议。本邮件讨论了它的删除。因此，如果您一直在最小化Windows上shared_buffers的大小，那么现在可以停止了。 



------

### [![Performance](https://momjian.us/main/img/pgblog/performance.png) 微优化](https://momjian.us/main/blogs/pgblog/2018.html#December_14_2018)

*Friday, December 14, 2018*

这个邮件列表讨论了添加只影响一小部分查询的优化改进的权衡，即微优化。关键是我们不知道检查这些优化所需要的时间是否值得。对于短时间运行的查询，它可能不必要，但是对于长时间运行的查询，它可能需要。问题是直到优化阶段结束时，我们才知道查询的最终成本——这使得我们无法决定在优化期间检查微优化是否值得。 

在邮件讨论中，认为优化X = X子句对所有查询都有效，所以被应用。转换或查询以使用union的优化仍在考虑之中。最近讨论了在优化开始之前估算成本的方法。 



------

### [![Performance](https://momjian.us/main/img/pgblog/performance.png) 优化器提示](https://momjian.us/main/blogs/pgblog/2018.html#December_12_2018)

*Wednesday, December 12, 2018*

你可能知道Postgres将优化器提示列为我们不希望实现的特性。我过去曾讨论过这个问题。 

这个来自Tatsuro Yamada的演示更详细地介绍了优化器提示的利弊。从幻灯片29开始，Yamada-san解释了使用优化提示的首要原因——作为对低效查询计划的短期修复。他使用pg_hint_plan(由ntt生成)修复用例中的低效计划。然后，他继续考虑针对低效计划的可能的非暗示解决方案，例如记录在执行过程中发现的数据分布，以便在以后的查询优化中使用。 

我最感兴趣的是他复制了关于Postgres wiki上的优化器提示讨论，包括他对pg_hint_plan如何符合该标准的分析。当然，优化器提示在某些环境中是有用的，而且Yamada-san似乎已经找到了一个。社区不打算支持提示的原因是考虑到优化器提示可能会给用户带来比它们解决的问题更多的问题。虽然Postgres有一些粗糙的手动优化器控件，但是如果Postgres能够提出更多的解决方案，进一步减少出现明显低效的计划，那当然是件好事。 



------

### [![Performance](https://momjian.us/main/img/pgblog/performance.png) 分配 *Work_mem*](https://momjian.us/main/blogs/pgblog/2018.html#December_10_2018)

*Monday, December 10, 2018*

我们已经讨论过分配shared buffers，work mem还有其他内核缓存的复杂性。然而，即使可以对他们进行优化配置，work_mem(及其相关的设置maintenance_work_mem)也会针对每个查询进行配置，如果多个查询节点需要的话，还可以对它们进行多次分配。因此，即使知道为整个集群分配的最优work_mem数量，您仍然需要知道如何在会话中分配它。 

这个详细的电子邮件列表探索了一些可能的方法来简化这个问题，但得出的答案很少。如前所述，这是一个困难的问题，要做好它将需要大量的工作。甚至DB2对该问题的解决方案也受到了批评，尽管它是我们解决该问题的最初方法。使用额外的并行特性，配置work_mem对于用户来说变得更加复杂，更不用说分配并行进程本身的复杂性了。 

最终必须解决这个问题，分开做是不会有结果的。它将需要一个全新的子系统，可能具有其他Postgres模块所没有的动态特性。 



------

### [![Performance](https://momjian.us/main/img/pgblog/performance.png) 内存资源三元组](https://momjian.us/main/blogs/pgblog/2018.html#December_7_2018)

*Friday, December 7, 2018*

有三种资源会影响查询性能:cpu、内存和存储。为优化查询性能分配cpu和存储非常简单，至少是线性的。对于cpu，对于每个查询，必须决定为并行查询执行分配的最优cpu数量。当然，只有某些查询可以从并行特性中获益，并且cpu更改的最佳数量取决于正在执行的其他查询。它并不简单，但它是线性的。 

对于存储，它更像是一个二进制决策——表或索引应该存储在快速介质(ssd)或慢介质(磁盘)上，特别是快速随机访问。(一些nas服务器甚至有更细粒度的分层存储。)需要分析来决定每个表或索引的最佳存储类型，但是Postgres统计视图可以帮助确定哪些对象将受益。 

不幸的是，对于内存来说，资源分配更加复杂。它不是一个线性或二元问题，而是一个多维问题——我来解释一下。如上所述，对于cpu，您必须决定要使用多少cpu，对于存储需要使用什么类型。对于内存，您必须决定在数据库服务器启动时为shared_buffers分配多少内存，然后决定为每个查询分配多少内存，以便通过work_mem进行排序和散列。notallocate内存被用作内核缓存，Postgres依赖于这些内存来获得一致的性能(因为所有的读写都要经过该缓存)。因此，为了优化内存分配，您必须选择最佳的大小:

1. shared buffers(服务器启动时的固定大小)
2. work_mem(根据工作负载对每个查询进行优化)
3. kernel buffers(剩余部分)

你必须选择一个1、一旦服务器启动后不能改变；2,可以改变,但是你需要了解其他会话的内存分配和未使用的内存优化；3不管尚未分配的前两项。 

可以看到，这是一个几乎不可能的问题，这也是为什么管理员通常选择合理的值、监视资源耗尽情况并调整特定问题查询的原因。对于第一条，共享缓冲区的推荐默认值是内存的25%。您可以选择更大的内存，更大的值允许您在内存中保留更多的工作集，并且不需要大的内核缓存来吸收许多写操作。对于第二条，您可以监视log_temp_files，并在看到使用临时存储进行排序或散列的查询时增加它。一个创造性的想法是使用alter system根据空闲内核缓冲区的数量自动增加或减少work_mem。(我对autovacuum提出了类似的解决方案。)最后，您可能应该监控空闲内核缓冲区，以确保第一条和第二条没有分配太多内存。 

好消息是，与许多其他关系系统相比，Postgres对非最优内存分配的敏感度较低。这是因为小于最优内存分配意味着有更多的内核缓冲区，而更多的内核缓冲区有助于减少小于最优共享缓冲区或work_mem的影响。相比之下，超过最优的内存分配可能会导致会话接收内存分配错误，导致Linux oom killer杀死进程，或者导致内核缺少内核缓冲区来吸收写操作。 

综上所述，Postgres对于分配不足比分配过多更宽容。有时，了解系统在配置不完美时的行为比了解如何完美地配置它更有帮助，尤其是在不可能进行完美配置的情况下。 



------

### [![Internals](https://momjian.us/main/img/pgblog/internals.png) Wal 的意义](https://momjian.us/main/blogs/pgblog/2018.html#December_5_2018)

*Wednesday, December 5, 2018*

预写日志（wal）对Postgres的可靠性非常重要。然而,它的运作方式通常不清晰。 

wal日志中的“write-ahead”部分意味着所有数据库更改必须在提交之前写入pg_wal文件。但是，可以在事务提交之前或之后写入(和fsync'ed)事务脏的共享缓冲区。 

嗯?Postgres允许在事务提交之前将脏缓冲区写入存储?是的。当脏缓冲区被写入存储时，每个修改的行都用修改它的当前执行事务id标记。任何查看这些行的会话都知道在事务提交之前忽略这些更改。如果没有，长时间的事务可能会占用所有可用的共享缓冲区，并阻止未来的数据库更改。 

此外，Postgres允许在事务提交后将脏缓冲区写入存储?是的。如果Postgres在事务提交之后崩溃，但是在检查点写入修改后的共享缓冲区页之前崩溃，那么在恢复期间将重播wal，它将恢复事务所做的任何更改。 

它实际上是写入事务提交日志pg_xact，所有正在运行的会话都会参考pg_xact文件，以检测提交、中止或进程内的事务id。允许共享缓冲区写入独立于事务状态记录，允许灵活地处理工作负载。 



------

### [![Data modeling](https://momjian.us/main/img/pgblog/data_modeling.png) 视图与物化视图的比较](https://momjian.us/main/blogs/pgblog/2018.html#December_3_2018)

*Monday, December 3, 2018*

视图和物化视图是密切相关的。视图在每次访问时有效地运行视图查询，而物化视图将查询输出存储在表中，并在每个物化视图引用上重用结果，直到刷新物化视图。当底层查询或表速度较慢时，例如分析查询和外部数据包装表，这种缓存效果会变得更加显著。您可以将物化视图视为缓存视图。 



------

### [![Data modeling](https://momjian.us/main/img/pgblog/data_modeling.png) 可扩展性](https://momjian.us/main/blogs/pgblog/2018.html#November_30_2018)

*Friday, November 30, 2018*

可扩展性从创建之日起就被构建到Postgres中。在早期，可扩展性常常被忽略，使得Postgres服务器编程更加困难。然而，在过去的15年里，可扩展性使得Postgres能够以惊人的速度适应现代工作负载。如果没有Postgres的可扩展性，本文中提到的非关系数据存储选项就不可能实现。 



------

### [![Data modeling](https://momjian.us/main/img/pgblog/data_modeling.png) 数据存储选项 ](https://momjian.us/main/blogs/pgblog/2018.html#November_28_2018)

*Wednesday, November 28, 2018*

因为我花了30年时间做关系型数据库，您可能认为我认为所有存储都需要关系存储。但是，我已经使用了足够多的非关系型数据存储，以了解每种存储类型都有自己的优点和成本。 

要知道使用哪个数据存储来存储数据通常很复杂。让我们看看不同的存储级别，从最简单的到最复杂的依次是:

1. 平面文件:平面文件就是它们听起来的样子——存储在文件中的非结构化字节流。文件本身没有定义结构——结构必须在读取文件的应用程序中实现。这显然是存储数据最简单的方法，当只有一个用户和几个协调良好的应用程序需要访问时，它可以很好地处理较小的数据量。序列化多用户访问需要文件锁定。典型地更改需要重写完整的文件。

2. 文字处理文档:这类似于平面文件,但在数据文件中定义了结构。例如高亮显示部分。同样的平面文件限制应用。

3. 电子表格:这类似于文字处理文档，但是增加了更多的功能，包括计算和数据元素之间关系的定义。与前一种格式相比，这种格式的数据更加原子化。 

4. NoSQL存储:这消除了以前数据存储的许多限制。支持多用户访问和锁定并且修改单个数据元素不需要重写所有数据。 

5. 关系数据库:这是最复杂的数据存储选项。虽然存在非结构化选项，但在内部强制执行严格的结构。数据访问使用基于该结构的动态优化声明式语言。多用户和多应用程序访问是有效的。 

您可能认为，由于关系数据库具有最多的特性，所以所有的东西都应该使用它。然而，它的特点是复杂和死板。因此，所有级别对于某些用例都是有效的:

- 平面文件非常适合只读、单用户和单应用程序访问，例如配置文件。使用文本编辑器很容易进行修改。 

- 你知道有多少组织使用文字处理文档或电子表格来管理他们的组织?当只有少数人必须访问或修改数据时，这通常用于部门级别。 

- NoSQL在应用程序开发人员中流行起来，这些开发人员不希望关系系统太死板，而希望更简单的多节点部署。 

- 关系数据库仍然适用于多用户、多应用程序工作负载。 

所以，下次当有人使用电子表格处理他们的工作负载时，不要窃笑——它可能是最适合这项工作的工具。 



------

### [![Configuration](https://momjian.us/main/img/pgblog/configuration.png) First Wins, Last Wins, Huh?](https://momjian.us/main/blogs/pgblog/2018.html#November_26_2018)

*Monday, November 26, 2018*

最近有人指出Postgres的配置文件中有一个奇怪的行为。具体来说，他们提到了在postgresql.conf中最后设置的变量是生效的，但是在pg_hba.conf中，第一个匹配到的连接是生效的。它们都是集群数据目录中的配置文件，但是它们的行为不同。它们行为不同的原因很清楚——因为pg_hba.conf中的行顺序很重要，并且特殊的行可以放在普通的行之前(参见拒绝连接的使用)。尽管如此，它还是会让人困惑，所以我想指出来。 



------

### [![Conference](https://momjian.us/main/img/pgblog/conference.gif) 向会议提交演讲](https://momjian.us/main/blogs/pgblog/2018.html#November_5_2018)

*Monday, November 5, 2018*

我参加了很多会议，对于如何提交成功的会议发言，我有几点建议。首先，确定会议类型。然后，尝试提交与会议类型相匹配的演讲;可能的主题包括: 

- Postgres新特性

- 用户案例研究

- 内部构件

- 新工作负载

- 性能

- 应用程序开发


当然，只有其中一些主题与特定类型的会议相匹配。 

第二，提交多次会谈。很有可能比你知道的更多的人或者比你有更好的摘要的人，也会提交给会议。通过提交多个主题，您可以增加提交一些独特而有趣的内容的机会。 

第三，努力脱颖而出。也许你有一个关于你的主题的有趣的故事，或者是一幅能抓住你将要谈论的内容的图片。试着把这个问题告诉那些决定是否接受你的演讲的人。你以前成功地做过演讲吗?想办法也提一下。 

最后，试着提交一些能吸引参会者或给听众留下持久印象的东西。要做到这一点，你必须创造性地思考。 

哦，一旦你被录取，最难的部分就开始了——你必须写幻灯片。然而，不要认为在你演讲前30分钟你会想到一些惊人的想法。接受这种不太可能发生的情况，在幻灯片展示前几周制作。然后，如果你想在接下来的几周改善你的谈话，你就有时间去改善它。制作幻灯片可以巩固你的观点，当你思考如何展示你的演讲时，往往会有改进。警告一句——不要在演讲当天更改幻灯片;你更有可能用不熟悉的幻灯片来迷惑自己，而不是改进内容。 



------

### [![Community](https://momjian.us/main/img/pgblog/community.gif) 用户和开发者的区别](https://momjian.us/main/blogs/pgblog/2018.html#November_1_2018)

*Thursday, November 1, 2018*

一些开源项目在开源软件的开发者和用户之间有区别。因为Postgres最初是在一所大学开发的，而当基于internet的开发在1996年开始时，没有一个大学开发人员继续开发，所以我们所有活跃的开发人员都认为自己是在我们到来之前开发的代码的管理员。这就形成了一个扁平的组织结构，并有助于建立更紧密的用户/开发人员关系。 



------

### [![Community](https://momjian.us/main/img/pgblog/community.gif) 长途行为](https://momjian.us/main/blogs/pgblog/2018.html#October_19_2018)

*Friday, October 19, 2018*

新加入Postgres社区的人常常会对社区在某些问题上的慎重和在其他领域打破向后兼容的意愿感到困惑。源代码是32年前创建的，我们中的许多人已经从事Postgres 10-20年了。有了这段时间的参与，我们清楚地认识到我们的决定的长期后果。许多私有的和开源的开发者不会提前几年考虑，但是使用Postgres，这是我们的正常行为。 

这就导致了一些不寻常的Postgres行为:

- 每周的源代码评论改进
- 每年的源代码重新格式化
- 即使是很小的改动，特别是用户可见的改动，也会进行详尽的讨论
- Api重新设计

这种对细节的关注通常会让新用户觉得不寻常，但当考虑到多年视图时，这是有意义的。



------

### [![Community](https://momjian.us/main/img/pgblog/community.gif) "Get Off My Lawn"](https://momjian.us/main/blogs/pgblog/2018.html#October_17_2018)

*Wednesday, October 17, 2018*

正如您可能知道的，Postgres在通信方法上是老派的，它的大部分开发讨论、bug报告和一般帮助都依赖于电子邮件。这是1996年的做法，我们今天仍然在这样做。当然，一些项目已经移到github或Slack。 

作为一个项目，我们试图利用新技术，同时保留仍然是最优的技术，电子邮件无疑是其中之一。电子邮件自1996年以来变化不大，但电子邮件客户端已经发生了变化。以前，所有电子邮件都是使用类似文本编辑器的界面编写的，这种界面允许进行复杂的格式化和编辑。新的电子邮件工具，如Gmail，提供了一个更简单的界面，尤其是在移动设备上。这个简化的界面非常适合在火车上写邮件，但是对于与成千上万的人交流复杂的话题就不那么理想了。 

电子邮件可以处理数千人交流技术点的需求，以及对细粒度组合的需求。基本上，当你给成千上万的人发电子邮件时，花点时间让沟通变得清晰是值得的。然而，这封电子邮件解释了一个事实，即许多电子邮件工具更适合在功能有限的设备上轻松通信。 

我不确定社区能做些什么来改善这种情况。制作复杂的技术交流对于这个项目来说总是很重要的，但是实现这种交流的工具越来越少了。 

更新:这篇博客文章解释了许多电子邮件列表的机制与更现代的方法。2018-10-17 



------

### [![Community](https://momjian.us/main/img/pgblog/community.gif) 三年循环](https://momjian.us/main/blogs/pgblog/2018.html#October_15_2018)

*Monday, October 15, 2018*

在Postgres开放源码开发的早期，我们主要关注在几个周末就可以完成的特性。在几年之内，我们已经完成了其中的许多项目，并面临着试图以志愿者为主的团队来完成大型项目的挑战。然而，很快，大公司开始赞助开发人员的时候，我们又开始了大型功能开发。 

目前，日程表是我们唯一真正的挑战。我们每年都会发布一些主要的版本，但是许多特性需要多年才能完全实现。我们看到了这一多年来的进程: 

- Windows端口

- 时间点恢复

- Json

- 流复制


并正在完成更多的工作: 

- 并行

- 分区

- 即时编译（jit）

- 分片


因此，如果功能在一个版本中以一种有限的形式出现，而下两个到三个版本最终完成了该功能，那么这不是您的想象。 



------

### [![Client](https://momjian.us/main/img/pgblog/client.png) Installing PL/v8](https://momjian.us/main/blogs/pgblog/2018.html#October_12_2018)

*Friday, October 12, 2018*

PL/v8是Postgres的JavaScript服务端语言。它已经出现好几年了，但是v8语言中谷歌包方式的改变使得打包者构建PL/v8包变得很麻烦。

 因此，很少有包管理器仍然发布PL/v8。这令人失望，因为它削弱了我们的NoSQL特性。我们以前支持json存储和特定于json的服务器语言。第二个选项实际上不再可用，使用PL/v8的用户需要找到替代方案。这突出了软件严重依赖于其他软件的风险，这些软件不受它的控制，也不能维护它自己。 



------

### [![Client](https://momjian.us/main/img/pgblog/client.png) 多主机 Libpq](https://momjian.us/main/blogs/pgblog/2018.html#October_10_2018)

*Wednesday, October 10, 2018*

许多客户机接口语言使用Libpq与Postgres服务器通信。Postgres 10的一个新特性是可以为连接尝试指定多个服务器。具体来说，它允许连接字符串包含主机、hostaddr和端口值的多个集合。这些尝试直到有一个连接。 

NoSQL解决方案使用这种多主机连接的方法已经有一段时间了，所以Postgres现在也可以这样做。它没有独立连接池的所有特性，但也没有独立连接池的管理或性能开销，因此它当然适合某些环境的需要。 



------

### [![Administration](https://momjian.us/main/img/pgblog/administration.png) 触发写能力](https://momjian.us/main/blogs/pgblog/2018.html#October_9_2018)

*Tuesday, October 9, 2018*

Postgres对热备用服务器的支持允许在备用服务器上运行只读查询，但是在将备用服务器提升到主服务器时，如何处理只读会话呢?当备用服务器升级为主服务器后，新的连接被读写，但是现有的连接也被更改为读写: 

> ```
> SELECT pg_is_in_recovery();
>  pg_is_in_recovery
> -------------------
>  t
>  
> SHOW transaction_read_only;
>  transaction_read_only
> -----------------------
>  on
>  
> \! touch /u/pg/data2/primary.trigger
>  
> -- wait five seconds for the trigger file to be detected
> CREATE TABLE test (x INTEGER);
>  
> SELECT pg_is_in_recovery();
>  pg_is_in_recovery
> -------------------
>  f
>  
> SHOW transaction_read_only;
>  transaction_read_only
> -----------------------
>  off
> ```

注意，会话不需要断开和重新连接——它会自动提升为读写。 



------

### [![Administration](https://momjian.us/main/img/pgblog/administration.png) 移动表空间](https://momjian.us/main/blogs/pgblog/2018.html#October_3_2018)

*Wednesday, October 3, 2018*

表空间被设计成允许Postgres集群跨多个存储设备分布。Create tablespace在集群数据目录中的pg_tblspc目录中创建一个符号链接，指向新创建的表空间目录。 

不幸的是,虽然有一个命令可以移动表和索引之间的索引,但没有命令将表空间移到不同的目录。然而,自Postgres 9.2以来,移动表格的过程相当简单: 

​	1.记录要移动的表空间的oid

​	2.关闭Postgres集群

​	3.将表空间目录移动到相同的文件系统或不同的文件系统中

​	4.将移动的表空间的oid符号链接更新到新的表空间目录位置

​	5.重新启动服务器

这里有一个移动表空间的例子: 

> ```
> $ mkdir /u/postgres/test_tblspc
>  
> $ psql test
>  
> CREATE TABLESPACE test_tblspc LOCATION '/u/postgres/test_tblspc';
>  
> CREATE TABLE test_table (x int) TABLESPACE test_tblspc;
>  
> INSERT INTO test_table VALUES (1);
>  
> SELECT oid, * FROM pg_tablespace;
>   oid  |   spcname   | spcowner | spcacl | spcoptions
> -------+-------------+----------+--------+------------
>   1663 | pg_default  |       10 |        |
>   1664 | pg_global   |       10 |        |
>  16385 | test_tblspc |       10 |        |
>  
> SELECT pg_tablespace_location(16385);
>  pg_tablespace_location
> -------------------------
>  /u/postgres/test_tblspc
>  
> \q
>  
> $ pg_ctl stop
>  
> $ mv /u/postgres/test_tblspc /u/postgres/test2_tblspc/
>  
> $ cd $PGDATA/pg_tblspc/
>  
> $ ls -l
> lrwxrwxrwx 1 postgres postgres 23 Sep  5 22:20 16385 -> /u/postgres/test_tblspc
>  
> $ ln -fs /u/postgres/test2_tblspc 16385
>  
> $ ls -l
> lrwxrwxrwx 1 root root 24 Sep  5 22:25 16385 -> /u/postgres/test2_tblspc
>  
> $ pg_ctl start
>  
> $ psql test
>  
> SELECT * FROM test_table;
>  x
> ﻿---
>  1
>  
> SELECT pg_tablespace_location(16385);
>   pg_tablespace_location
> --------------------------
>  /u/postgres/test2_tblspc
> ```



------

### [![Administration](https://momjian.us/main/img/pgblog/administration.png) 切换/故障转移和会话迁移 ](https://momjian.us/main/blogs/pgblog/2018.html#October_1_2018)

*Monday, October 1, 2018*

我已经部署了切换和故障转移。在故障转移的情况下,旧的主是脱机的,因此没有选择将客户从旧主给新主。如果有切换,则有客户迁移的选项。假设使用流复制,只有一个服务器可以接受写入。因此,对于客户迁移,您也可以: 

- 强制旧主服务器上的所有客户端退出，然后提升新主服务器

- 等待旧主服务器上的所有客户端退出，然后提升新主服务器


如果您选择force，它将破坏应用程序;必须设计它们来处理断开并可能重新配置它们的会话，例如会话变量、游标和打开的事务。如果选择wait，在等待现有客户机断开连接时，如何处理希望连接的客户机?需要重新启动数据库服务器的小型升级也有类似的问题。 

唯一完美的解决方案是使用多主复制，以便新客户机可以连接到新主客户机，同时等待旧主客户机完成并断开连接。然而，仅仅为了最小化切换中断，支持多主机是非常昂贵的。 



------

### [![Presentation](https://momjian.us/main/img/pgblog/presentation.jpg) Postgres 11功能演示 ](https://momjian.us/main/blogs/pgblog/2018.html#September_14_2018)

*Friday, September 14, 2018*

现在我已经在纽约做了一个关于Postgres 11特性的演讲，我已经把我的幻灯片放到了网上。 



------

### [![Administration](https://momjian.us/main/img/pgblog/administration.png) 多主机 Pg_dump](https://momjian.us/main/blogs/pgblog/2018.html#September_12_2018)

*Wednesday, September 12, 2018*

您可能已经了解了pg_dump支持的逻辑转储，以及pg_restore(更简单地说，psql)恢复。您可能没有意识到，当涉及到多台计算机时，可以使用许多选项来转储和恢复。 

最简单的情况是在同一个服务器上转储和恢复: 

> ```
> $ pg_dump -h localhost -Fc test > /home/postgres/dump.sql
> $ pg_restore -h localhost test < /home/postgres/dump.sql
> ```

或者用纯文本转储: 

> ```
> $ pg_dump -h localhost -f /home/postgres/dump.sql test
> $ psql -h localhost -f /home/postgres/dump.sql test
> ```

有趣的是，当多主机的时候，你可以：

> ```
> $ # dump a remote database to your local machine
> $ pg_dump -h remotedb.mydomain.com -f /home/postgres/dump.sql test
>  
> $ # dump a local database and write to a remote machine
> $ pg_dump -h remotedb.mydomain.com test | ssh postgres@remotedb.mydomain.com 'cat > dump.sql'
>  
> $ # dump a remote database and write to the same remote machine
> $ pg_dump -h remotedb.mydomain.com test | ssh postgres@remotedb.mydomain.com 'cat > dump.sql'
>  
> $ # or a different remote machine
> $ pg_dump -h remotedb1.mydomain.com test | ssh postgres@remotedb2.mydomain.com 'cat > dump.sql'
> ```

您还有类似的恢复选项。下面我将使用psql，但是pg_restore的工作原理是一样的: 

> ```
> $ # dump a remote database and restore to your local machine
> $ pg_dump -h remotedb.mydomain.com test1 | psql test2
>  
> $ # dump a local database and restore to a remote machine
> $ pg_dump -h remotedb.mydomain.com test | ssh postgres@remotedb.mydomain.com 'psql test'
>  
> $ # dump a remote database and restore to the same remote machine
> $ pg_dump -h remotedb.mydomain.com test1 | ssh postgres@remotedb.mydomain.com 'psql test2'
>  
> $ # or a different remote machine
> $ pg_dump -h remotedb1.mydomain.com test | ssh postgres@remotedb2.mydomain.com 'psql test'
> ```

正如您所看到的，这是非常灵活的。 



------

### [![Administration](https://momjian.us/main/img/pgblog/administration.png) 监控复杂性](https://momjian.us/main/blogs/pgblog/2018.html#September_10_2018)

*Monday, September 10, 2018*

我一直无法理解Postgres中提供的许多监视选项。我终于将所有流行的监视工具收集到一个图表中(幻灯片96)。它显示了各种级别的监控:操作系统、进程、查询、解析器、计划器、执行器。它还分离出实时报告和跨时间警报/聚合选项。 



------

### [![Security](https://momjian.us/main/img/pgblog/security.png) 签名行 ](https://momjian.us/main/blogs/pgblog/2018.html#September_7_2018)

*Friday, September 7, 2018*

通过在我之前的博客文章中创建的rsa密钥，我们现在可以正确地对行进行签名，以提供完整性和不可抵赖性，这是我们以前没有的。为了说明这一点，让我们通过将最后一列重命名为signature来创建上一个模式的修改版本: 

> ```
> CREATE TABLE secure_demo2 (
>         id SERIAL, car_type TEXT, license TEXT, activity TEXT, 
>         event_timestamp TIMESTAMP WITH TIME ZONE, username NAME, signature BYTEA);
> ```

现在,让我们做前面的插入: 

> ```
> INSERT INTO secure_demo2
> VALUES (DEFAULT, 'Mazda Miata', 'AWR-331', 'flat tire',
> CURRENT_TIMESTAMP, 'user1', NULL) RETURNING *;
>  id |  car_type   | license | activity  |        event_timestamp        | username | signature
> ----+-------------+---------+-----------+-------------------------------+----------+-----------
>   1 | Mazda Miata | AWR-331 | flat tire | 2017-07-08 10:20:30.842572-04 | user1    | (null)
> ```

现在,我们使用我们的私有rsa密钥签名,而不是为此创建一个随机秘钥: 

> ```
> SELECT ROW(id, car_type, license, activity, event_timestamp, username)
> FROM secure_demo2
> WHERE id = 1
>  
> -- set psql variables to match output columns
> \gset
>  
> \set signature `echo :'row' | openssl pkeyutl -sign -inkey ~user1/.pgkey/rsa.key | xxd -p | tr -d '\n'`
>  
> UPDATE secure_demo2 SET signature = decode(:'signature', 'hex') WHERE id = 1;
>  
> SELECT * FROM secure_demo2;
>  id |  car_type   | license | activity  |        event_timestamp        | username | signature
> ----+-------------+---------+-----------+-------------------------------+----------+-------------
>   1 | Mazda Miata | AWR-331 | flat tire | 2017-07-08 10:20:30.842572-04 | user1    | \x857310...
> ```

为了以后验证数据行没有被修改，我们可以: 

> ```
> SELECT ROW(id, car_type, license, activity, event_timestamp, username), signature
> FROM secure_demo2
> WHERE id = 1;
>                                      row                                     | signature
> -----------------------------------------------------------------------------+-------------
>  (1,"Mazda Miata",AWR-331,"flat tire","2017-07-08 10:20:30.842572-04",user1) | \x857310...
> \gset
>  
> \echo `echo :'signature' | xxd -p -revert > sig.tmp`
> \echo `echo :'row' | openssl pkeyutl -verify -pubin -inkey /u/postgres/keys/user1.pub -sigfile sig.tmp`
> Signature Verified Successfully
>  
> \! rm sig.tmp
> ```

因为签名验证是使用公共证书完成的，所以任何人都可以验证数据有没有被修改。它还允许非作者验证数据是由私有证书的所有者创建的。 

这两个博客条目是相关的。第一个解释了如何创建和存储一个简单的消息身份验证代码(mac)。第二个解释了如何使用对称和公钥加密技术在客户端加密数据。这个博客条目展示了如何通过公钥签名进行消息身份验证，这样任何访问公钥的人都可以验证作者身份。 



------

### [![Security](https://momjian.us/main/img/pgblog/security.png) 客户端行访问控制 ](https://momjian.us/main/blogs/pgblog/2018.html#September_5_2018)

*Wednesday, September 5, 2018*

通常数据库管理员控制谁可以访问数据库数据。但是，客户端可以完全控制谁可以在openssl下访问数据库中的数据。 

首先，让我们从命令行为三个用户创建rsa密钥。我们首先在每个用户的主子目录中创建一个rsa公钥/私钥对，然后在共享目录/u/postgres/keys中复制他们的rsa公钥: 

> ```
> # # must be run as the root user
> # cd /u/postgres/keys
> # for USER in user1 user2 user3
> > do    mkdir ~"$USER"/.pgkey
> >       chown -R "$USER" ~"$USER"/.pgkey
> >       chmod 0700 ~"$USER"/.pgkey
> >       openssl genpkey -algorithm RSA -out ~"$USER"/.pgkey/rsa.key
> >       chmod 0600 ~"$USER"/.pgkey/*
> >       openssl pkey -in ~"$USER"/.pgkey/rsa.key -pubout -out "$USER".pub
> > done
> ```

更复杂的设置包括创建证书颁发机构，并为使用创建的密钥的每个用户签名证书。这允许证书颁发机构证明公钥属于指定的用户。 

有了这些，现在就可以使用公钥加密客户机上的数据，公钥只能由访问匹配私钥的人解密。下面是用户user1的一个例子: 

> ```
> # echo test4 | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user1.pub
> > openssl pkeyutl -decrypt -inkey ~"$USER"/.pgkey/rsa.key
> test4
> ```

它使用user1的公钥加密文本，然后使用它们的私钥解密文本。

现在，让我们创建一个表来保存加密数据，并添加一些加密数据: 

> ```
> CREATE TABLE survey1 (id SERIAL, username NAME, result BYTEA);
>  
> \set enc `echo secret_message | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user1.pub | xxd -p | tr -d '\n'`
> INSERT INTO survey1 VALUES (DEFAULT, 'user1', decode(:'enc', 'hex'));
>  
> -- save data for the other two users
> \set enc `echo secret_message | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user2.pub | xxd -p | tr -d '\n'`
> INSERT INTO survey1 VALUES (lastval(), 'user2', decode(:'enc', 'hex'));
>  
> \set enc `echo secret_message | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user3.pub | xxd -p | tr -d '\n'`
> INSERT INTO survey1 VALUES (lastval(), 'user3', decode(:'enc', 'hex'));
> ```

我们可以使用bytea数组将所有用户加密的数据放在同一行中: 

> ```
> CREATE TABLE survey2 (id SERIAL, username NAME[], result BYTEA[]);
>  
> \set enc1 `echo secret_message | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user1.pub | xxd -p | tr -d '\n'`
> \set enc2 `echo secret_message | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user2.pub | xxd -p | tr -d '\n'`
> \set enc3 `echo secret_message | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user3.pub | xxd -p | tr -d '\n'`
>  
> INSERT INTO survey2 VALUES (
>         DEFAULT,
>         '{user1, user2, user3}',
>         ARRAY[decode(:'enc1', 'hex'), decode(:'enc2', 'hex'), decode(:'enc3', 'hex')]::bytea[]);
> ```

我们可以只使用随机密码存储加密值一次，然后使用每个用户的公钥加密密码存储: 

> ```
> CREATE TABLE survey3 (id SERIAL, result BYTEA, username NAME[], keys BYTEA[]);
>  
> \set key `openssl rand -hex 32`
> \set enc `echo secret_message | openssl enc -aes-256-cbc -pass pass\::key | xxd -p | tr -d '\n'`
>  
> \set enc1 `echo :'key' | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user1.pub | xxd -p | tr -d '\n'`
> \set enc2 `echo :'key' | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user2.pub | xxd -p | tr -d '\n'`
> \set enc3 `echo :'key' | openssl pkeyutl -encrypt -pubin -inkey /u/postgres/keys/user3.pub | xxd -p | tr -d '\n'`
>  
> INSERT INTO survey3 VALUES (
>         DEFAULT,
>         :'enc',
>         '{user1, user2, user3}',
>         ARRAY[decode(:'enc1', 'hex'), decode(:'enc2', 'hex'), decode(:'enc3', 'hex')]::bytea[]);
> ```

要使用第一个模式(每行有一个用户，没有数组)解密数据，user1可以: 

> ```
> SELECT * FROM survey1 WHERE username = 'user1';
>  id | username |    result
> ----+----------+-------------
>   1 | user1    | \x80c9d0...
>  
> -- set psql variables to match output columns
> \gset
>  
> -- 'cut' removes \x
> \set decrypt `echo :'result' | cut -c3- | xxd -p -revert | openssl pkeyutl -decrypt -inkey ~user1/.pgkey/rsa.key`
>  
> SELECT :'decrypt';
>     ?column?
> ----------------
>  secret_message
> ```

对于survey2和survey3来说，这个过程是类似的。当然，这并不妨碍数据库管理员从数据库中删除数据，而且因为使用公钥加密，所以他们也可以添加数据。消息验证码(mac)可以防止这种情况。 



------

### [![Security](https://momjian.us/main/img/pgblog/security.png) 密码认证行](https://momjian.us/main/blogs/pgblog/2018.html#August_31_2018)

*Friday, August 31, 2018*

有一个假设，在数据库中存储数据时，您必须信任数据库管理员不修改数据库中的数据。虽然这通常是正确的，但是可以检测数据库行的更改(而不是删除)。 

为了说明这一点，让我们首先创建一个表: 

> ```
> CREATE TABLE secure_demo (
>         id SERIAL, car_type TEXT, license TEXT, activity TEXT, 
>         event_timestamp TIMESTAMP WITH TIME ZONE, username NAME, hmac BYTEA);
> ```

最后一列(hmac)用于更改检测。在表中插入一行: 

> ```
> INSERT INTO secure_demo
> VALUES (DEFAULT, 'Mazda Miata', 'AWR-331', 'flat tire',
> CURRENT_TIMESTAMP, 'user1', NULL) RETURNING *;
>  id |  car_type   | license | activity  |       event_timestamp        | username | hmac
> ----+-------------+---------+-----------+------------------------------+----------+------
>   1 | Mazda Miata | AWR-331 | flat tire | 2017-07-06 20:15:59.16807-04 | user1    |
> ```

请注意，该查询还返回插入行的文本表示，包括计算列id和event_timestamp。

为了检测行更改，需要生成消息身份验证码(mac)，该代码使用只有客户端知道的密码生成。有必要在客户端生成mac，这样密码就永远不会传输到服务器上。这些psql查询更新插入的行来存储mac: 

> ```
> SELECT ROW(id, car_type, license, activity, event_timestamp, username)
> FROM secure_demo
> WHERE id = 1;
>  
> -- set psql variables to match output columns
> \gset
>  
> \set hmac `echo :'row' | openssl dgst -sha256 -binary -hmac 'MY-SECRET' | xxd -p | tr -d '\n'`
>  
> UPDATE secure_demo SET hmac = decode(:'hmac', 'hex') WHERE id = 1;
>  
> SELECT * FROM secure_demo;
>  id |  car_type   | license | activity  |       event_timestamp        | username |   hmac
> ----+-------------+---------+-----------+------------------------------+----------+-------------
>   1 | Mazda Miata | AWR-331 | flat tire | 2017-07-06 20:15:59.16807-04 | user1    | \x9549f1...
> ```

稍后验证数据行没有修改,可以: 

> ```
> SELECT ROW(id, car_type, license, activity, event_timestamp, username), hmac
> FROM secure_demo
> WHERE id = 1;
>                                     row                                     |   hmac
> ----------------------------------------------------------------------------+-------------
>  (1,"Mazda Miata",AWR-331,"flat tire","2017-07-06 20:15:59.16807-04",user1) | \x9549f1...
>  
> \gset
>  
> \echo  ' E''\\\\x'`echo :'row' | openssl dgst -sha256 -binary -hmac 'MY-SECRET' | xxd -p | tr -d '\n'`''''
>  E'\\x9549f10d54c6a368499bf98eaca716128c732132680424f74cb00e1d5a175b63'
>  
> \echo :'hmac'
>  E'\\x9549f10d54c6a368499bf98eaca716128c732132680424f74cb00e1d5a175b63'
> ```

数据库管理员可以替换或删除hmac值，但这将被检测到。这是因为计算一个正确的hmac需要MY-SECRET密钥，它永远不会发送到服务器。 

 上面的解决方案只允许访问密钥的人确定行是否被修改，这意味着只有他们可以检查消息的完整性。更复杂的解决方案是使用私钥签署一个散列的行值,这将允许任何人访问公共密钥检查行有没有被修改,但仍只允许那些访问私钥生成一个新的hmac。这也将允许不可抵赖性。

 插入返回的行值可能与提供的值不匹配，因此需要添加一些客户端检查。也没有检测到删除的行;这类似于试图检测阻塞的tls连接尝试的问题。 

 对于许多数据库来说，这样的设置显然是多余的，但是在一些用例中，客户端保证的数据完整性(独立于数据库管理员)是有用的。使用公钥基础设施的不可抵赖性有时也很有用。 



------

### [![Security](https://momjian.us/main/img/pgblog/security.png) 外部数据包装和密码](https://momjian.us/main/blogs/pgblog/2018.html#August_29_2018)

*Wednesday, August 29, 2018*

外部数据封装器(fdw)允许数据读取和写入外部数据源,如NoSQL存储或其他Postgres服务器。不幸的是,fdws支持的身份验证通常仅限于使用创建用户映射定义的密码。例如,postgres_fdw只支持基于密码的身份验证。例如，scram。虽然只有数据库管理员可以看到密码,但这仍然是一个安全问题。 

理想情况下，至少一些Postgres fdws应该支持更复杂的身份验证方法，特别是SSL证书。另一种选择是允许通过fdws发送用户身份验证，以便用户对fdw源和目标具有相同的权限。从技术上讲，fdw身份验证并不仅限于密码。这个问题已经讨论过了，看起来有人有解决它的计划，所以希望它能很快得到改进。 



------

### [![Security](https://momjian.us/main/img/pgblog/security.png) 证书撤销列表 ](https://momjian.us/main/blogs/pgblog/2018.html#August_27_2018)

*Monday, August 27, 2018*

如果您正在设置Postgres服务器或客户机的TLS/SSL证书，请确保还配置了对证书撤销列表(crl)的支持。这个由证书颁发机构分发的列表列出了不应该再受信任的证书。 

虽然crl最初可能是空的，但是当证书或设备使用的私钥以未经授权的方式公开时，或者访问私钥的员工离开您的组织时，就会出现这种情况。当这种情况发生时，您将需要使证书失效的能力——预先配置这种能力将会有帮助，特别是在危机期间。 



------

### [![Performance](https://momjian.us/main/img/pgblog/performance.png) Oracle Real Application Clusters (RAC)](https://momjian.us/main/blogs/pgblog/2018.html#July_9_2018)

*Monday, July 9, 2018*

我经常被问到Oracle RAC。我通常的回答是Oracle RAC提供了50%的高可靠性(存储是共享的，镜像是有帮助的)和50%的可伸缩性(CPU和内存是可伸缩的，存储不是)。将应用程序划分到特定节点以避免缓存一致性开销的需求是另一个缺点。(我的缩放演示展示的是Oracle RAC。) 

我说过，社区不太可能走Oracle RAC的方向，因为它不能完全解决一个单独的问题，而且过于复杂。社区更喜欢完全解决问题和简单的解决方案。 

 对我来说，流复制完全解决了高可用性问题，分片完全解决了可伸缩性问题。当然，如果您同时需要这两种解决方案，则必须同时部署这两种解决方案，这将提供两个解决方案的100%，而不是像Oracle RAC提供每个解决方案的50%。 

但是，我确实认为使用Oracle RAC进行数据库升级更容易，而且添加/删除节点要比使用分片容易得多。我认为，这张图表可以总结它: 

> ```
>                          HA   Scaling  Upgrade Add/Remove
>         Oracle RAC       50%     50%    easy    easy
>         Streaming Rep.  100%     25%*   hard    easy
>         Sharding          0%    100%    hard    hard
>         
>         * Allows read scaling
> ```

(我在2016年把这个贴到了pgsql-general。 )



------

### [![Performance](https://momjian.us/main/img/pgblog/performance.png) 查询计划会谈](https://momjian.us/main/blogs/pgblog/2018.html#June_23_2018)

*Saturday, June 23, 2018*

软件工程电台刚刚发布了一段我对Postgres查询优化器进行的采访的一个一小时的录音。对于任何想了解关系数据库如何优化查询的人来说，它足够通用，也非常有用。 

另一个不相关的消息是，我很快就要动身前往欧洲进行为期25天的巡回演讲。我将在苏黎世、伦敦和阿姆斯特丹(法兰克福的一个用户团体)为期一天的会议上发表演讲，并将在欧洲各地的10个EnterpriseDB活动上发表演讲。 



------

### [![Presentation](https://momjian.us/main/img/pgblog/presentation.jpg) Postgres 会永远存在吗?](https://momjian.us/main/blogs/pgblog/2018.html#June_7_2018)

*Thursday, June 7, 2018*

我有机会在今年的Postgres Vision大会上提出一个不同寻常的话题:Postgres会永远存在吗?这不是我经常谈论的话题，但是它提出了一些有趣的对比:开源软件与私有软件有何不同，以及为什么创新是软件使用寿命的基础。要得到这个问题的答案，你必须看幻灯片。 



------

### [![News](https://momjian.us/main/img/pgblog/news.gif) Postgres 11发布说明草稿 ](https://momjian.us/main/blogs/pgblog/2018.html#May_17_2018)

*Thursday, May 17, 2018*

我已经完成了Postgres 11发布说明的草稿。这个版本由167个条目组成，在分区、并行性和经由程序的服务器端事务控制方面取得了很大进展。一个更意想不到但有用的特性是“允许在空缓冲区中使用‘quit’和‘exit’退出psql”。 

发布说明将不断更新，直到最终发布，预计今年9月或10月。 



------

### [![Documentation](https://momjian.us/main/img/pgblog/documentation.png) 中级证书 ](https://momjian.us/main/blogs/pgblog/2018.html#January_22_2018)

*Monday, January 22, 2018*

我之前提到了高质量文档的重要性，所以我们一直在寻求改进。这封2013年的邮件试图将如何正确使用中间ssl/tls证书与Postgres结合的规则编入法典。此时，我们的文档被更新，建议使用根证书存储中间证书，因为不清楚在什么情况下，中间证书被转移到远程服务器，以链接到受信任的根证书。 

在我研究四次安全讲座的时候，我学习了证书处理。我在verifymanual页面找到了证书链解析规则。在测试各种证书位置时，我还发现Postgres遵循相同的规则。 

通过这次测试，我意识到2013年得出的结论是不准确的，至少是不完整的。虽然文档化的过程是有效的，但是更实用和推荐的方法是存储中间证书(使用v3_ca扩展创建)，并将叶子证书发送到远程端。(我认为，在创建中间证书时使用v3_ca扩展的要求是导致过去许多测试混淆的原因。) 

这个新过程允许在过期时替换短生命期的叶子和中间证书，而长生命期的根证书存储保持不变。例如，客户端要验证服务器的证书，服务器将包含中间证书和服务器的叶子证书，客户端只需要根证书，根证书很少更改。 

为了推荐这个新过程，所有支持的Postgres版本的文档都已更新。我还添加了一些示例脚本，展示如何创建root-leaf和root- middle -leaf证书链。 

 这些更改将在下一个较小的Postgres版本中发布，计划在下个月发布。在此新文档发布之前，您可以阅读服务器和libpq ssl部分中的Postgres 11文档中的更新。我希望这个澄清的文档将鼓励人们使用ssl和ssl证书验证。 



------

### [![Presentation](https://momjian.us/main/img/pgblog/presentation.jpg) 四次新的安全会谈](https://momjian.us/main/blogs/pgblog/2018.html#January_15_2018)

*Monday, January 15, 2018*

在过去的几个月里，我已经完成了四次新的安全会谈，总共294张幻灯片。第一次和第三次分别介绍了加密技术和加密硬件的基础知识。第二和第四部分讨论了这些基本原理的应用。第二部分讨论tls，包括Postgres对ssl证书的使用。第四部分介绍了应用程序使用加密硬件的情况(包括Postgres)。 



------

### [![Conference](https://momjian.us/main/img/pgblog/conference.gif) 俄罗斯采访视频](https://momjian.us/main/blogs/pgblog/2018.html#January_10_2018)

*Wednesday, January 10, 2018*

我刚刚用英语对俄罗斯Postgres用户组进行了两个小时的采访。采访的视频记录在网上，并涵盖了俄罗斯与会者提出的问题。 



------

### 网络论坛?

*Friday, January 5, 2018*

这个电子邮件主要探讨了社区支持web论坛代替电子邮件列表的想法，大多数社区开发和讨论都是电子邮件列表中进行的。不参加网上论坛的理由包括: 

- 以前试过，但是失败了

- 更大的网络论坛社区已经存在，例如，堆栈溢出, [Stack Overflow](https://stackoverflow.com/questions/tagged/postgresql)

- 已建立的Postgres社区成员更喜欢电子邮件


最后，我认为Postgres社区需要更好的宣传外部社区的存在，帮助Postgres用户，例如Slack。例如，Postgres irc通道已经得到了很好的宣传，目前有1100个连接的用户。另外，EnterpriseDB在六个月前创建了Postgres Rocks 网络论坛。 



------

### Wal and Xlog

*Wednesday, January 3, 2018*

Postgres并不擅长命名事物。当然，有句老话是这样说的:“在计算机科学中只有两件难事:缓存失效和命名。”由于Postgres已经31岁了，并且是由几个不同的项目团队开发的，所以命名可能更加不一致。 

一个命名不一致的地方是write-ahead log的名称，这种情况我们已经讨论了很多年了。Postgres在诸如wal_level这样的服务器变量中使用了首字母wal，但是在PGDATA目录被称为pg_xlog。在“pg_xlog”中，“x”代表“trans”，是“transaction”的缩写，“log”当然是“日志”的意思，所以“xlog”是“transaction log”的缩写。这也令人困惑的，因为有一个clog目录记录“事务状态”信息(提交、中止)。因此，“xlog”或“transaction log”已经是一个糟糕的名字了，如果将它作为wal引用的话，就更糟了。 

Postgres 10对删除“xlog”和“clog”的引用进行了更改，并一致地将它们命名为“wal”和“pg_xact”。这个电子邮件帖子涵盖了我们改变了什么以及为什么要改变的许多血淋淋的细节。更改内部数据库对象的名称并不理想，这将给迁移到Postgres 10的用户带来一些痛苦，但Postgres的未来用户将对Postgres及其工作方式有更一致的体验。 