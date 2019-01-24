# PostgreSQL使用了多少内存?

(免责声明:这里的所有数据和示例都是在Linux上获得的——相同的数据也可以在其他系统上获得，只是我在Linux上工作，不太了解其他系统)。

这个问题偶尔会在不同的地方出现——PostgreSQL使用了太多的内存，这是为什么呢，要怎么缓和呢？

在进行“优化”之前，我们应该先理解问题。我们的做法是：标准工具 ps 和 top。为什么这样做?让我们来看看。

我的电脑上有一个非常简单的PostgreSQL实例，配置了4 GB的共享缓冲区和100MB的work_mem。运行之后，ps显示如下:

```
=$ ps -u pgdba uf
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
pgdba    32324  0.0  0.0  79788  1900 ?        S    14:26   0:00 sshd: pgdba@pts/13  
pgdba    32325  0.0  0.0  25844  5788 pts/13   Ss+  14:26   0:00  \_ -bash
pgdba    27502  0.0  0.8 4344112 109724 ?      S    14:18   0:00 /home/pgdba/work/bin/postgres
pgdba    27506  0.0  0.0  24792   620 ?        Ss   14:18   0:00  \_ postgres: logger process     
pgdba    27508  1.5 34.7 4346688 4274752 ?     Ss   14:18   0:14  \_ postgres: checkpointer process   
pgdba    27509  0.2 12.1 4346164 1495780 ?     Ss   14:18   0:02  \_ postgres: writer process     
pgdba    27510  0.3  0.1 4346164 17292 ?       Ss   14:18   0:03  \_ postgres: wal writer process   
pgdba    27511  0.0  0.0 4347168 2408 ?        Ss   14:18   0:00  \_ postgres: autovacuum launcher process   
pgdba    27512  0.0  0.0  26888   856 ?        Ss   14:18   0:00  \_ postgres: archiver process   last was 00000001000000060000004D
pgdba    27513  0.0  0.0  27184  1160 ?        Ss   14:18   0:00  \_ postgres: stats collector process   
pgdba    27713  5.6 34.8 4347268 4285716 ?     Ss   14:19   0:51  \_ postgres: depesz depesz [local] idle
pgdba    27722  2.6  3.1 4347412 392704 ?      Ss   14:19   0:23  \_ postgres: depesz depesz [local] idle
pgdba    27726 15.8 35.0 4352560 4309776 ?     Ss   14:19   2:25  \_ postgres: depesz depesz [local] idle
```

top显示的数据基本相同。

这很可疑，因为“free”表明：

```
=$ free
             total       used       free     shared    buffers     cached
Mem:      12296140   12144356     151784          0      26828   10644460
-/+ buffers/cache:    1473068   10823072
Swap:            0          0          0
```

也就是只使用了1.5GB的内存(还有大约10GB用作磁盘缓存——如果有应用程序需要更多的内存，可以释放)。

为什么会在PS中看到这么大的数字呢?

首先，我们需要忽略VSZ列。最重要的是RSS。但它仍然不是很有用:

```
=$ ps -u pgdba o pid,rss:8,cmd | awk 'NR>1 {A+=$2} {print} END{print "Total RSS: " A}'
  PID      RSS CMD
27502   109724 /home/pgdba/work/bin/postgres
27506      620 postgres: logger process     
27508  4274752 postgres: checkpointer process   
27509  1755420 postgres: writer process     
27510    17292 postgres: wal writer process   
27511     2408 postgres: autovacuum launcher process   
27512      856 postgres: archiver process   last was 00000001000000060000004D
27513     1160 postgres: stats collector process   
27713  4285716 postgres: depesz depesz [local] idle
27722   392700 postgres: depesz depesz [local] idle
27726  4309776 postgres: depesz depesz [local] idle
32324     1900 sshd: pgdba@pts/13  
32325     5788 -bash
Total RSS: 15158112
```

可以看到这个时刻的总内存是15GB，比我拥有的内存更大。那么，真正的内存使用情况是什么呢?比如:如果我杀了Pg的进程，我能获得多少内存?

幸运的是，我们可以从/proc目录的/filesystem/mountpoint/fairy查看RAM的确切用途。

Linux上的每个进程在/proc中都有一个目录。在这个目录中有许多文件和目录。不要被记录的文件大小所迷惑——它们都有“0”字节，但是它们确实包含信息。这是不可思议的。

我们感兴趣的一个文件是“smaps”。

它的内容是这样的:

```
=$ sudo head -n 20 /proc/27713/smaps
00400000-00914000 r-xp 00000000 09:00 3545633                            /home/pgdba/work/bin/postgres
Size:               5200 kB
Rss:                 964 kB
Pss:                 214 kB
Shared_Clean:        964 kB
Shared_Dirty:          0 kB
Private_Clean:         0 kB
Private_Dirty:         0 kB
Referenced:          964 kB
Anonymous:             0 kB
AnonHugePages:         0 kB
Swap:                  0 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Locked:                0 kB
00b13000-00b14000 r--p 00513000 09:00 3545633                            /home/pgdba/work/bin/postgres
Size:                  4 kB
Rss:                   4 kB
Pss:                   0 kB
Shared_Clean:          0 kB
...
```

这个进程的详细说明smaps超过2000行,所以我没有向大家完全展示它。

所以,不管怎样,进程27713根据ps,使用4285716千字节的内存。那么,它有多大呢?快速grep一下,我们看到:

```
=$ sudo grep -B1 -E '^Size: *[0-9]{6}' /proc/27713/smaps
7fde8dacc000-7fdf952d6000 rw-s 00000000 00:04 232882235                  /SYSV005a5501 (deleted)
Size:            4317224 kB
```

只有一个“block”的大小超过100MB,而且它的大小非常接近整个进程的大小。

关于它的完整信息:

```
7fde8dacc000-7fdf952d6000 rw-s 00000000 00:04 232882235                  /SYSV005a5501 (deleted)
Size:            4317224 kB
Rss:             4280924 kB
Pss:             1245734 kB
Shared_Clean:          0 kB
Shared_Dirty:    4280924 kB
Private_Clean:         0 kB
Private_Dirty:         0 kB
Referenced:      4280924 kB
Anonymous:             0 kB
AnonHugePages:         0 kB
Swap:                  0 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Locked:                0 kB
```

大多数信息或多或少是含义模糊的,但我们看到了一些东西:

- 它是共享内存(第一行包含rw-s,“s”说明是共享的)
- 通过(/SYSV… deleted),看起来共享内存是使用mmaping删除文件来完成的——因此在free输出中，这些内存将在“Cached”中,而不是“Used”列。
- 共享块的大小为4317224,其中4280924实际上是固定在内存中的

这是可以的——这是shared_buffer。但问题是,大多数的后端进程都使用了共享缓冲区。更糟糕的是,他们也不总是在同一范围上。例如,进程27722有相同的共享缓冲区数据:

```
=$ sudo grep -A14 7fde8dacc000-7fdf952d6000 /proc/27722/smaps
7fde8dacc000-7fdf952d6000 rw-s 00000000 00:04 232882235                  /SYSV005a5501 (deleted)
Size:            4317224 kB
Rss:              388652 kB
Pss:               95756 kB
Shared_Clean:          0 kB
Shared_Dirty:     388652 kB
Private_Clean:         0 kB
Private_Dirty:         0 kB
Referenced:       388652 kB
Anonymous:             0 kB
AnonHugePages:         0 kB
Swap:                  0 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Locked:                0 kB
```

在这里，我们看到这个进程只请求/使用了388MB的内存。

因此计算将是复杂的。例如——我们可能会有两个进程,每个使用400 MB的shared_buffers,但它并没有告诉我们它实际上是使用多少内存,因为它可能是,他们使用100 MB的相同的缓冲区,和300 MB的不同缓冲区,所以在总内存使用量是700 mb。

我们知道这个shared_buffers块的总大小是4317224。这是很好的。但是其他事情呢?例如库——它们可以由内核在多个进程之间共享。

幸运的是，2007年吴凤光(之前也写过)为内核发送了一个非常酷的补丁——它为smaps添加了“Pss”信息。

基本上，Pss最多是Rss，但是如果多个进程使用相同的内存页，Pss会减少。

这就是为什么上面的Pss比Rss的值低得多。例如，在上一个例子中。Rss提供了388652，但是Pss只有95756，这意味着这个后端使用的大多数页面也被其他3个后端使用。

所以，现在，了解了Pss，我们终于可以得到一个正在运行的pg集群的实际内存使用情况:

```
=$ ps -u pgdba o pid= | sed 's#.*#/proc/&/smaps#' | xargs sudo grep ^Pss: | awk '{A+=$2} END{print A}'
4329040
```

如果你只是说“天啊，他跑了什么?”，让我解释一下。第一个命令: 

```
=$ ps -u pgdba o pid=
27502
...
32325
```

返回pgdba用户的pids(通常您想要的是postgres，但我不一样，我是以pgdba的身份运行PostgreSQL)。

第二- sed -将pids更改为smaps文件的路径:

```
=$ ps -u pgdba o pid= | sed 's#.*#/proc/&/smaps#'
/proc/27502/smaps
...
/proc/32325/smaps
```

然后我简单的从sed中过滤以Pss开头的行。结果返回很多行，比如: 

```
/proc/32325/smaps:Pss:                   0 kB
/proc/32325/smaps:Pss:                   4 kB
/proc/32325/smaps:Pss:                   4 kB
```

然后awk统计第二列(即大小)。得到的数字是4329040，单位是千字节。

因此，理论上，如果我停止Pg，我将回收那么多内存。让我们看看这是不是真的:

```
=$ free; pg_ctl -m immediate stop; free
             total       used       free     shared    buffers     cached
Mem:      12296140   12145424     150716          0      40708   10640968
-/+ buffers/cache:    1463748   10832392
Swap:            0          0          0
waiting FOR server TO shut down.... done
server stopped
             total       used       free     shared    buffers     cached
Mem:      12296140    7781960    4514180          0      40856    6325092
-/+ buffers/cache:    1416012   10880128
Swap:            0          0          0
```

使用的内存从12145424下降到7781960——这意味着我得到了4363464 kB的RAM。这甚至比预期的4329040略高，但已经足够接近了。正如预期的那样，它大部分来自磁盘缓存，因为它用于shared_buffers。

这一切都很好，但是这个方法可以用来估计通过杀死单个后端进程可以回收多少内存吗?

也可以说是也可以说不是。关闭整个Pg意味着正在使用的共享内存可以被释放。在正常环境中，当您终止后端进程时，您最终只释放该后端私有的内存。这个数字通常很低。

例如，在另一台机器上，有更令人印象深刻的硬件环境:

```
=> ps uxf | grep USER.db_name | sort -nk6 | tail -n 1 | tee >( cat - >&2) | awk '{system("cat /proc/"$2"/smaps")}' | grep ^Private | awk '{A+=$2} END{print A}'
postgres  5278  8.2  0.3 107465132 1727408 ?   Ss   13:21   0:03  \_ postgres: USER db_name aa.bbb.cc.dd(eeeee) idle
52580
```

也就是说，该进程有1.7GB的RSS(在ps输出中可见)，但是只有52MB是私有内存，如果它被杀死，私有内存将被释放。

所以在这儿你不能使用Pss，但你可以使用来自smaps的Private_*数据来获取私有内存。

总而言之——PostgreSQL使用的内存比乍一看要少得多，虽然可以得到非常准确的数字——但您需要执行一些shell脚本来获得它们。

现在我准备好接受人们的评论，他们会在这篇文章中指出所有的技术错误，或者(更糟糕的)拼写错误。