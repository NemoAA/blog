# BRIN索引-概述

> [本章节翻译自](https://blog.anayrat.info/en/2016/04/19/brin-indexes-overview/)

2016年1月发布的9.5版的PostgreSQL提供了一种新的索引：`BRIN`索引（块范围索引）。它被推荐用于非常大并与物理位置相关的表。我决定发表关于该索引的一系列文章：

- [Brin索引-概述](http://blog.anayrat.info/2016/04/19/index-brin-principe/)
- [Brin索引-工作原理](http://blog.anayrat.info/2016/04/20/index-brin-fonctionnement/)
- [Brin索引-相关性](http://blog.anayrat.info/2016/04/20/index-brin-correlation/)
- [Brin索引-性能](http://blog.anayrat.info/2016/04/21/index-brin-performances/)

## 介绍

在物理层面，表是由包含元组的8k块组成。`BRIN`会去储存一个块范围内最大和最小值。如果您搜索的值不在范围内，就可以排除掉一组块。

注意：`BRIN`索引类似于Oracle的存储索引([Exadata存储索引](https://en.wikipedia.org/wiki/Block_Range_Index#Exadata_Storage_Indexe))。

以下是支持的类型： [内建运算符类](http://www.postgresql.org/docs/current/static/brin-builtin-opclasses.html#BRIN-BUILTIN-OPCLASSES-TABLE)

```
abstime
bigint
bit
bit varying
box
bytea
character
"char"
date
double precision
inet
inet
integer
interval
macaddr
name
numeric
pg_lsn
oid
any range type
real
reltime
smallint
text
tid
timestamp without time zone
timestamp with time zone
time without time zone
time with time zone
uuid
```

# BRIN索引 – 工作原理

> [本章节翻译自](https://blog.anayrat.info/2016/04/20/index-brin-fonctionnement/)

2016年1月发布的9.5版的PostgreSQL提供了一种新的索引：用于范围索引的`BRIN`索引。它被推荐用于非常大并与物理位置相关表。我决定发表关于该索引的一系列文章：

- [Brin索引-概述](http://blog.anayrat.info/2016/04/19/index-brin-principe/)
- [Brin索引-工作原理](http://blog.anayrat.info/2016/04/20/index-brin-fonctionnement/)
- [Brin索引-相关性](http://blog.anayrat.info/2016/04/20/index-brin-correlation/)
- [Brin索引-性能](http://blog.anayrat.info/2016/04/21/index-brin-performances/)

在第二篇文章中，我们将看到`BRIN`索引是如何工作的。

## 工作原理

该索引将包含在一组块的区间里最小和最大值：范围（在单列上的索引的情况下）。

默认范围的大小为128个块的区间。（128x8KB=>1MB）

例如，由每行加1的‘’id‘’列组成的100000行的表，这个表在物理层面是这样存储的（一个块可以包含几个元组）：

| Bloc | id    |
| ---- | ----- |
| 0    | 1     |
| 0    | 2     |
| …    | …     |
| 1    | 227   |
| …    | …     |
| 128  | 28929 |
| …    | …     |
| 255  | 57856 |
| 256  | 57857 |
| …    | …     |

```SQL
CREATE TABLE t1 (c1) AS (SELECT * FROM generate_series(1,100000));
SELECT ctid,c1 from t1;
```

如果我们在28929和57856之间搜索值，postgresql将会读取整张表。它不知道没必要在块128之前和块255之后读取。

第一反应就是创建一个`btree`索引。不需要详细说明，这种索引可以更有效的读取表。它存储了表中每个值的位置。

索引如下：

| id    | Location |
| ----- | -------- |
| 1     | 0        |
| 2     | 0        |
| …     |          |
| 227   | 1        |
| …     | …        |
| 57857 | 256      |

我们可以直观的看到，如果表很大，索引也会很大。

`BRIN`索引包含以下内容：

| Range (128 blocks) | min   | max    | allnulls | hasnulls |
| ------------------ | ----- | ------ | -------- | -------- |
| 1                  | 1     | 28928  | false    | false    |
| 2                  | 28929 | 57856  | false    | false    |
| 3                  | 57857 | 86784  | false    | false    |
| 4                  | 86785 | 115712 | false    | false    |

```SQL
create index ON t1 using brin(c1) ;
create extension pageinspect;
SELECT * FROM brin_page_items(get_raw_page('t1_c1_idx', 2), 't1_c1_idx');
```

因此，搜索28929到57856之间的值时，postgresql必须找128-255的块。

与`btree`相比，我们可以用4行代替B树种超过10万行的内容。当然现实情况中要复杂的多，然而这种简化已经描述了该索引的紧凑的特性。

## 范围大小的影响

默认的范围大小为128个块，也就是1M（1个块为8KB）。由于可以调整`pages_per_range`参数，我们可以使用不同大小的范围进行测试。

我们使用一个更大的数据，它有1亿行：

```SQL
CREATE TABLE brin_large (c1 INT);
INSERT INTO brin_large SELECT * FROM generate_series(1,100000000);
```

表的大小约为3.5G：

```SQL
\dt+ brin_large
                       List OF relations
 Schema |    Name    | TYPE  |  Owner   |  SIZE   | Description
--------+------------+-------+----------+---------+-------------
 public | brin_large | TABLE | postgres | 3458 MB |
```

启用psql “\timing” 选项来判断索引创建的时间。我们使用不同的`pages_per_range`的值来创建`BRIN`索引：

```SQL
CREATE INDEX brin_large_brin_idx ON brin_large USING brin (c1);
CREATE INDEX brin_large_brin_idx_8 ON brin_large USING brin (c1) WITH (pages_per_range = 8);
CREATE INDEX brin_large_brin_idx_16 ON brin_large USING brin (c1) WITH (pages_per_range = 16);
CREATE INDEX brin_large_brin_idx_32 ON brin_large USING brin (c1) WITH (pages_per_range = 32);
CREATE INDEX brin_large_brin_idx_64 ON brin_large USING brin (c1) WITH (pages_per_range = 64);
```

再创建一个`btree`索引：

```SQL
CREATE INDEX brin_large_btree_idx ON brin_large USING btree (c1);
```

比较大小：

```SQL
\di+ brin_large*
                                    List OF relations
 Schema |          Name          | TYPE  |  Owner   |   TABLE    |  SIZE   | Description
--------+------------------------+-------+----------+------------+---------+-------------
 public | brin_large_brin_idx    | INDEX | postgres | brin_large | 128 kB  |
 public | brin_large_brin_idx_16 | INDEX | postgres | brin_large | 744 kB  |
 public | brin_large_brin_idx_32 | INDEX | postgres | brin_large | 392 kB  |
 public | brin_large_brin_idx_64 | INDEX | postgres | brin_large | 216 kB  |
 public | brin_large_brin_idx_8  | INDEX | postgres | brin_large | 1448 kB |
 public | brin_large_btree_idx   | INDEX | postgres | brin_large | 2142 MB |
```

以下是创建索引的时间及其大小：

![Duration](https://blog.anayrat.info/img/2016/duration.png)

创建的速度更快。两种类型的索引之间有10倍的差距。测试的设备配置（笔记本电脑，机械硬盘）。我建议你用自己的设备进行测试。

注意我将`maintenance_work_mem`值设为1GB。虽然这个值很高，但这并不妨碍建立`btree`索引的临时文件。

![size](https://blog.anayrat.info/img/2016/size.png)

对于索引的大小，它们的差值更加重要，我用对数比例来表示差距。在`pages_per_range`为默认值时是128KB，而`btree`大于2GB！

查询如何呢？

让我们试试这个查询，它搜索10到2000之间的值。为了详细研究postgresql工作过程，我们将使用选项 (`ANALYZE`, `VERBOSE`, `BUFFERS`)来进行分析。

最后为了便于分析，我们将使用一个较小的表：

```SQL
CREATE TABLE brin_demo (c1 INT);
INSERT INTO brin_demo SELECT * FROM generate_series(1,100000);
EXPLAIN (ANALYZE,BUFFERS,VERBOSE) SELECT c1 FROM brin_demo WHERE c1> 1 AND c1<2000;
 QUERY PLAN
-------------------------------------------------------------------------------------------------------------------
 Seq Scan on public.brin_demo (cost=0.00..2137.47 rows=565 width=4) (actual time=0.010..11.311 rows=1998 loops=1)
 Output: c1
 Filter: ((brin_demo.c1 > 1) AND (brin_demo.c1 < 2000))
 Rows Removed by Filter: 98002
 Buffers: shared hit=443
 Planning time: 0.044 ms
 Execution time: 11.412 ms
```

没有索引时，postgresql将读取整张表（`seq`扫描）并读取443个块。

相同的查询使用`BRIN`索引：

```SQL
CREATE INDEX brin_demo_brin_idx ON brin_demo USING brin (c1);
EXPLAIN (ANALYZE,BUFFERS,VERBOSE) SELECT c1 FROM brin_demo WHERE c1> 1 AND c1<2000;
 QUERY PLAN
---------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on public.brin_demo (cost=17.12..488.71 rows=500 width=4) (actual time=0.034..3.483 rows=1998 loops=1)
 Output: c1
 Recheck Cond: ((brin_demo.c1 > 1) AND (brin_demo.c1 < 2000))
 Rows Removed by Index Recheck: 26930
 Heap Blocks: lossy=128
 Buffers: shared hit=130
 -> Bitmap Index Scan on brin_demo_brin_idx (cost=0.00..17.00 rows=500 width=0) (actual time=0.022..0.022 rows=1280 loops=1)
 Index Cond: ((brin_demo.c1 > 1) AND (brin_demo.c1 < 2000))
 Buffers: shared hit=2
 Planning time: 0.074 ms
 Execution time: 3.623 ms
```

postgresql从索引中读取2个块，然后在表中读取了128个块。

让我们尝试使用较小的`pages_per_range`，例如：

```SQL
CREATE INDEX brin_demo_brin_idx_16 ON brin_demo USING brin (c1) WITH (pages_per_range = 16);
EXPLAIN (ANALYZE,BUFFERS,VERBOSE) SELECT c1 FROM brin_demo WHERE c1> 10 AND c1<2000;
 QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on public.brin_demo (cost=17.12..488.71 rows=500 width=4) (actual time=0.053..0.727 rows=1989 loops=1)
 Output: c1
 Recheck Cond: ((brin_demo.c1 > 10) AND (brin_demo.c1 < 2000))
 Rows Removed by Index Recheck: 1627
 Heap Blocks: lossy=16
 Buffers: shared hit=18
 -> Bitmap Index Scan on brin_demo_brin_idx_16 (cost=0.00..17.00 rows=500 width=0) (actual time=0.033..0.033 rows=160 loops=1)
 Index Cond: ((brin_demo.c1 > 10) AND (brin_demo.c1 < 2000))
 Buffers: shared hit=2
 Planning time: 0.114 ms
 Execution time: 0.852 ms
```

同样postgresql从索引中读取了2个块，但是它只在表中读取了16个块。

当`pages_per_range`的值较小时，索引具有更大的选择性，读取的块也就更少。

使用`pageinspect`扩展来观察索引的内容：

```SQL
CREATE extension pageinspect;
SELECT * FROM brin_page_items(get_raw_page('brin_demo_brin_idx_16', 2),'brin_demo_brin_idx_16');
 itemoffset | blknum | attnum | allnulls | hasnulls | placeholder | value
------------+--------+--------+----------+----------+-------------+-------------------
 1 | 0 | 1 | f | f | f | {1 .. 3616}
 2 | 16 | 1 | f | f | f | {3617 .. 7232}
 3 | 32 | 1 | f | f | f | {7233 .. 10848}
 4 | 48 | 1 | f | f | f | {10849 .. 14464}
 5 | 64 | 1 | f | f | f | {14465 .. 18080}
 6 | 80 | 1 | f | f | f | {18081 .. 21696}
 7 | 96 | 1 | f | f | f | {21697 .. 25312}
 8 | 112 | 1 | f | f | f | {25313 .. 28928}
 9 | 128 | 1 | f | f | f | {28929 .. 32544}
 10 | 144 | 1 | f | f | f | {32545 .. 36160}
 11 | 160 | 1 | f | f | f | {36161 .. 39776}
 12 | 176 | 1 | f | f | f | {39777 .. 43392}
 13 | 192 | 1 | f | f | f | {43393 .. 47008}
 14 | 208 | 1 | f | f | f | {47009 .. 50624}
 15 | 224 | 1 | f | f | f | {50625 .. 54240}
 16 | 240 | 1 | f | f | f | {54241 .. 57856}
 17 | 256 | 1 | f | f | f | {57857 .. 61472}
 18 | 272 | 1 | f | f | f | {61473 .. 65088}
 19 | 288 | 1 | f | f | f | {65089 .. 68704}
 20 | 304 | 1 | f | f | f | {68705 .. 72320}
 21 | 320 | 1 | f | f | f | {72321 .. 75936}
 22 | 336 | 1 | f | f | f | {75937 .. 79552}
 23 | 352 | 1 | f | f | f | {79553 .. 83168}
 24 | 368 | 1 | f | f | f | {83169 .. 86784}
 25 | 384 | 1 | f | f | f | {86785 .. 90400}
 26 | 400 | 1 | f | f | f | {90401 .. 94016}
 27 | 416 | 1 | f | f | f | {94017 .. 97632}
 28 | 432 | 1 | f | f | f | {97633 .. 100000}
(28 lignes)

SELECT * FROM brin_page_items(get_raw_page('brin_demo_brin_idx', 2),'brin_demo_brin_idx');
 itemoffset | blknum | attnum | allnulls | hasnulls | placeholder | value
------------+--------+--------+----------+----------+-------------+-------------------
 1 | 0 | 1 | f | f | f | {1 .. 28928}
 2 | 128 | 1 | f | f | f | {28929 .. 57856}
 3 | 256 | 1 | f | f | f | {57857 .. 86784}
 4 | 384 | 1 | f | f | f | {86785 .. 100000}
(4 lignes)
```

可以发现，在brin_demo_brin_idx_16索引中，第一组块（0-15号块）中存在着我们的查询范围。跟默认范围的brin_demo_brin_idx相比每个区间拥有的块更少。在brin_demo_brin_idx索引中，我们的查询范围在第一组块（0-127号块），相比brin_demo_brin_idx_16索引每一个区间拥有的块更多。从而可以解释为什么在brin_demo_brin_idx_16有更多的区间。