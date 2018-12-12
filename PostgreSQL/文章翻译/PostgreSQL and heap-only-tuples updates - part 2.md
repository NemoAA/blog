# **PostgreSQL and heap-only-tuples updates - part 2**

> 文章翻译自[postgresql-and-heap-only-tuples-updates-part-2/](https://blog.anayrat.info/en/2018/11/19/postgresql-and-heap-only-tuples-updates-part-2/)

这一系列文章将以11版本的新特性作为焦点。

在开发这个版本的过程中，一个特性引起了我的注意。它可以在[发行说明](https://www.postgresql.org/docs/11/static/release-11.html)中找到。

> 当表达式的值不变时，允许对表达式索引进行heap-only-tuple (HOT)更新(Konstantin Knizhnik)。

我承认这不是很明确，这个特性需要一些关于postgres如何工作的知识，我将通过几篇文章来解释:

1. [MVCC如何工作的和更新heap-only-tuples](https://blog.anayrat.info/en/2018/11/12/postgresql-and-heap-only-tuples-updates-part-1/1)
2. [什么时候postgres不使用heap-only-tuples更新和v11中新特性的介绍](https://blog.anayrat.info/en/2018/11/12/postgresql-and-heap-only-tuples-updates-part-1/2)
3. 对性能的影响

**这个特性在11.1版本中被禁用,因为它可能导致实例崩溃。我之所以选择发表这些文章，是因为它们有助于理解HOT更新的机制以及这个特性可能带来的好处。**

在上一篇文章中演示了`heap-only-tuple`机制，在这一篇中，我们将会看到Postgres什么时候不会去执行`heap-only-tuple`更新，这样我们就能够接近11版本该有的功能。

## **在更新列上有索引的案例 **

我们可以在以前例子的基础上增加一个新的索引列：

```
ALTER TABLE t3 ADD COLUMN c3 int;
CREATE INDEX ON t3(c3);
```

以前的更新是在一个没有索引的列上，如果更新c3列会怎么样儿呢？

先看一下执行更新之前的表和索引：

```
SELECT lp,lp_flags,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp | lp_flags |       t_data       | t_ctid
----+----------+--------------------+--------
  1 |        2 |                    |
  2 |        1 | \x0200000002000000 | (0,2)
  3 |        0 |                    |
  4 |        0 |                    |
  5 |        1 | \x0100000006000000 | (0,5)
(5 rows)

SELECT * FROM  bt_page_items(get_raw_page('t3_c1_idx',1));              
 itemoffset | ctid  | itemlen | nulls | vars |          data
------------+-------+---------+-------+------+-------------------------
          1 | (0,1) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          2 | (0,2) |      16 | f     | f    | 02 00 00 00 00 00 00 00
(2 rows)

SELECT * FROM  bt_page_items(get_raw_page('t3_c3_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars | data
------------+-------+---------+-------+------+------
          1 | (0,1) |      16 | t     | f    |
          2 | (0,2) |      16 | t     | f    |
(2 rows)
```

我们可以看到表没有变化，因为现在列c3还是空的，我们可以通过查看索引`t3_c3_idx`来看到这一点，它每一行都显示空，这是正确的。

```
UPDATE t3 SET c3 = 7 WHERE c1=1;
SELECT * FROM  bt_page_items(get_raw_page('t3_c3_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars |          data
------------+-------+---------+-------+------+-------------------------
          1 | (0,3) |      16 | f     | f    | 07 00 00 00 00 00 00 00
          2 | (0,1) |      16 | t     | f    |
          3 | (0,2) |      16 | t     | f    |
(3 rows)

SELECT lp,lp_flags,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp | lp_flags |           t_data           | t_ctid
----+----------+----------------------------+--------
  1 |        2 |                            |
  2 |        1 | \x0200000002000000         | (0,2)
  3 |        1 | \x010000000600000007000000 | (0,3)
  4 |        0 |                            |
  5 |        1 | \x0100000006000000         | (0,3)
(5 rows)

SELECT * FROM  bt_page_items(get_raw_page('t3_c1_idx',1));              
 itemoffset | ctid  | itemlen | nulls | vars |          data
------------+-------+---------+-------+------+-------------------------
          1 | (0,3) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          2 | (0,1) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          3 | (0,2) |      16 | f     | f    | 02 00 00 00 00 00 00 00
(3 rows)
```

我们注意到c3的索引中出现了新条目，而且表里也确实有了新记录，索引`t3_c1_idx`也被更新。这样即使c1列中的值没有改变，也导致添加了第三个条目。 

执行`vacuum`后：

```sql
VACUUM t3;
SELECT * FROM  bt_page_items(get_raw_page('t3_c1_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars |          data
------------+-------+---------+-------+------+-------------------------
          1 | (0,3) |      16 | f     | f    | 01 00 00 00 00 00 00 00
          2 | (0,2) |      16 | f     | f    | 02 00 00 00 00 00 00 00
(2 rows)

SELECT lp,lp_flags,t_data,t_ctid FROM  heap_page_items(get_raw_page('t3',0));
 lp | lp_flags |           t_data           | t_ctid
----+----------+----------------------------+--------
  1 |        0 |                            |
  2 |        1 | \x0200000002000000         | (0,2)
  3 |        1 | \x010000000600000007000000 | (0,3)
  4 |        0 |                            |
  5 |        0 |                            |
(5 rows)

SELECT * FROM  bt_page_items(get_raw_page('t3_c3_idx',1));
 itemoffset | ctid  | itemlen | nulls | vars |          data
------------+-------+---------+-------+------+-------------------------
          1 | (0,3) |      16 | f     | f    | 07 00 00 00 00 00 00 00
          2 | (0,2) |      16 | t     | f    |
(2 rows)
```

可以看到Postgres清理了表和索引，表的第一行不再有`REDIRECT`标志。

## **11版本新特性：**heap-only-tuple (HOT) 和函数索引

当修改有函数索引的列时，尽管该列被更新，但是表达式的结果也可能保持不变。因此，索引中的关键字将保持不变。

举个例子: 一个函数索引在一个`JSON`对象的特定键上。 

```
CREATE TABLE t4 (c1 jsonb, c2 int,c3 int);
CREATE INDEX ON t4 ((c1->>'prenom')) ;
CREATE INDEX ON t4 (c2);
INSERT INTO t4 VALUES ('{ "prenom":"adrien" , "ville" : "valence"}'::jsonb,1,1);
INSERT INTO t4 VALUES ('{ "prenom":"guillaume" , "ville" : "lille"}'::jsonb,2,2);


-- change that does not concern the first name, we change only the city
UPDATE t4 SET c1 = '{"ville": "valence (#soleil)", "prenom": "guillaume"}' WHERE c2=2;
SELECT pg_stat_get_xact_tuples_hot_updated('t4'::regclass);
 pg_stat_get_xact_tuples_hot_updated
-------------------------------------
                                   0
(1 row)

UPDATE t4 SET c1 = '{"ville": "nantes", "prenom": "guillaume"}' WHERE c2=2;
SELECT pg_stat_get_xact_tuples_hot_updated('t4'::regclass);
 pg_stat_get_xact_tuples_hot_updated
-------------------------------------
                                   0
(1 row)
```

函数`pg_stat_get_get_xact_tuples_hot_updated` 指出由HOT机制更新的行数。

这两个更新都只改变了 “city” 键而不是 “first name” 键。这将不会导致索引的修改因为索引只在“first name” 键上。

Postgres不会去做HOT。实际上对他来说，只要在列上更新，索引就必须更新。

在11版本中，postgres能够看到表达式的结果不会改变。我们在11版本上做了同样的测试: 

```
CREATE TABLE t4 (c1 jsonb, c2 int,c3 int);
-- CREATE INDEX ON t4 ((c1->>'prenom'))  WITH (recheck_on_update='false');
CREATE INDEX ON t4 ((c1->>'prenom')) ;
CREATE INDEX ON t4 (c2);
INSERT INTO t4 VALUES ('{ "prenom":"adrien" , "ville" : "valence"}'::jsonb,1,1);
INSERT INTO t4 VALUES ('{ "prenom":"guillaume" , "ville" : "lille"}'::jsonb,2,2);


-- changement qui ne porte pas sur prenom
UPDATE t4 SET c1 = '{"ville": "valence (#soleil)", "prenom": "guillaume"}' WHERE c2=2;
SELECT pg_stat_get_xact_tuples_hot_updated('t4'::regclass);
 pg_stat_get_xact_tuples_hot_updated
-------------------------------------
                                   1
(1 row)

UPDATE t4 SET c1 = '{"ville": "nantes", "prenom": "guillaume"}' WHERE c2=2;
SELECT pg_stat_get_xact_tuples_hot_updated('t4'::regclass);
 pg_stat_get_xact_tuples_hot_updated
-------------------------------------
                                   2
(1 row)
```

这一次，Postgres正确使用了HOT机制。可以通过查看索引的物理内容来验证这一点: 

10版本：

```
SELECT * FROM  bt_page_items(get_raw_page('t4_expr_idx',1));
itemoffset | ctid  | itemlen | nulls | vars |                      data                       
------------+-------+---------+-------+------+-------------------------------------------------
         1 | (0,1) |      16 | f     | t    | 0f 61 64 72 69 65 6e 00
         2 | (0,4) |      24 | f     | t    | 15 67 75 69 6c 6c 61 75 6d 65 00 00 00 00 00 00
         3 | (0,3) |      24 | f     | t    | 15 67 75 69 6c 6c 61 75 6d 65 00 00 00 00 00 00
         4 | (0,2) |      24 | f     | t    | 15 67 75 69 6c 6c 61 75 6d 65 00 00 00 00 00 00
(4 rows)
```

11版本：

```
SELECT * FROM  bt_page_items(get_raw_page('t4_expr_idx',1));
itemoffset | ctid  | itemlen | nulls | vars |                      data
------------+-------+---------+-------+------+-------------------------------------------------
         1 | (0,1) |      16 | f     | t    | 0f 61 64 72 69 65 6e 00
         2 | (0,2) |      24 | f     | t    | 15 67 75 69 6c 6c 61 75 6d 65 00 00 00 00 00 00
(2 rows)
```

当创建索引`recheck_on_update`时，这种行为可以由一个新的选项来控制。 

在默认情况下，postgres检查表达式的结果来执行HOT更新。如果碰巧表达式的结果在更新过程中发生变化，那样它就可以被设置为off，这样可以避免不必要地执行表达式。 

也可以注意到，如果开销大于1000,postgres避免评估表达式。 

在第三也就是最后一篇文章中，我们将看到一个更具体的案例来衡量对性能和容量的影响。 