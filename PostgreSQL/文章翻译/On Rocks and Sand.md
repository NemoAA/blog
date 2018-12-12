# On Rocks and Sand

> 文章翻译自[On Rocks and Sand](https://blog.2ndquadrant.com/on-rocks-and-sand/)

在规划数据库容量时，需要考虑很多，在这方面postgresql也是一样。需要调整的要素之一就是存储。然而在存储层面上有些隐藏列是被忽略掉的。

## 基本对齐

在大多数底层计算机语言(如C)中，数据类型按其最大的值进行寻址，而不管它们的实际大小如何。因此一个标准的32位整数可以存储超过20亿的值，但必须作为一个整体来读取。这意味着即使是0值也需要4个字节来存储。

此外，postgresql的设计使其内部自然对齐为8字节，这意味的某些情况下，不同大小的连续固定长度的列必须填充空字节。在这个例子中我们可以看到：

```sql
SELECT pg_column_size(ROW()) AS empty,        
	pg_column_size(ROW(0::SMALLINT)) AS byte2,        
	pg_column_size(ROW(0::BIGINT)) AS byte8,        
	pg_column_size(ROW(0::SMALLINT, 0::BIGINT)) AS byte16;    
	
empty | byte2 | byte8 | byte16
-------+-------+-------+--------     
24 |    26 |    32 |     40
```

这表明在postgresql中一个空行需要24字节的各种头部信息，`SMALLINT`列为2字节，`BIGINT`列为8字节，两种列组合在一起是16字节？这是为了为了对齐，postgresql总是填充较小的列来匹配后面列的大小。所以在这里不是2+8=10，而是8+8=16。

## 混乱的列排序

就其本身而言，这未必是一个问题。但是考虑一下这个个人订单表：

```sql
CREATE TABLE user_order (
    is_shipped    BOOLEAN NOT NULL DEFAULT FALSE,
    user_id       BIGINT NOT NULL,
    order_total   NUMERIC NOT NULL,
    order_dt      TIMESTAMPTZ NOT NULL,
    order_type    SMALLINT NOT NULL,
    ship_dt       TIMESTAMPTZ,
    item_ct       INT NOT NULL,
    ship_cost     NUMERIC,
    receive_dt    TIMESTAMPTZ,
    tracking_cd   TEXT,
    id            BIGSERIAL PRIMARY KEY NOT NULL );
```

表中列的顺序很奇怪。这种列顺序并不罕见，可能是由一个匆忙的开发人员简单的记下列属性或者ORM从一个任意散列键位置生成。在最后的id列是一个很好的指示，列顺序不是架构或者规划的一部分。

这就是postgresql所看到的：

```sql
SELECT a.attname, t.typname, t.typalign, t.typlen
	FROM pg_class c
	JOIN pg_attribute a ON (a.attrelid = c.oid)
	JOIN pg_type t ON (t.oid = a.atttypid)
	WHERE c.relname = 'user_order'    AND a.attnum >= 0
	ORDER BY a.attnum;

attname   |   typname   | typalign | typlen
-------------+-------------+----------+--------
is_shipped  | bool        | c        |      1
user_id     | int8        | d        |      8
order_total | NUMERIC     | i        |     -1
order_dt    | timestamptz | d        |      8
order_type  | int2        | s        |      2
ship_dt     | timestamptz | d        |      8
item_ct     | int4        | i        |      4
ship_cost   | NUMERIC     | i        |     -1
receive_dt  | timestamptz | d        |      8
tracking_cd | text        | i        |     -1
id          | int8        | d        |      8
```

 `typalign` 列中的值指的是预定的对齐类型。 [`pg_type`手册页](https://www.postgresql.org/docs/current/static/catalog-pg-type.html)。

从前面的讨论中，我们可以看到int类型可以映射到它们各自的字节大小。对于`NUMERIC`和`TEXT`情况就复杂些，我们以后需要解决这个问题。现在，考虑大小不变的转换以及可能对对齐产生的影响。

## 预估最少的填充空间

为了避免这种状况，postgresql对每个小列都进行填充，以匹配下一个连续列的大小。由于存在这种特殊的列排列，在每个列之间都会有少量的缓冲。

我们用一百万行的表进行测试并查看结果：

```sql
INSERT INTO user_order (
    is_shipped, user_id, order_total, order_dt, order_type,
    ship_dt, item_ct, ship_cost, receive_dt, tracking_cd
	) SELECT TRUE, 1000, 500.00, now() - INTERVAL '7 days',
	3, now() - INTERVAL '5 days', 10, 4.99,
	now() - INTERVAL '3 days', 'X5901324123479RROIENSTBKCV4'
	FROM generate_series(1, 1000000);

SELECT pg_relation_size('user_order') AS size_bytes, 
	pg_size_pretty(pg_relation_size('user_order')) AS size_pretty;

size_bytes | size_pretty
-----------+-------------
 141246464 | 135 MB
```

现在我们可以用它作为我们的基准值。下一个问题是：其中有多少是填充的？下面是我们根据各个列长度来对齐估计出的最少的浪费值(**注意 变长类型的必须至少为 4，因为它们需要包含一个 `int4`作为它们的第一个组成部分** )：

- 7 bytes between `is_shipped` and `user_id`
- 4 bytes between `order_total` and `order_dt`
- 6 bytes between `order_type` and `ship_dt`
- 4 bytes between `receive_dt` and `id`

因此，我们可能每行大约会损失21字节，声明的类型占实际空间的59个字节，没有行头部的话总行长度是80个字节。同样，这只是基于对齐存储。事实证明变长类型`NUMERIC`和`TEXT`列的总数要比对齐的多些。

如果实际我们非常接近这个估算值，意味着我们可以把表缩小26%，大约有37MB。

## 一些基本规则

执行这些操作的技巧就是获得理想的列对齐，从而使增加的字节数最少。要做到这一点我们需要考虑`NUMERIC`和`TEXT`类型的列，因为它们是可变类型的，会经过特殊的处理。举个例子：

```sql
SELECT pg_column_size(ROW()) AS empty_row,
	pg_column_size(ROW(0::NUMERIC)) AS no_val,
    pg_column_size(ROW(1::NUMERIC)) AS no_dec,
    pg_column_size(ROW(9.9::NUMERIC)) AS with_dec,
    pg_column_size(ROW(1::INT2, 1::NUMERIC)) AS col2,
    pg_column_size(ROW(1::INT4, 1::NUMERIC)) AS col4,
    pg_column_size(ROW(1::NUMERIC, 1::INT4)) AS round8;    
   
empty_row | no_val | no_dec | with_dec | col2 | col4 | round8
-----------+--------+--------+----------+------+------+--------
	24 |     27 |     29 |       31 |   31 |   33 |     36
```

这些结果表明，我们可以认为`NUMERIC`是未对齐的。但要注意，即使`NUMERIC`中有一个数字它也占5个字节，但它也不像INT8那样影响前一列。

下面是`TEXT`类型的：

```sql
SELECT pg_column_size(ROW()) AS empty_row,
	pg_column_size(ROW(''::TEXT)) AS no_text,
    pg_column_size(ROW('a'::TEXT)) AS min_text,
    pg_column_size(ROW(1::INT4, 'a'::TEXT)) AS two_col,
    pg_column_size(ROW('a'::TEXT, 1::INT4)) AS round4;    
   
empty_row | no_text | min_text | two_col | round4
-----------+---------+----------+---------+--------  
	24 |      25 |       26 |      30 |     32
```

从这我们可以看出可变长度列类型会根据下一列类型按接近4字节数进行调整。这意味着，除了在正确的边界处引入填充外，我们可以链接可变长度的列。因此，我们可以推断只要可变长度列位于列表的末尾就不会导致膨胀。

如果定长列类型根据下一列进行调整，这意味着最大的类型应该放在最前面。否则，我们可以“pack列，让连续列累计消耗8字节。

同样，我们可以看到它们的作用：

```sql
SELECT pg_column_size(ROW()) AS empty_row,
	pg_column_size(ROW(1::SMALLINT)) AS int2,
    pg_column_size(ROW(1::INT)) AS int4,
    pg_column_size(ROW(1::BIGINT)) AS int8,
    pg_column_size(ROW(1::SMALLINT, 1::BIGINT)) AS padded,
    pg_column_size(ROW(1::INT, 1::INT, 1::BIGINT)) AS not_padded; 

empty_row | int2 | int4 | int8 | padded | not_padded
-----------+------+------+------+--------+------------
24 |   26 |   28 |   32 |     40 |         40
```

## 新的列排序

前面给出的是一种奇特的说法“按照`pg_type`中定义的类型长度对列进行排序”。幸运的是，我们可以通过查询输出列类型来获得该信息:

```sql
SELECT a.attname, t.typname, t.typalign, t.typlen
	FROM pg_class c
	JOIN pg_attribute a ON (a.attrelid = c.oid)
	JOIN pg_type t ON (t.oid = a.atttypid)
	WHERE c.relname = 'user_order'    AND a.attnum >= 0
	ORDER BY t.typlen DESC;
	
attname   |   typname   | typalign | typlen
-------------+-------------+----------+--------
id          | int8        | d        |      8
user_id     | int8        | d        |      8
order_dt    | timestamptz | d        |      8
ship_dt     | timestamptz | d        |      8
receive_dt  | timestamptz | d        |      8
item_ct     | int4        | i        |      4
order_type  | int2        | s        |      2
is_shipped  | bool        | c        |      1
tracking_cd | text        | i        |     -1
ship_cost   | NUMERIC     | i        |     -1
order_total | NUMERIC     | i        |     -1
```

在相同的条件下，我们可以将列和类型长度进行匹配，如果我们希望得到更漂亮的排序，可以在必要时组合长度较短类型的列。

让我们看看如果我们使用这种设计的表怎么样：

```sql
DROP TABLE user_order;
CREATE TABLE user_order (
    id            BIGSERIAL PRIMARY KEY NOT NULL,
    user_id       BIGINT NOT NULL,
    order_dt      TIMESTAMPTZ NOT NULL,
    ship_dt       TIMESTAMPTZ,
    receive_dt    TIMESTAMPTZ,
    item_ct       INT NOT NULL,
    order_type    SMALLINT NOT NULL,
    is_shipped    BOOLEAN NOT NULL DEFAULT FALSE,
    order_total   NUMERIC NOT NULL,
    ship_cost     NUMERIC,
    tracking_cd   TEXT );
```

如果重复前面插入的100万行，新表大小为117,030,912字节，约为112 MB。通过简单地重新组织表列，我们节省了21%的空间。

这对单个表可能意义不大，但在数据库实例中的每个表都重复使用，可能使存储容量大幅度减少。在数据仓库环境中，数据通常只加载一次，以后再也不会修改，减少10%-20%的存储是值得考虑的，因为所涉及的规模很大。我看过60 TB Postgres数据库，想象一下在没有删除任何数据的情况下将其减少6-12TB。

## 解决差异

就像用石头、鹅卵石和沙子填充罐子一样，最好的定义Postgres表的方法就是使用列对齐类型。首先是较大的列，其次是中列，最后是小列，以及变长类型，如`NUMERIC`和`TEXT`类型，它们被放到了最后，它们就好像是灰尘一样。

就目前而言，表列的定义可能是这样的：

```sql
CREATE TABLE user_order (
    id            BIGSERIAL PRIMARY KEY NOT NULL,
    user_id       BIGINT NOT NULL,
    order_type    SMALLINT NOT NULL,
    order_total   NUMERIC NOT NULL,
    order_dt      TIMESTAMPTZ NOT NULL,
    item_ct       INT NOT NULL,
    ship_dt       TIMESTAMPTZ,
    is_shipped    BOOLEAN NOT NULL DEFAULT FALSE,
    ship_cost     NUMERIC,
    tracking_cd   TEXT,
    receive_dt    TIMESTAMPTZ );
```

此刻，恰巧比理想状态下大8MB，或者说比理想状态大7.7%。为了演示我们故意将列的顺序打乱。实际中的表可能位于最好和最坏的之间，而保证最小的唯一方法就是手动排序。

有人会问了，为什么不把它建在postgresql中呢。当然它知道理想的列排序并且有能力将用户的可见映射和实际磁盘映射分离出来。但这是一个很难回答并且会涉及很多bike-shedding。

将物理表示与逻辑表示分离的一个主要好处是Postgres将允许列重新排序，或者在指定位置添加列。如果用户希望经过多次修改后他们的列表看起来很漂亮，为什么不这么做呢？

这是因为关于优先权的问题。这至少可以追溯到2006年，有一个TODO项目来解决这个问题。从那以后补丁一直都会有，每次交流也得不到一个明确结论。显然这是个很难解决的问题，正如他们所说还有有更重要的事要做。

如果有足够的需求，有人会赞助一个补丁来完成，即使它需要多个Postgres版本去做必要的底层更改。在此之前，如果对特定用例的影响足够大，一个简单的查询可以神奇地显示理想的列排序。

对于那些喜欢这种底层调整的人，让我们知道这是否值得。我们很想听听你的故事！