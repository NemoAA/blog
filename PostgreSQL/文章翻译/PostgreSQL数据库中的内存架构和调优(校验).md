# PostgreSQL数据库中的内存架构和调优 

> 文章翻译自[architecture-and-tuning-memory-postgresql-databases](https://severalnines.com/blog/architecture-and-tuning-memory-postgresql-databases?tdsourcetag=s_pcqq_aiomsg/)

PostgreSQL中的内存管理对于提高数据库服务器的性能非常重要。PostgreSQL的配置文件（postgresql .conf）管理数据库服务器的配置。它使用参数的默认值，但是我们可以更改这些值以更好地配合工作负载和操作环境。 

在本文中，我们将介绍这些内存相关参数。在开始介绍之前，让我们先看看PostgreSQL中的内存架构。 

## 内存架构

PostgreSQL中的内存可以分为两类:

1. 本地内存区域:分配给每个后端进程使用。

2. 共享内存区域:它被PostgreSQL服务器的所有进程使用。

![img](https://severalnines.com/sites/default/files/blog/node_5287/image1.png)

## 本地内存区域

在PostgreSQL中，每个后端进程分配本地内存进行查询处理;每个区域被划分为大小固定或可变的子区域。

子区域如下。

#### Work_mem

执行器使用这个区域对进行ORDER BY和DISTINCT操作的元组进行整理。它还用于merge-join和hash-join操作的表连接。

#### Maintenance_work_mem

此参数用于某些维护操作(VACUUM，REINDEX)。 

#### Temp_buffers

执行器使用此区域存储临时表。 

## 共享内存区域

共享内存区域在PostgreSQL server启动时分配。这个区域被划分成几个固定大小的子区域。 

#### Shared buffer pool

PostgreSQL将表和索引中的页面从持久存储加载到共享缓冲池，然后直接对它们进行操作。 

#### WAL buffer

PostgreSQL支持WAL (Write ahead log)机制，以确保在服务器故障后不会丢失数据。WAL数据实际上是PostgreSQL中的一个事务日志，WAL buffer是将WAL数据写入持久存储之前的一个缓冲区域。 

#### Commit Log

提交日志(commit log, CLOG)保存所有事务的状态，是并发控制机制的一部分。提交日志被分配给共享内存，并在整个事务处理过程中使用。

PostgreSQL定义了以下四种事务状态。

1. IN_PROGRESS
2. COMMITTED
3. ABORTED
4. SUB-COMMITTED

## 内存参数调优

在PostgreSQL中，有一些重要的参数是用于内存管理的： 

### Shared_buffers

此参数指定用于共享内存缓冲区的内存容量。shared_buffers参数确定服务器有多少内存用于缓存数据。shared_buffers的默认值通常为128 mb (128MB)。

这个参数的默认值非常低，因为在一些平台上，如较老的Solaris版本和SGI，想要较大的值需要进行侵入性操作，比如重新编译内核。即使在现代Linux系统上，如果不首先调整内核设置，内核可能也不允许shared_buffers超过32MB。

在PostgreSQL 9.4和更高版本中，这种机制已经发生了变化，因此内核设置不需要在这里进行调整。

如果数据库服务器上有高负载，那么设置高值将提高性能。

如果您有一个具有1GB或更多内存的专用DB服务器，shared_buffer配置参数的合理初始值是系统内存的25%。 

shared_buffers的默认值= 128 MB。更改需要重启PostgreSQL服务。 

下面是设置shared_buffers的一般建议。

- 在2GB内存以下，将shared_buffers的值设置为系统总内存的20%。
- 在32GB内存以下，将shared_buffers的值设置为系统总内存的25%。
- 超过32GB内存，将shared_buffers的值设置为8GB

### Work_mem

此参数指定内部排序操作和散列表在写入临时磁盘文件之前要使用的内存量。如果发生了很多复杂的排序，并且您有足够的内存，那么增加work_mem参数允许PostgreSQL进行更大的内存排序将比基于磁盘的排序更快。 

注意，对于复杂查询，许多排序或哈希操作可能并行运行。在开始将数据写入临时文件之前，将允许每个操作使用与该值指定的内存相同的内存。有一种可能性是，几个会话可以同时执行这些操作。因此，使用的总内存可能是work_mem参数值的许多倍。 

在选择正确的值时请记住这一点。排序操作用于ORDER BY、DISTINCT和merge连接。哈希表用于哈希连接、基于哈希的子查询处理和基于哈希的聚合。

参数log_temp_files可用于记录排序、散列和临时文件，这对于判断排序是否溢出到磁盘而不是装入内存非常有用。您可以使用EXPLAIN ANALYZE查看查询计划检查溢出到磁盘的排序。例如，在EXPLAIN ANALYZE的输出中，如果您看到像这样的行:“Sort Method: external merge Disk: 7528kB”，那么一个至少8MB的work_mem将把中间数据保存在内存中，并提高查询响应时间。 

work_mem的默认值是4MB。

一般建议work_mem如下设置：

- 从低值开始:32-64MB
- 然后在日志中查找temporary file”行
- 设置为最大临时文件的2-3倍

### maintenance _work_mem

此参数指定维护操作使用的最大内存量(如VACUUM、CREATE INDEX和ALTER TABLE ADD FOREIGN KEY)。由于数据库会话一次只能执行其中一个操作，而PostgreSQL安装没有很多操作同时运行，因此将maintenance_work_mem的值设置为明显大于work_mem的值是安全的。 

设置更大的值可以提高vacuum和恢复数据库转储的性能。

有必要记住，在autovacuum运行时，可能会分配到autovacuum_max_workers乘以此内存的内存量，因此请注意不要将默认值设置得太高。

maintenance_work_mem的默认值是64MB。

一般建议maintenance_work_mem如下设置：

- 设置系统内存的10%，最多1GB
- 如果vacuum有问题，可以设置得更高

### Effective_cache_size

应该将effective_cache_size设置为操作系统和数据库本身可用于磁盘缓存的内存的估计数。这是关于操作系统和PostgreSQL缓冲缓存中可用内存的指导原则，而不是分配。

PostgreSQL 查询计划使用这个值来确定它所考虑的计划是否适合内存。如果设置得太低，索引可能无法按您期望的方式执行查询。由于大多数Unix系统在缓存时都很主动，所以专用数据库服务器上至少50%的可用内存将充满缓存的数据。

一般建议effective_cache_size如下设置：

- 将该值设置为可用文件系统缓存的数量
- 如果您不知道，请将该值设置为系统总内存的50%

effective_cache_size的默认值是4GB。

### Temp_buffers

此参数设置每个数据库会话使用的临时缓冲区的最大值。会话本地缓冲区仅用于访问临时表。此参数的设置可以在单个会话中更改，但只能在会话中首次使用临时表之前更改。

PostgreSQL数据库利用这个内存区域来保存每个会话的临时表，当连接关闭时，这些临时表将被清除。

temp_buffer的默认值为8MB。

## Conclusion

理解内存架构并能够对参数进行适当的调优对于提高性能非常重要，对于高负载尤其必要。更多有关此类的性能调优技巧，请查看 [performance cheat sheet for PostgreSQL](https://severalnines.com/blog/performance-cheat-sheet-postgresql)。 