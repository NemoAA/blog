## 为PostgreSQL优化Linux内核参数

>[本文翻译自](https://www.percona.com/blog/2018/08/29/tune-linux-kernel-parameters-for-postgresql-optimization/)

PostgreSQL数据库能否获得更好的性能，取决于是否正确定义了操作系统参数。OS内核参数配置不合适会导致数据库服务器性能下降。因此，必须根据数据库服务器及其工作负载配置这些参数。在这篇文章中，我们将讨论一些可能影响数据库服务器性能的重要内核参数，以及如何调整这些参数。

### SHMMAX / SHMALL

SHMMAX是一个内核参数，用于定义Linux进程可以分配的单个共享内存段的最大值。在9.2版本之前，PostgreSQL需要使用System V (SysV)来设置SHMMAX。在9.2之后，PostgreSQL切换到POSIX共享内存。所以现在它仅需要更少的System V共享内存字节。

在9.3版本之前，SHMMAX是最重要的内核参数。SHMMAX的值以字节为单位。

类似地，SHMALL是用于定义系统范围内共享内存页总量的另一个内核参数。要查看SHMMAX、SHMALL或SHMMIN的当前值，可以使用ipcs命令。

```
$ ipcs -lm
------ Shared Memory Limits --------
max number of segments = 4096
max seg size (kbytes) = 1073741824
max total shared memory (kbytes) = 17179869184
min seg size (bytes) = 1
```



```
$ ipcs -M
IPC status from  as of Thu Aug 16 22:20:35 PKT 2018
shminfo:
	shmmax: 16777216	(max shared memory segment size)
	shmmin:       1	(min shared memory segment size)
	shmmni:      32	(max number of shared memory identifiers)
	shmseg:       8	(max shared memory segments per process)
	shmall:    1024	(max amount of shared memory in pages)
```

PostgreSQL使用System V IPC来分配共享内存。这个参数是最重要的内核参数之一。每次当你看到以下错误时，这意味着你使用的是旧版本的PostgreSQL,，并且SHMMAX值非常低。用户需要根据他们使用的共享内存调整和增加值。

#### 可能错误的配置

如果SHMMAX配置错误，那么使用initdb初始化PostgreSQL集群时可能会出现以下错误。

```
DETAIL: Failed system call was shmget(key=1, size=2072576, 03600).
HINT: This error usually means that PostgreSQL's request for a shared memory segment exceeded your kernel's SHMMAX parameter.&nbsp;
You can either reduce the request size or reconfigure the kernel with larger SHMMAX. To reduce the request size (currently 2072576 bytes),
reduce PostgreSQL's shared memory usage, perhaps by reducing shared_buffers or max_connections.
If the request size is already small, it's possible that it is less than your kernel's SHMMIN parameter,
in which case raising the request size or reconfiguring SHMMIN is called for.
The PostgreSQL documentation contains more information about shared memory configuration. child process exited with exit code 1
```

类似地，在使用pg_ctl命令启动PostgreSQL服务器时也会出现以下错误。

```
DETAIL: Failed system call was shmget(key=5432001, size=14385152, 03600).
HINT: This error usually means that PostgreSQL's request for a shared memory segment exceeded your kernel's SHMMAX parameter.
You can either reduce the request size or reconfigure the kernel with larger SHMMAX.; To reduce the request size (currently 14385152 bytes),
reduce PostgreSQL's shared memory usage, perhaps by reducing shared_buffers or max_connections.
If the request size is already small, it's possible that it is less than your kernel's SHMMIN parameter,
in which case raising the request size or reconfiguring SHMMIN is called for.
The PostgreSQL documentation contains more information about shared memory configuration.
```

#### 注意不同的定义

在Linux和MacOS x中，SHMMAX/SHMALL参数的定义略有不同，定义如下:

- Linux: kernel.shmmax, kernel.shmall
- MacOS X: kern.sysv.shmmax, kern.sysv.shmall

The *sysctl* command can be used to change the value temporarily. To permanently set the value, add an entry into */etc/sysctl.conf*. The details are given below.

可以使用sysctl命令临时修改。要永久修改，请在/etc/sysctl.conf中添加一个条目。详情如下。

```
# Get the value of SHMMAX
sudo sysctl kern.sysv.shmmax
kern.sysv.shmmax: 4096
# Get the value of SHMALL
sudo sysctl kern.sysv.shmall
kern.sysv.shmall: 4096
# Set the value of SHMMAX
sudo sysctl -w kern.sysv.shmmax=16777216
kern.sysv.shmmax: 4096 -> 16777216<br>
# Set the value of SHMALL
sudo sysctl -w kern.sysv.shmall=16777216
kern.sysv.shmall: 4096 -> 16777216
```

```
# Get the value of SHMMAX
sudo sysctl kernel.shmmax
kernel.shmmax: 4096
# Get the value of SHMALL
sudo sysctl kernel.shmall
kernel.shmall: 4096
# Set the value of SHMMAX
sudo sysctl -w kernel.shmmax=16777216
kernel.shmmax: 4096 -> 16777216<br>
# Set the value of SHMALL
sudo sysctl -w kernel.shmall=16777216
kernel.shmall: 4096 -> 16777216
```

记住：永久修改需要在`/etc/sysctl.conf`中添加这些值

### 大页

默认情况下linux使用4K的内存页，BSD是Super Pages，而windows是Large Pages。页是分配给进程的RAM块。一个进程可以拥有多个页，这取决于它对内存的需求。进程需要的内存越多，分配给它的页面就越多。操作系统维护一个页分配给进程的表。页越小，表越大，查找该页表中的页所需的时间就越多。因此，大页可以在减少开销的情况下使用更多的内存，更少的查找时间，更少的页错误，更快的读写操作。这将会提高性能。

PostgreSQL只支持Linux上的大页。默认情况下，Linux使用4K内存页，因此在有大量内存操作的情况下，需要设置更大的页。通过使用大小为2MB和1GB的大页，观察性能的提升。可以设置大页的大小引导时间。您可以使用`cat /proc/meminfo | grep -i huge`命令轻松地检查Linux机器上的大面设置和利用率。

```
Note: This is only for Linux, for other OS this operation is ignored$ cat /proc/meminfo | grep -i huge
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
```

在这个例子中，虽然将大页设置为2,048 (2 MB)，但是大页的总数为0。这意味着大页被禁用了。

#### 确定大页数量的脚本

这是一个简单的脚本，返回所需的大页数量。当PostgreSQL运行时，在Linux机器上执行脚本。确保将$PGDATA环境变量设置为PostgreSQL的数据目录。

```
#!/bin/bash
pid=`head -1 $PGDATA/postmaster.pid`
echo "Pid: $pid"
peak=`grep ^VmPeak /proc/$pid/status | awk '{ print $2 }'`
echo "VmPeak: $peak kB"
hps=`grep ^Hugepagesize /proc/meminfo | awk '{ print $2 }'`
echo "Hugepagesize: $hps kB"
hp=$((peak/hps))
echo Set Huge Pages:     $hp
```

脚本的输出是这样的：

```
Pid:            12737
VmPeak:         180932 kB
Hugepagesize:   2048 kB
Set Huge Pages: 88
```

推荐的大页数量为88，因此应该将值设置为88。

```
sysctl -w vm.nr_hugepages= 88
```

现在检查大页，可以看到没有使用大页(HugePages_Free = HugePages_Total)。

```
$ cat /proc/meminfo | grep -i huge
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
HugePages_Total:      88
HugePages_Free:       88
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
```

现在$PGDATA/postgresql.conf中设置参数huge_pages=“on”并重新启动服务器。

```
$ cat /proc/meminfo | grep -i huge
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
HugePages_Total:      88
HugePages_Free:       81
HugePages_Rsvd:       64
HugePages_Surp:        0
Hugepagesize:       2048 kB
```

现在可以看到只使用了很少的几个大页。现在我们向数据库中插入一些数据。

```
postgres=# CREATE TABLE foo(a INTEGER);
CREATE TABLE
postgres=# INSERT INTO foo VALUES(generate_Series(1,10000000));
INSERT 0 10000000
```

让我们看看现在是否比以前使用了更多的大页。

```
$ cat /proc/meminfo | grep -i huge
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
HugePages_Total:      88
HugePages_Free:       18
HugePages_Rsvd:        1
HugePages_Surp:        0
Hugepagesize:       2048 kB
```

现在可以看到大部分大页都在使用中。

注意：这里使用的大页值非常低，这并不是大型生产机器的正常值。请评估系统所需的页面数量，并根据系统的工作负载和性能情况进行设置。

### vm.swappiness

vm.swappiness是另一个可能影响数据库性能的内核参数。此参数用于控制Linux系统上的swappiness(从交换内存到RAM页面)行为。该值的范围为0-100。它将控制交换或换出多少内存。0表示禁用交换，100表示主动交换。

可以设置较低的值，获得较好的性能。

在较新的内核中设置0可能会导致OOM Killer(Linux中的内存杀手进程)杀死进程。因此，为了安全起见，如果希望最小化交换，可以将值设置为1。Linux系统上的默认值是60。较高的值会导致MMU(内存管理单元)比RAM使用更多的交换空间，而较低的值会在内存中保存更多的数据/代码。

较小的值是提高PostgreSQL性能的好方法。

### vm.overcommit_memory / vm.overcommit_ratio

应用程序获取内存并在不需要时释放该内存。但是在某些情况下，应用程序会获取过多内存，并且没有释放。这可以调用OOM killer。下面是vm.overcommit_memory参数值，每个参数有一个描述：

​	1.启发式overcommit，智能执行(默认)，基于内核的启发式

​	2.允许overcommit

​	3.不允许超过overcommit_ratio

[参考资料：]( https://www.kernel.org/doc/Documentation/vm/overcommit-accounting)

vm.overcommit_ratio是用于overcommit的RAM的百分比。在具有2GB RAM的系统上，如果值为50%，则可能提交最多3GB RAM。

当vm.overcommit_memory的值为2时，将为PostgreSQL提供了更好的性能。这个值使服务器进程的RAM利用率最大化，而不会有被OOM killer进程杀死的风险。应用程序将能够过量使用，但只能在过量使用比率内。因此，值为2比默认值0性能更好。但是，可以通过确保超出允许范围的内存不会过度使用来提高可靠性。它避免了进程被OOM-killer杀死的风险。

在没有交换的系统上，当overcommit_memory为2，vm可能会遇到问题。

<https://www.postgresql.org/docs/current/static/kernel-resources.html#LINUX-MEMORY-OVERCOMMIT>

### vm.dirty_background_ratio/vm.dirty_background_bytes

 vm.dirty_background_ratio是脏页需要刷新到磁盘时，脏页在内存中的占比。刷新是在后台完成的。该参数取值范围为0~100；但是，低于5的值可能不是有效的，一些内核是不支持的。大多数Linux系统上的默认值是10。你可以以较低的比率获得写密集型操作的性能，这意味着Linux会在后台刷新脏页。

你需要设置vm.dirty_background_bytes的值取决于磁盘速度。

这两个参数没有“好”值，因为它们都依赖于硬件。然而，在大多数情况下将vm.dirty_background_ratio设置为5和vm.dirty_background_bytes设置为25%，磁盘速度可以提高25%的性能。

### vm.dirty_ratio / dirty_bytes

这和 vm.dirty_background_ratio / dirty_background_bytes是一样的。只是刷新在前台完成的，会阻塞了应用程序。所以vm.dirty_ratio应该高于vm.dirty_background_ratio。这将确保后台进程在前台进程之前启动，以尽可能避免阻塞应用程序。你可以根据磁盘IO负载调整这两个比率之间的差距。

### 总结

你也可以调优其他参数，但是改进的效果可能很小。我们必须记住，并非所有参数都与应用程序相关。有些应用程序通过调整某些参数而性能更好，而有些应用程序则不是。你需要在程序预计的工作负载、工作类型与配置参数之间找到良好的平衡，并且在进行调整时还必须考虑操作系统的行为。内核参数的调优不像数据库参数的调优那么容易：很难做到规范性。

在下一篇文章中，我将研究如何调优PostgreSQL的数据库参数。

