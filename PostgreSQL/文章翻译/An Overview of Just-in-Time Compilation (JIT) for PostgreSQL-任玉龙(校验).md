# An Overview of Just-in-Time Compilation (JIT) for PostgreSQL

> 文章翻译自<https://severalnines.com/blog/overview-just-time-compilation-jit-postgresql>

从历史上看，PostgreSQL以预先编译PL/pgSQL函数的形式提供了编译特性，version 10引入了表达式编译。但是这些都不能生成机器码。

SQL的JIT在很多年前就已经讨论过了，而对于PostgreSQL的特性则是大量代码更改的结果。

要检查PostgreSQL是否支持使用LLVM，请使用pg_configure命令查看编译参数，并在输出中查找-with-llvm。PGDG RPM分布示例:

```
omiday ~ $ /usr/pgsql-11/bin/pg_config --configure
'--enable-rpath' '--prefix=/usr/pgsql-11' '--includedir=/usr/pgsql-11/include' '--mandir=/usr/pgsql-11/share/man' '--datadir=/usr/pgsql-11/share' '--enable-tap-tests' '--with-icu' '--with-llvm' '--with-perl' '--with-python' '--with-tcl' '--with-tclconfig=/usr/lib64' '--with-openssl' '--with-pam' '--with-gssapi' '--with-includes=/usr/include' '--with-libraries=/usr/lib64' '--enable-nls' '--enable-dtrace' '--with-uuid=e2fs' '--with-libxml' '--with-libxslt' '--with-ldap' '--with-selinux' '--with-systemd' '--with-system-tzdata=/usr/share/zoneinfo' '--sysconfdir=/etc/sysconfig/pgsql' '--docdir=/usr/pgsql-11/doc' '--htmldir=/usr/pgsql-11/doc/html' 'CFLAGS=-O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1 -specs=/usr/lib/rpm/redhat/redhat-annobin-cc1 -m64 -mtune=generic -fasynchronous-unwind-tables -fstack-clash-protection -fcf-protection' 'PKG_CONFIG_PATH=:/usr/lib64/pkgconfig:/usr/share/pkgconfig'
```

## Why LLVM JIT?

正如Adres Freund在他的文章中所解释的，这一切大约始于两年前，当时表达式求值和元组变形被证明是加速大型查询的障碍。在添加JIT实现之后，用Andres的话说，“表达式求值本身比以前快十倍以上”。此外，文章结尾的Q&A部分解释了LLVM是优于其他实现的选择。

当LLVM是选择的程序时，GUC参数jit_provider可以用来指向另一个JIT程序。请注意，由于构建过程的工作方式，内联支持仅在使用LLVM提供程序时可用。

## When to JIT?

文档写的很清楚:受CPU限制的长时间运行的查询将受益于JIT编译。此外，本博客中引用的邮件列表讨论指出，对于只执行一次的查询来说，JIT的开销太大了。

与编程语言相比，PostgreSQL的优势是通过依赖查询规划器知道什么时候应该使用JIT。为此，引入了一些GUC参数。为了保护用户在启用JIT时不受负面意外的影响，故意将成本相关的参数设置为合理的高值。请注意，将JIT成本参数设置为“0”将强制所有查询都是JIT编译的，从而减慢所有查询的速度。

尽管JIT通常是有益的，但是在启用它的情况下，也有一些情况是有害的，如 [commit b9f2d4d3](https://www.postgresql.org/message-id/20180914222657.mw25esrzbcnu6qlu@alap3.anarazel.de)中所讨论的。

## How to JIT?

如上所述，RPM二进制包支持llvm。然而，为了让JIT编译正常工作，还需要一些额外的步骤:

即:

```
postgres@[local]:54311 test# show server_version;
server_version
----------------
11.1
(1 row)
postgres@[local]:54311 test# show port;
port
-------
54311
(1 row)
postgres@[local]:54311 test# create table t1 (id serial);
CREATE TABLE
postgres@[local]:54311 test# insert INTO t1 (id) select * from generate_series(1, 10000000);
INSERT 0 10000000
postgres@[local]:54311 test# set jit = 'on';
SET
postgres@[local]:54311 test# set jit_above_cost = 10; set jit_inline_above_cost = 10; set jit_optimize_above_cost = 10;
SET
SET
SET
postgres@[local]:54311 test# explain analyze select count(*) from t1;
                                                               QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------------
Finalize Aggregate  (cost=97331.43..97331.44 rows=1 width=8) (actual time=647.585..647.585 rows=1 loops=1)
   ->  Gather  (cost=97331.21..97331.42 rows=2 width=8) (actual time=647.484..649.059 rows=3 loops=1)
         Workers Planned: 2
         Workers Launched: 2
         ->  Partial Aggregate  (cost=96331.21..96331.22 rows=1 width=8) (actual time=640.995..640.995 rows=1 loops=3)
               ->  Parallel Seq Scan on t1  (cost=0.00..85914.57 rows=4166657 width=0) (actual time=0.060..397.121 rows=3333333 loops=3)
Planning Time: 0.182 ms
Execution Time: 649.170 ms
(8 rows)
```
请注意，我确实启用了JIT(在[commit b9f2d4d3](https://www.postgresql.org/message-id/20180914222657.mw25esrzbcnu6qlu@alap3.anarazel.de)中引用的pgsql-hacker讨论之后，默认情况下禁用了JIT)。我还按照文档的建议调整了JIT参数的成本。

第一个提示在jit文档中引用的src/backend/jit/README文件中:

```
Which shared library is loaded is determined by the jit_provider GUC, defaulting to "llvmjit".
```

由于RPM包并不是自动引入JIT依赖项的——这是在深入讨论之后决定的(参见完整的线程)——我们需要手动安装它:

```
[root@omiday ~]# dnf install postgresql11-llvmjit
```

一旦安装完成，我们可以立即测试:

```
postgres@[local]:54311 test# explain analyze select count(*) from t1;
                                                               QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------------
Finalize Aggregate  (cost=97331.43..97331.44 rows=1 width=8) (actual time=794.998..794.998 rows=1 loops=1)
   ->  Gather  (cost=97331.21..97331.42 rows=2 width=8) (actual time=794.870..803.680 rows=3 loops=1)
         Workers Planned: 2
         Workers Launched: 2
         ->  Partial Aggregate  (cost=96331.21..96331.22 rows=1 width=8) (actual time=689.124..689.125 rows=1 loops=3)
               ->  Parallel Seq Scan on t1  (cost=0.00..85914.57 rows=4166657 width=0) (actual time=0.062..385.278 rows=3333333 loops=3)
Planning Time: 0.150 ms
JIT:
   Functions: 4
   Options: Inlining true, Optimization true, Expressions true, Deforming true
   Timing: Generation 2.146 ms, Inlining 117.725 ms, Optimization 47.928 ms, Emission 69.454 ms, Total 237.252 ms
Execution Time: 803.789 ms
(12 rows)
```

我们还可以显示JIT的详细信息:

```
postgres@[local]:54311 test# explain (analyze, verbose, buffers) select count(*) from t1;
                                                                  QUERY PLAN
------------------------------------------------------------------------------------------------------------------------------------------------
Finalize Aggregate  (cost=97331.43..97331.44 rows=1 width=8) (actual time=974.352..974.352 rows=1 loops=1)
   Output: count(*)
   Buffers: shared hit=2592 read=41656
   ->  Gather  (cost=97331.21..97331.42 rows=2 width=8) (actual time=974.166..980.942 rows=3 loops=1)
         Output: (PARTIAL count(*))
         Workers Planned: 2
         Workers Launched: 2
         JIT for worker 0:
         Functions: 2
         Options: Inlining true, Optimization true, Expressions true, Deforming true
         Timing: Generation 0.378 ms, Inlining 74.033 ms, Optimization 11.979 ms, Emission 9.470 ms, Total 95.861 ms
         JIT for worker 1:
         Functions: 2
         Options: Inlining true, Optimization true, Expressions true, Deforming true
         Timing: Generation 0.319 ms, Inlining 68.198 ms, Optimization 8.827 ms, Emission 9.580 ms, Total 86.924 ms
         Buffers: shared hit=2592 read=41656
         ->  Partial Aggregate  (cost=96331.21..96331.22 rows=1 width=8) (actual time=924.936..924.936 rows=1 loops=3)
               Output: PARTIAL count(*)
               Buffers: shared hit=2592 read=41656
               Worker 0: actual time=900.612..900.613 rows=1 loops=1
               Buffers: shared hit=668 read=11419
               Worker 1: actual time=900.763..900.763 rows=1 loops=1
               Buffers: shared hit=679 read=11608
               ->  Parallel Seq Scan on public.t1  (cost=0.00..85914.57 rows=4166657 width=0) (actual time=0.311..558.192 rows=3333333 loops=3)
                     Output: id
                     Buffers: shared hit=2592 read=41656
                     Worker 0: actual time=0.389..539.796 rows=2731662 loops=1
                     Buffers: shared hit=668 read=11419
                     Worker 1: actual time=0.082..548.518 rows=2776862 loops=1
                     Buffers: shared hit=679 read=11608
Planning Time: 0.207 ms
JIT:
   Functions: 9
   Options: Inlining true, Optimization true, Expressions true, Deforming true
   Timing: Generation 8.818 ms, Inlining 153.087 ms, Optimization 77.999 ms, Emission 64.884 ms, Total 304.787 ms
Execution Time: 989.360 ms
(36 rows)
```

JIT的实现还可以利用并行查询执行特性。举例来说，首先让我们禁用并行化:

```
postgres@[local]:54311 test# set max_parallel_workers_per_gather = 0;
SET
postgres@[local]:54311 test# explain analyze select count(*) from t1;
                                                      QUERY PLAN
----------------------------------------------------------------------------------------------------------------------
Aggregate  (cost=169247.71..169247.72 rows=1 width=8) (actual time=1447.315..1447.315 rows=1 loops=1)
   ->  Seq Scan on t1  (cost=0.00..144247.77 rows=9999977 width=0) (actual time=0.064..957.563 rows=10000000 loops=1)
Planning Time: 0.053 ms
JIT:
   Functions: 2
   Options: Inlining true, Optimization true, Expressions true, Deforming true
   Timing: Generation 0.388 ms, Inlining 1.359 ms, Optimization 7.626 ms, Emission 7.963 ms, Total 17.335 ms
Execution Time: 1447.783 ms
(8 rows)
```

相同的命令用并行查询，只需要一半的时间就能完成:

```
postgres@[local]:54311 test# reset max_parallel_workers_per_gather ;
RESET
postgres@[local]:54311 test# explain analyze select count(*) from t1;
                                                               QUERY PLAN
-----------------------------------------------------------------------------------------------------------------------------------------
Finalize Aggregate  (cost=97331.43..97331.44 rows=1 width=8) (actual time=707.126..707.126 rows=1 loops=1)
   ->  Gather  (cost=97331.21..97331.42 rows=2 width=8) (actual time=706.971..712.199 rows=3 loops=1)
         Workers Planned: 2
         Workers Launched: 2
         ->  Partial Aggregate  (cost=96331.21..96331.22 rows=1 width=8) (actual time=656.102..656.103 rows=1 loops=3)
               ->  Parallel Seq Scan on t1  (cost=0.00..85914.57 rows=4166657 width=0) (actual time=0.067..384.207 rows=3333333 loops=3)
Planning Time: 0.158 ms
JIT:
   Functions: 9
   Options: Inlining true, Optimization true, Expressions true, Deforming true
   Timing: Generation 3.709 ms, Inlining 142.150 ms, Optimization 50.983 ms, Emission 33.792 ms, Total 230.634 ms
Execution Time: 715.226 ms
(12 rows)
```

在JIT实现的初始阶段和最终版本中，我发现比较本文中讨论的测试结果很有趣。首先，确保原始测试的条件满足，即数据库必须有合适的内存:

```
postgres@[local]:54311 test# \l+
postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |                       | 8027 kB | pg_default | default administrative connection database
template0 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +| 7889 kB | pg_default | unmodifiable empty database
          |          |          |             |             | postgres=CTc/postgres |         |            |
template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +| 7889 kB | pg_default | default template for new databases
          |          |          |             |             | postgres=CTc/postgres |         |            |
test      | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |                       | 2763 MB | pg_default |
 
 
postgres@[local]:54311 test# show shared_buffers ;
3GB
 
Time: 0.485 ms
```

运行禁用JIT的测试:

```
postgres@[local]:54311 test# set jit = off;
SET
Time: 0.483 ms
 
postgres@[local]:54311 test# select sum(c8) from t1;
   0
 
Time: 1036.231 ms (00:01.036)
 
postgres@[local]:54311 test# select sum(c2), sum(c3), sum(c4), sum(c5),
   sum(c6), sum(c7), sum(c8) from t1;
   0 |   0 |   0 |   0 |   0 |   0 |   0
 
Time: 1793.502 ms (00:01.794)
```

接下来运行启用JIT的测试:

```
postgres@[local]:54311 test# set jit = on; set jit_above_cost = 10; set
jit_inline_above_cost = 10; set jit_optimize_above_cost = 10;
SET
Time: 0.473 ms
SET
Time: 0.267 ms
SET
Time: 0.204 ms
SET
Time: 0.162 ms
postgres@[local]:54311 test# select sum(c8) from t1;
   0
 
Time: 795.746 ms
 
postgres@[local]:54311 test# select sum(c2), sum(c3), sum(c4), sum(c5),
   sum(c6), sum(c7), sum(c8) from t1;
   0 |   0 |   0 |   0 |   0 |   0 |   0
 
Time: 1080.446 ms (00:01.080)
```

对于第一个测试用例，这是大约25%的加速，对于第二个测试用例，这是40%的加速!

最后，重要的是要记住，对于准备好的语句，JIT编译是在第一次执行函数时执行的。

## Conclusion

默认情况下，JIT编译是禁用的，对于基于RPM的系统，安装程序不会提示需要安装为默认提供程序LLVM提供位码的JIT包。

在从源进行构建时，请注意编译标志，以避免性能问题，例如是否启用了LLVM。

正如pgsql-hacker列表中所讨论的那样，JIT对成本的影响还没有被完全理解，因此在启用整个特性集群之前需要仔细规划，因为那些本来可以从编译中获益的查询实际上可能运行得更慢。但是，可以在每个查询的基础上启用JIT。

要获得关于JIT编译实现的深入信息，请查看项目Git日志、提交者和pgsql-hacker邮件列表。



