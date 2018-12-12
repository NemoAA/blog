# 企业级PostgreSQL扩展

> 本文翻译自[PostgreSQL Extensions for an Enterprise-Grade System](https://www.percona.com/blog/2018/10/05/postgresql-extensions-for-an-enterprise-grade-system/)

在本系列博客中，我们一直在讨论构建企业级postgresql的相关设置，例如安全、备份策略、高可用，以及不同规模postgresql。在本篇博客中，我们将回顾一些最流行的开源postgresql扩展，这些扩展的一些功能用于满足特定的一些需求。我们将在文章中讨论一些关于10月10号举行的网络研讨会的一些内容。

## 1拓展与PostgreSQL扩展

postgresql是世界上功能最丰富、最先进的开源关系型数据库之一。他的特性不仅仅是通过社区发布的主要/维护版本的功能，还包括使用postgresql中的扩展可以开发出上百个附加功能，以满足特定用户的需求。其中一些扩展非常流行，对于构建企业级postgresql是非常有用的。我们在之前的博客中提到一些`fdw`的扩展（[mysql_fdw](https://www.percona.com/blog/2018/08/24/postgresql-accessing-mysql-as-a-data-source-using-mysql_fdw/) 和 [postgres_fdw](https://www.percona.com/blog/2018/08/21/foreign-data-wrappers-postgresql-postgres_fdw/)），可以允许postgresql数据库与远程的相同/不同数据库（如postgresql、mysql、mongodb等）进行对话。现在我们将讨论一些其他的扩展，这些可以扩展postgresql服务器的能力。

### 1.1pg_stat_statements

[pg_stat_statements](https://www.postgresql.org/docs/10/static/pgstatstatements.html) 模块提供了跟踪服务器所执行的所有sql语句统计信息的功能。该模块收集的统计信息可以通过`pg_stat_statements`视图进行查看。此模块要安装在每个要监控的数据库中，而且像此列表中其他扩展一样，它的 [contrib](https://www.postgresql.org/docs/10/static/contrib.html) 版本可以从[PostgreSQL PGDG repository](https://yum.postgresql.org/repopackages.php)中获得。

### 1.2pg_repack

postgresql中的表可能会由于MVCC特性而导致碎片化和膨胀，或者是因为大量的行被删除。这不仅会导致表中的空闲空间被占用，而且还会导致执行的sql语句效率不高。`pg_repack`是通过最流行的重新组织和打包表的办法来解决这个问题的。它可以重新组织表的内容，而无需在处理过程中对其设置排它锁。在重新打包过程中不会阻塞`DML`和查询操作。pg_repack1.2版本进一步引入并行索引构建新特性，以及重建索引的能力。详情请参阅[official documentation](http://reorg.github.io/pg_repack/) 。

### 1.3pgaudit

postgresql有一个基础的语句日志功能。它可以设置log_statement =all参数来使用标准日志记录工具来实现。但这不足以满足大多数审计要求。企业部署的数据库特性之一就是针对用户交互/语句进行细粒度审计的功能。这是许多安全标准主要的遵从要求。

postgresql审计扩展(`pgaudit`)通过标准的postgresql日志记录工具提供详细的会话和/或对象审计日志记录。详情请参阅 [settings section of its official documentation](https://github.com/pgaudit/pgaudit#settings)。

### 1.4pldebugger

对于使用pl/pgsql编写存储过程的开发人员来说，这是一个必要的扩展。此扩展可以和[pgadmin](https://www.pgadmin.org/)等GUI工具很好的集成起来，它允许开发人员对代码逐步的进行调试。在pgdg存储库中有`pldebugger`包，安装很简单，设置好后我们就可以进行远程的代码调试了。

![img](https://www.percona.com/blog/wp-content/uploads/2018/10/Pldebugger.png)

官方git链接[在这里](https://git.postgresql.org/gitweb/?p=pldebugger.git)。

### 1.5plprofiler

这是一个很好的扩展，可以找到执行慢的代码位置。这是非常有用的，特别是在专用数据库（如Oracle到postgresql）的复杂迁移过程中，会影响应用程序的性能。这个扩展可以编写一份关于总体执行时间和表状态的报告，并提供每一行代码的清晰信息。这个扩展在PGDG repo中是不可用的，需要从源码中构建它。关于构建和安装`plprofiler`的详细信息将在以后的博客中介绍。同时，官方的库和文档也可以使用  [here](https://bitbucket.org/openscg/plprofiler)。

### 1.6PostGIS

`postgis`可以说是开放地理空间联盟规范的最通用的实现。我们可以看到`postgis`中的 [大量特性](https://postgis.net/features/)，这些特性在任何其他关系型数据库中都很少可用。

许多用户主要选择使用postgresql是因为支持`postgis`特性，事实上所有的这些特征不是由单个扩展实现的，而是由一系列扩展实现的。这使得`postgis`成为源代码构建中最复杂的扩展之一了。幸运的是所有的扩展都可以在PGDG中获得：

```shell
$ sudo yum install postgis24_10.x86_64 
```

只要安装了postgis包，我们就能在目标数据库上创建扩展了：

```plsql
postgres=# CREATE EXTENSION postgis;
CREATE EXTENSION
postgres=# CREATE EXTENSION postgis_topology;
CREATE EXTENSION
postgres=# CREATE EXTENSION postgis_sfcgal;
CREATE EXTENSION
postgres=# CREATE EXTENSION fuzzystrmatch;
CREATE EXTENSION
postgres=# CREATE EXTENSION postgis_tiger_geocoder;
CREATE EXTENSION
postgres=# CREATE EXTENSION address_standardizer;
CREATE EXTENSION 
```


### 1.7语言扩展 : PL/Python, PL/Perl, PL/V8,PL/R etc.

postgresql的另一个强大的特性就是对编程语言的支持。你可以几乎用所有的编程语言写数据库的函数/存储过程。

因为有大量的库和完善的社区，根据TIOBE程序设计指标python在编程语言中排名第三。你的团队技能和编码库在postgresql上也是支持的！用Java脚本为Node.js或者Angular编写代码的团队可以轻松的在PL/V8中编写postgresql代码。所需要的软件包都可以在pgdg库中找到。

### 1.8cstore_fdw

`cstore_fdw`是postgresql的列式存储扩展。列式存储对数据分析场景下的批量加载提供了显著的好处。`cstore_fdw`的专有特性是通过从磁盘读取相关数据来提供性能。它可以将数据压缩到6到10倍，减少了数据存档的空间。 [这里](https://github.com/citusdata/cstore_fdw)有官方文档和库 。

### 1.9HypoPG

`hypopg`是一个支持添加虚拟索引的扩展--也就是说，不实际添加索引。这有助于我们回答例如“如果x列上有索引，执行计划将会怎样”等问题。安装和说明是[官方文档](https://hypopg.readthedocs.io/en/latest/installation.html)的一部分。

### 1.10mongo_fdw

`mongo_fdw`将mongodb的集合在postgresql中以表的形式体现。这是nosql和sql的结合。我们将在以后的博客中讨论这个扩展。这里有[官方文档](https://github.com/EnterpriseDB/mongo_fdw)可以使用。

### 1.11tds_fdw

postgresql另一个重要的扩展就是`tds_fdw`。在微软的sqlserver和sybase中都使用了TDS格式的数据。它可以将sqlsever或者sybase数据库中表作为postgresql的本地表进行使用。`fdw`使用的是 [FreeTDS](http://www.freetds.org/) libraries。

### 1.12orafce

正如前面所提到的，有许多Oracle正在往postgresql上进行迁移。对于那些正在迁移服务器的人来说，postgresql中不兼容的函数是很麻烦的。`orafce`扩展就实现了Oracle数据库中的一些功能。该功能在Oracle10g上得到了验证，该模块对于生产工作非常有用。请参阅其 [官方文档](https://github.com/orafce/orafce#orafce---oracles-compatibility-functions-and-packages) 中有关PostgreSQL中实现的Oracle函数的列表。

### 1.13TimescaleDB

在这个IOT和互联设备的新世界中。对于时序数据需求越来越大。`timescale`可以将postgresql转换为可扩展时序数据进行存储。[官方网站](https://www.timescale.com/) 的链接。

### 1.14pg_bulkload

将大量数据以非常高效和快速的方式加载到数据库中对您来说是一个挑战吗?如果这样的话，`pg_bulkload`可能会帮助你解决这个问题。[官方文档](http://ossc-db.github.io/pg_bulkload/index.html) 的链接。

### 1.15pg_partman

postgresql10引入了分区。但是创建新的分区和维护现有分区，包括清除不需要的分区时需要手工操作，如果你想使用自动化的部分维护，可以看看`pg_partman`提供了什么功能。 [官方文档 ](https://github.com/pgpartman/pg_partman)的链接。

### 1.16wal2json

postgresql具有与逻辑复制相关的内置特性，另外的信息被记录在WAL中，这将有助于逻辑解码。`wal2json`是一个流行的逻辑解码输出插件。还可以用于不同的用途，包括变化数据捕获。除了`wal2json`之外还有其他输出插件：[PostgreSQL wiki](https://wiki.postgresql.org/wiki/Logical_Decoding_Plugins)中有一个简明的列表。

还有更多扩展可以帮助我们使用开源解决方案搭建企业级postgresql。请随意评论，并询问我们是否知道有一种产品能满足您的特殊需求。如果还有时间，报名参加我们十月的网络研讨会问我们！