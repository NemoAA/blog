# **PostgreSQL 11中的分区改进**

>  文章翻译自:https://blog.2ndquadrant.com/partitioning-improvements-pg11/

PostgreSQL中的分区系统最初是由2ndQuadrant创始人Simon Riggs在PostgreSQL 8.1中添加的。它基于继承表，并使用了一种`约束排除`的新技术将不相关的表排除在被查询扫描之外。虽然当时是前进了一大步，但现在使用起来既麻烦又慢，因而需要更换。

在PostgreSQL10中，由于Amit Langote的努力，它被现代风格的`declarative partitioning`取代。这种新技术意味着不再需要手动编写代码来将数据分配到正确的分区，并且不再需要为每个分区手动创建正确的约束：系统会自动执行这些操作。

但是，在PostgreSQL 10中，也就仅仅做了以上一点点的改善。正如Robert Haas在`Warsaw’s PGConf.EU`大会上发表的演讲一样，由于代码的复杂性和时间限制，在PostgreSQL 10的分区表中缺乏很多功能	。

许多人致力于在PostgreSQL 11中改善这种情况，以下是我重新统计的结果，并将之分为三个方面：

- 1. 新的分区功能
  2. 分区表上更好的DDL支持
  3. 性能优化

## 1. 新的分区功能


在PostgreSQL 10中，分区表可以采用RANGE分区或者LIST分区。这些分区是对于基本的数据库是足够的，但对于许多其它设计，就需要使用在PostgreSQL 11中添加的新的分区模式：HASH分区。许多用户需要它，而且通过Amul Sul的努力已经实现这一目标。下面是一个简单的例子：

```sql
CREATE TABLE clients (
client_id INTEGER, name TEXT
) PARTITION BY HASH (client_id);
 
CREATE TABLE clients_0 PARTITION OF clients
    FOR VALUES WITH (MODULUS 3, REMAINDER 0);
CREATE TABLE clients_1 PARTITION OF clients
    FOR VALUES WITH (MODULUS 3, REMAINDER 1);
CREATE TABLE clients_2 PARTITION OF clients
    FOR VALUES WITH (MODULUS 3, REMAINDER 2);
```

并非所有分区都必须使用相同的MODULUS值；这允许您稍后创建更多的分区，并在必要时一次重新分配一个分区。

Amit Khandekar实现的另一个非常重要的功能是允许UPDATE将行从一个分区移动到另一个分区 。也就是说，如果分区列的值发生更改，则该行会自动移动到正确的分区。以前，该操作会抛出错误。

另一个由Amit Langote实现的新功能是INSERT ON CONFLICT UPDATE可以应用于分区表。以前，对于分区表，此命令将失败。可以通过确定行最终位于哪个分区来实现它，但这不方便。这里不会详细介绍那个命令的细节，但是如果你希望在Postgres中使用UPSERT，那就需要使用它。需要注意的是，UPDATE操作可能无法将行移动到另一个分区。

最后，PostgreSQL 11中的另一个的新功能，这次由Jeevan Ladhe，Beena Emerson，Ashutosh Bapat，Rahila Syed和Robert Haas实现，支持分区表中的默认分区：即接收所有不适合任何常规分区行的分区。然而，虽然在表面上很好，但这个功能在生产设置上不是很方便，因为一些操作会在默认分区产生更严格的锁。例如：创建新分区需要扫描默认分区，以确定没有现有行与新分区的边界匹配。也许在将来这些锁会降低，但现在还是建议不要使用它。

##  2. 更好的DDL支持

在PostgreSQL 10中，某些DDL语句不能应用于分区表，需要单独处理每个分区。在PostgreSQL 11中，已经解决了一些限制，正如Simon Riggs先前所宣布的那样。首先，现在可以在分区表上使用CREATE INDEX。这可以减少重复性工作，不用为每个分区重复命令（并确保永远不会漏掉每个新分区），只需要为分区表执行一次，它会自动应用到所有分区。

另一件重要的功能是匹配分区中的现有索引。众所周知，创建索引会发生阻塞，因此花费的时间越少越好。此功能将分区中的现有索引与正在创建的索引进行比较，如果存在匹配，则无需扫描分区以创建新索引，将使用现有索引。

与此同时，也可以创建UNIQUE约束以及PRIMARY KEY约束。两个注意事项：首先，分区键必须是主键的一部分。这允许在每个分区本地完成唯一性检查，从而避免全局索引。其次，不能有外键引用这些主键。

另外，现在可以在分区表上创建FOR EACH ROW触发器，并将其应用于所有分区。同时，这将造成分区表具有延迟的唯一约束。一个注意事项：只允许AFTER触发器，直到弄清楚如何处理将行移动到不同分区的BEFORE触发器。

最后，分区表可以具有FOREIGN KEY约束。这对于分割大型事实表非常方便，同时避免了悬空引用（“dangling references”）。

## 3. 工作性能

之前，预处理查询以找出不扫描哪些分区（约束排除）是过度简化和缓慢的。现在这一点改善了，引入了“faster pruning”和基于它的“runtime pruning”。结果更完善，速度也更快（David Rowley在之前的文章中已经对此进行了描述。）在完成所有这些工作之后，在查询生命周期的三个点应用分区修剪：

​     （1）在查询计划时
​     （2）收到查询参数后
​     （3）在一个查询节点将值作为参数传递给另一个节点时

原始系统只能在查询计划时应用，现在系统有了显著改进。

可以通过在关闭enable_partition_pruning选项之前和之后比较查询的EXPLAIN输出来查看此功能。一个非常简单的例子，比较有没有pruning的执行计划：

### 没有pruning时:

```
SET enable_partition_pruning TO off;
EXPLAIN (ANALYZE, COSTS off) SELECT * FROM clientes WHERE cliente_id = 1234;
```

 

```
QUERY PLAN                                
-------------------------------------------------------------------------
 Append (actual time=6.658..10.549 rows=1 loops=1)
   ->  Seq Scan on clientes_1 (actual time=4.724..4.724 rows=0 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 24978
   ->  Seq Scan on clientes_00 (actual time=1.914..1.914 rows=0 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 12644
   ->  Seq Scan on clientes_2 (actual time=0.017..1.021 rows=1 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 12570
   ->  Seq Scan on clientes_3 (actual time=0.746..0.746 rows=0 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 12448
   ->  Seq Scan on clientes_01 (actual time=0.648..0.648 rows=0 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 12482
   ->  Seq Scan on clientes_4 (actual time=0.774..0.774 rows=0 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 12400
   ->  Seq Scan on clientes_5 (actual time=0.717..0.717 rows=0 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 12477
 Planning Time: 0.375 ms
 Execution Time: 10.603 ms
 
```

### 有pruning时：

```

EXPLAIN (ANALYZE, COSTS off) SELECT * FROM clientes WHERE cliente_id = 1234;
```

```
QUERY PLAN                               
----------------------------------------------------------------------
 Append (actual time=0.054..2.787 rows=1 loops=1)
   ->  Seq Scan on clientes_2 (actual time=0.052..2.785 rows=1 loops=1)
         Filter: (cliente_id = 1234)
         Rows Removed by Filter: 12570
 Planning Time: 0.292 ms
 Execution Time: 2.822 ms
```

通过仔细阅读回归测试预期文件，可以看到大量更复杂的示例。

另外，Ashutosh Bapat引入了分区连接。如果有两个分区表，并且它们以相同的方式分区，那么当它们被连接时，可以将一侧的每个分区连接到另一侧的匹配分区;这比将每个分区连接到另一侧的每个分区要好得多。分区方案需要精确匹配，这看起来用不到，但实际上有很多情况适用。例如：订单表及其对应的订单条目表。现在已经有很多工作来放宽这个限制。

最后，由Jeevan Chalke，Ashutosh Bapat和Robert Haas实现了分区聚合。此优化意味着可以通过分别聚合每个分区的行来执行包含GROUP BY子句中的分区键的聚合，这要快得多。


##  4. 结束思考

在一周年的重大发展之后，PostgreSQL有一个更引人注目的分区系统。虽然仍有许多需要改进，特别是需要提高涉及分区表的各种操作的性能和并发性，但现在“declarative partitioning”分区系统已成功服务于许多有重大价值的系统。在2ndQuadrant，我们将继续贡献代码来改进这个领域和其他领域的PostgreSQL，就像我们之前为每一个版本所做的那样。

 

 


