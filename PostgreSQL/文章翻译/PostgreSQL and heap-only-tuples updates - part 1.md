# **PostgreSQL and heap-only-tuples updates - part 1**

> 文章翻译自[PostgreSQL and heap-only-tuples updates - part 1](https://blog.anayrat.info/en/2018/11/12/postgresql-and-heap-only-tuples-updates-part-1/)
>

这是一系列和11版本新特性有关的文章。

在开发这个版本的过程中，一个特性引起了我的注意。它可以在[发行说明](https://www.postgresql.org/docs/11/static/release-11.html)中找到。

> 当表达式的值不变时，允许对表达式索引进行heap-only-tuple (HOT)更新(Konstantin Knizhnik)。
>

我承认这不是很明确，这个特性需要一些关于postgres如何工作的知识，我将通过几篇文章来解释:

1. [MVCC如何工作的和更新heap-only-tuples](https://blog.anayrat.info/en/2018/11/12/postgresql-and-heap-only-tuples-updates-part-1/1)

2. [什么时候postgres不使用heap-only-tuples更新和v11中新特性的介绍](https://blog.anayrat.info/en/2018/11/12/postgresql-and-heap-only-tuples-updates-part-1/2)

3. 对性能的影响

**这个特性在11.1被禁用,因为它可能导致实例崩溃。我之所以选择发表这些文章，是因为它们有助于理解HOT更新的机制以及这个特性可能带来的好处。**

## **MVCC机制 **

由于[MVCC](Multiversion_concurrency_control), postgres不会直接更新一行，而是复制该行并提供可见性信息。为什么会这样呢?

在使用关系型数据库时，需要考虑一个关键组成部分:并发性。我们正在编辑的行可能被先前的事务使用，例如正在进行的备份。为此，关系型数据库采用了不同的技术:

- 修改行并且把以前的版本存储在另一个地方，例如`oracle`的`undo`日志


- 复制行并且储存哪些行可以被哪些事务可见的信息，这就需要清理机制去清理掉那些不被任何事务可见的行。这是Postgres中的实现，`vacuum`负责执行这项清理。


让我们以一个非常简单的表为例，使用`pageinspect`扩展，看看它的内容如何演变:

```sql
CREATE TABLE t2(c1 int);
INSERT INTO t2 VALUES (1);
SELECT lp,t_data FROM  heap_page_items(get_raw_page('t2',0));

 lp |   t_data   
----+------------  
  1 | \x01000000

(1 row)

UPDATE t2 SET c1 = 2 WHERE c1 = 1;
SELECT lp,t_data FROM  heap_page_items(get_raw_page('t2',0));

 lp |   t_data   
----+------------  
  1 | \x01000000

  2 | \x02000000

(2 rows)

VACUUM t2;
SELECT lp,t_data FROM  heap_page_items(get_raw_page('t2',0));

 lp |   t_data   
----+------------ 
  1 |

  2 | \x02000000

(2 rows)
```

我们可以看到引擎给这一行做了一个副本并且`vacuum`清理了这个位置以供将来使用

## **heap-only-tuple 机制**

我们来看看另外一种情况，可能会有些复杂。一个两列的表，其中一列上建索引：

```sql
CREATE TABLE t3(c1 int,c2 int);
CREATE INDEX ON t3(c1);
INSERT INTO t3(c1,c2) VALUES (1,1);
INSERT INTO t3(c1,c2) VALUES (2,2);
SELECT ctid,* FROM t3;
 ctid  | c1 | c2
-------+----+----
 (0,1) |  1 |  1
 (0,2) |  2 |  2
(2 rows)
```

我们同样去用`pageinspect`看一下数据页上的内容：

```sql
SELECT * FROM  bt_page_items(get_raw_page('t3_c1_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars |          data           
------------+-------+---------+-------+------+-------------------------
          1 | (0,1) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          2 | (0,2) |      16 | f     | f    | 02 00 00 00 00 00 00 00
(2 rows)
```

目前，我的表非常简单，只有两个记录，索引也包含两个记录指向表(`ctid`列)中的相应块。如果我更新列c1，例如使用新值3，则必须更新索引。现在，如果我更新c2列。c1上的索引会更新吗?乍一看，我们可能会说不，因为c1是不变的。但是由于上面给出的`MVCC`模型，理论上来说，答案是肯定的:我们刚刚看到postgres会给这行做个副本，所以它的物理位置会不同(下一个`ctid`是(0,3))。

让我们来看看:

```sql
UPDATE t3 SET c2 = 3 WHERE c1=1;
SELECT lp,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp |       t_data       | t_ctid
----+--------------------+--------
  1 | \x0100000001000000 | (0,3)
  2 | \x0200000002000000 | (0,2)
  3 | \x0100000003000000 | (0,3)
(3 rows)


SELECT * FROM  bt_page_items(get_raw_page('t3_c1_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars |          data           
------------+-------+---------+-------+------+-------------------------
          1 | (0,1) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          2 | (0,2) |      16 | f     | f    | 02 00 00 00 00 00 00 00
(2 rows)
```

看表的物理块信息证明那一行确实有个副本，通过仔细观察字段`t_date`,我们可以看出新增了一个t_data。当我们看索引块的时候，就会发现内容没变，如果我要查c1=1的行，索引会把我指向旧的记录（0,1）！这是什么情况？

实际上，这就是我们要谈的特殊机制：`heap-only-tuplealias` （HOT）。当一个列被更新时，如果没有索引指向该列并且记录可以插入到同一个块中，Postgres只会在旧记录和新记录之间创建一个指针。

这样的话postgres就避免了更新索引，这意味着：

- 避免了读写操作
- 减少索引碎片（旧索引的位置是很难再利用的）

如果查看表块，第一行的`ctid`指向(0,3)。如果再次更新该行，表的第一行将指向行(0.3)，而行(0.3)将指向(0.4)，从而形成所谓的链。`vacuum` 可以清理空闲空间，但总是保持指向最后一次记录的第一行。

当改变一行的时候索引并没有改变：

```sql
UPDATE t3 SET c2 = 4 WHERE c1=1;
SELECT * FROM  bt_page_items(get_raw_page('t3_c1_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars |          data           
------------+-------+---------+-------+------+-------------------------
          1 | (0,1) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          2 | (0,2) |      16 | f     | f    | 02 00 00 00 00 00 00 00
(2 rows)

SELECT lp,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp |       t_data       | t_ctid
----+--------------------+--------
  1 | \x0100000001000000 | (0,3)
  2 | \x0200000002000000 | (0,2)
  3 | \x0100000003000000 | (0,4)
  4 | \x0100000004000000 | (0,4)
(4 rows)
```

`Vacuum`清理可用的空间后：

```sql
VACUUM t3;
SELECT lp,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp |       t_data       | t_ctid
----+--------------------+--------
  1 |                    |
  2 | \x0200000002000000 | (0,2)
  3 |                    |
  4 | \x0100000004000000 | (0,4)
(4 rows)
```

再次更新将重用第二个位置，索引将保持不变。查看`t_ctid`的值:

```sql
UPDATE t3 SET c2 = 5 WHERE c1=1;
SELECT lp,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp |       t_data       | t_ctid
----+--------------------+--------
  1 |                    |
  2 | \x0200000002000000 | (0,2)
  3 | \x0100000005000000 | (0,3)
  4 | \x0100000004000000 | (0,3)
(4 rows)


SELECT * FROM  bt_page_items(get_raw_page('t3_c1_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars |          data           
------------+-------+---------+-------+------+-------------------------
          1 | (0,1) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          2 | (0,2) |      16 | f     | f    | 02 00 00 00 00 00 00 00
(2 rows)
```

第一行是空的，postgres重用了第三个位置?

事实上，信息不会出现在`pageinspect`中。让我们直接用`pg_filedump`来读取代码块:

**注意:必须首先请求一个检查点，否则块可能还没有写入磁盘。**

```shell
pg_filedump  11/main/base/16606/8890510

*******************************************************************
* PostgreSQL File/Block Formatted Dump Utility - Version 10.1
*
* File: 11/main/base/16606/8890510
* Options used: None
*
* Dump created on: Sun Sep  2 13:09:53 2018
*******************************************************************

Block    0 ********************************************************
<Header> -----
 Block Offset: 0x00000000         Offsets: Lower      40 (0x0028)
 Block: Size 8192  Version    4            Upper    8096 (0x1fa0)
 LSN:  logid     52 recoff 0xc39ea148      Special  8192 (0x2000)
 Items:    4                      Free Space: 8056
 Checksum: 0x0000  Prune XID: 0x0000168b  Flags: 0x0001 (HAS_FREE_LINES)
 Length (including item array): 40

<Data> ------
 Item   1 -- Length:    0  Offset:    4 (0x0004)  Flags: REDIRECT
 Item   2 -- Length:   32  Offset: 8160 (0x1fe0)  Flags: NORMAL
 Item   3 -- Length:   32  Offset: 8096 (0x1fa0)  Flags: NORMAL
 Item   4 -- Length:   32  Offset: 8128 (0x1fc0)  Flags: NORMAL
```

第一行包含标志:重定向。这表示这行对应HOT重定向。这在`src/include/storage/itemid.h`中有记录：

```shell
/*
 * lp_flags has these possible states.  An UNUSED line pointer is available     
 * for immediate re-use, the other states are not.                              
 */                                                                             
#define LP_UNUSED       0       /* unused (should always have lp_len=0) */      
#define LP_NORMAL       1       /* used (should always have lp_len>0) */        
#define LP_REDIRECT     2       /* HOT redirect (should have lp_len=0) */       
#define LP_DEAD         3       /* dead, may or may not have storage */  
```

实际上，我们也可以通过`pageinspect`的`lp_flags`列看到：

```sql
SELECT lp,lp_flags,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp | lp_flags |       t_data       | t_ctid
----+----------+--------------------+--------
  1 |        2 |                    |
  2 |        1 | \x0200000002000000 | (0,2)
  3 |        1 | \x0100000005000000 | (0,3)
  4 |        1 | \x0100000004000000 | (0,3)
(4 rows)
```

如果我们再做一次更新、`vacuum`，`checkpoint`把块写到磁盘上：

```shell
SELECT lp,lp_flags,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp | lp_flags |       t_data       | t_ctid
----+----------+--------------------+--------
  1 |        2 |                    |
  2 |        1 | \x0200000002000000 | (0,2)
  3 |        0 |                    |
  4 |        0 |                    |
  5 |        1 | \x0100000006000000 | (0,5)
(5 rows)

CHECKPOINT;

pg_filedump  11/main/base/16606/8890510

*******************************************************************
* PostgreSQL File/Block Formatted Dump Utility - Version 10.1
*
* File: 11/main/base/16606/8890510
* Options used: None
*
* Dump created on: Sun Sep  2 13:16:12 2018
*******************************************************************

Block    0 ********************************************************
<Header> -----
 Block Offset: 0x00000000         Offsets: Lower      44 (0x002c)
 Block: Size 8192  Version    4            Upper    8128 (0x1fc0)
 LSN:  logid     52 recoff 0xc39ea308      Special  8192 (0x2000)
 Items:    5                      Free Space: 8084
 Checksum: 0x0000  Prune XID: 0x00000000  Flags: 0x0005 (HAS_FREE_LINES|ALL_VISIBLE)
 Length (including item array): 44

<Data> ------
 Item   1 -- Length:    0  Offset:    5 (0x0005)  Flags: REDIRECT
 Item   2 -- Length:   32  Offset: 8160 (0x1fe0)  Flags: NORMAL
 Item   3 -- Length:    0  Offset:    0 (0x0000)  Flags: UNUSED
 Item   4 -- Length:    0  Offset:    0 (0x0000)  Flags: UNUSED
 Item   5 -- Length:   32  Offset: 8128 (0x1fc0)  Flags: NORMAL


*** End of File Encountered. Last Block Read: 0 ***
```

Postgres保留了第一行(标志重定向)，并在位置5处写入了新行。

然而，有一些特殊情况postgres不能用这些机制：

- 当一个数据块上没有多余的空间要写到另一个块上的时候，我们可以推断，表的碎片化在这里对HOT是有用的。
- 当索引在要更新的列上的时候,在这种情况下postgres必须更新索引。Postgres可以通过对新值和前一个值进行二进制比较来检测是否发生了更改。

在下一篇文章中，我们将看到postgres不能使用HOT机制的示例。然后是版本11的新特性，postgres可以使用这种机制。