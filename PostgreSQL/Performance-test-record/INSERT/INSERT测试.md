# PostgreSQL TPCB测试记录

## 1. 环境信息

### 1.1 系统信息

| IP           | 系统     | 数据库          | 内存   | CPU  | 磁盘       | 文件系统 |
| ------------ | -------- | --------------- | ------ | ---- | ---------- | -------- |
| 192.168.6.11 | rhel 7.5 | PostgreSQL 11.1 | 256 GB | 56核 | ssd raid 1 | xfs      |

## 2. 配置

### 2.1 系统配置

```bash
# add by flying
net.ipv4.tcp_keepalive_intvl=20
net.ipv4.tcp_keepalive_probes=3
net.ipv4.tcp_keepalive_time=60

net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_tw_recycle = 0
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1025 65535
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_early_retrans = 1
net.core.netdev_max_backlog = 50000

net.ipv4.tcp_congestion_control = htcp
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_max_tw_buckets = 400000
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 8388608 1258291 16777216
net.ipv4.tcp_wmem = 8388608 1258291 16777216
kernel.shmmax = 135089532928
kernel.shmall = 32980843
vm.zone_reclaim_mode = 0
vm.swappiness = 0
vm.overcommit_memory = 2
vm.overcommit_ratio = 80
vm.vfs_cache_pressure = 150
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
#vm.dirty_ratio = 80
#vm.dirty_background_bytes = 10485760
vm.dirty_bytes = 536870912
vm.dirty_background_bytes = 41943040
kernel.sem = 250 512000 100 2048
kernel.numa_balancing = 0
kernel.sched_migration_cost_ns = 5000000
kernel.sched_autogroup_enabled = 0
vm.nr_hugepages = 34000
```

### 2.1 数据库配置

```
listen_addresses = '*'		# what IP address(es) to listen on;
port = 8432				# (change requires restart)
max_connections = 500			# (change requires restart)
superuser_reserved_connections = 10	# (change requires restart)
unix_socket_directories = '/home/postgres'	# comma-separated list of directories
unix_socket_permissions = 0700		# begin with 0 to use octal notation
tcp_keepalives_idle = 60		# TCP_KEEPIDLE, in seconds;
tcp_keepalives_interval = 10		# TCP_KEEPINTVL, in seconds;
tcp_keepalives_count = 10		# TCP_KEEPCNT;
shared_buffers = 64GB			# min 128kB
huge_pages = on			# on, off, or try
work_mem = 256MB				# min 64kB
maintenance_work_mem = 2GB		# min 1MB
max_stack_depth = 6MB			# min 100kB
dynamic_shared_memory_type = posix	# the default is the first option
vacuum_cost_delay = 10			# 0-100 milliseconds
vacuum_cost_limit = 1000		# 1-10000 credits
bgwriter_delay = 10ms			# 10-10000ms between rounds
bgwriter_lru_maxpages = 1000		# max buffers written/round, 0 disables
bgwriter_lru_multiplier = 10.0		# 0-10.0 multiplier on buffers scanned/round
effective_io_concurrency = 100		# 1-1000; 0 disables prefetching
max_worker_processes = 56		# (change requires restart)
max_parallel_maintenance_workers = 28	# taken from max_parallel_workers
max_parallel_workers_per_gather = 28	# taken from max_parallel_workers
parallel_leader_participation = on
max_parallel_workers = 56		# maximum number of max_worker_processes that
wal_level = minimal			# minimal, replica, or logical
fsync = on				# flush data to disk for crash safety
synchronous_commit = on		# synchronization level;
wal_sync_method = fdatasync		# the default is the first option
full_page_writes = on			# recover from partial page writes
wal_compression = on			# enable compression of full-page writes
wal_buffers = 64MB			# min 32kB, -1 sets based on shared_buffers
wal_writer_delay = 10ms		# 1-10000 milliseconds
commit_delay = 10			# range 0-100000, in microseconds
commit_siblings = 28			# range 1-1000
checkpoint_timeout = 10min		# range 30s-1d
max_wal_size = 32GB
min_wal_size = 8GB
checkpoint_completion_target = 0.9	# checkpoint target duration, 0.0 - 1.0
max_wal_senders = 0		# max number of walsender processes
wal_keep_segments = 256		# in logfile segments; 0 disables
random_page_cost = 3.0			# same scale as above
effective_cache_size = 196GB
log_destination = 'csvlog'		# Valid values are combinations of
logging_collector = on		# Enable capturing of stderr and csvlog
log_directory = 'log'			# directory where log files are written,
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'	# log file name pattern,
log_file_mode = 0600			# creation mode for log files,
log_truncate_on_rotation = on		# If on, an existing log file with the
log_rotation_age = 1d			# Automatic rotation of logfiles will
log_rotation_size = 128MB		# Automatic rotation of logfiles will
log_checkpoints = on
log_error_verbosity = verbose		# terse, default, or verbose messages
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d '		# special values:
log_statement = 'ddl'			# none, ddl, mod, all
log_timezone = 'PRC'
track_io_timing = on
track_functions = all			# none, pl, all
track_activity_query_size = 2048	# (change requires restart)
autovacuum = on			# Enable autovacuum subprocess?  'on'
log_autovacuum_min_duration = 0	# -1 disables, 0 logs all actions and
autovacuum_naptime = 300s		# time between autovacuum runs
datestyle = 'iso, mdy'
timezone = 'PRC'
lc_messages = 'C'			# locale for system error message
lc_monetary = 'C'			# locale for monetary formatting
lc_numeric = 'C'			# locale for number formatting
lc_time = 'C'				# locale for time formatting
default_text_search_config = 'pg_catalog.english'
shared_preload_libraries = 'pg_prewarm,pg_stat_statements'	# (change requires restart)
pg_stat_statements.max = 10000
pg_stat_statements.track = all
pg_stat_statements.track_utility = off
pg_stat_statements.save = on
```

### 2.2 其他设置

```
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
echo noop > /sys/block/sda/queue/scheduler
echo 256 > /sys/block/sda/queue/read_ahead_kb
echo 256 > /sys/block/sda/queue/nr_requests
echo 2 > /sys/block/sda/queue/rq_affinity
```

## 3. 测试准备

### 3.1 测试用表

```
--创建测试表 t_signal_mnlcode
drop table if exists t_signal_mnlcode;
create table t_signal_mnlcode
(
  stationcode varchar(50) not null,
  mnlcode     varchar(36) not null,
  modifytime  timestamp   not null,
  islatest    int         not null,
  checkCode   int         not null,
  serialid    int         not null,
  frequency   int         not null
);

-- 创建索引
create index on t_signal_mnlcode(modifytime desc);
create index on t_signal_mnlcode(serialid ,modifytime desc);

-- 创建测试目录
su - postgres
mkdir -p /home/postgres/tsdb/log
```

### 3.2 测试语句

```
nohup pgbench -M simple --progress-timestamp -n -r -P 1 -f /home/postgres/tsdb/batch_insert_1.sql -c 56 -j 56 -T 1800 tsdb > /home/postgres/tsdb/log/batch_insert_1.log 2>&1 &
```

## 4. 测试

### 4.1 batch_size_1-1

> block_size = 32k
>
> hugepages = 2048KB

#### 4.1.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 536870912
vm.dirty_background_bytes = 41943040

-- postgresql.conf
checkpoint_timeout = 10min 
max_wal_size = 100GB
min_wal_size = 16GB
checkpoint_completion_target = 1
```

#### 4.1.2 checkpoint相关参数调整

```
tsdb=# select pg_current_wal_insert_lsn();select pg_sleep(300);select pg_current_wal_insert_lsn();
 pg_current_wal_insert_lsn 
---------------------------
 11C/61711838
(1 row)

Time: 0.653 ms
 pg_sleep 
----------
 
(1 row)

Time: 300034.425 ms (05:00.034)
 pg_current_wal_insert_lsn 
---------------------------
 120/71E7BC38
(1 row)


-- 查看写了多少WAL
tsdb=# select pg_size_pretty(pg_wal_lsn_diff('120/71E7BC38','11C/61711838'));
 pg_size_pretty 
----------------
 16 GB
(1 row)


checkpoint_timeout = 10min
max_wal_size = 3*2*wal_write_size = 96GB 
```

#### 4.1.3 测试结果



![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-tps.png)



![1546057186328](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-os.png)

![1546057199134](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-cpu.png)

![1546057211137](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-disk-sum.png)

![1546057223317](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-disk-write.png)

### 4.2 batch_size_1-2

> block_size = 8k
>
> hugepages = 2048KB

#### 4.2.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 536870912
vm.dirty_background_bytes = 41943040

-- postgresql.conf
checkpoint_timeout = 10min 
max_wal_size = 100GB
min_wal_size = 16GB
checkpoint_completion_target = 1
```

#### 4.2.2 checkpoint相关参数调整

```
tsdb=# select pg_current_wal_insert_lsn();select pg_sleep(300);select pg_current_wal_insert_lsn();
 pg_current_wal_insert_lsn 
---------------------------
 11C/61711838
(1 row)

Time: 0.653 ms
 pg_sleep 
----------
 
(1 row)

Time: 300034.425 ms (05:00.034)
 pg_current_wal_insert_lsn 
---------------------------
 120/71E7BC38
(1 row)


-- 查看写了多少WAL
tsdb=# select pg_size_pretty(pg_wal_lsn_diff('120/71E7BC38','11C/61711838'));
 pg_size_pretty 
----------------
 16 GB
(1 row)


checkpoint_timeout = 10min
max_wal_size = 3*2*wal_write_size = 96GB 
```

#### 4.2.3 测试结果

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-2-tps.png)

![1546064305954](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-2-os.png)

![1546064339577](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-2-cpu.png)

![1546064368088](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-2-disk-sum.png)

![1546064401149](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/INSERT/result/batch_size_1-2-disk-writer.png)

### 4.3 batch_size_10-1

> block_size = 8k
>
> hugepages = 2048KB

#### 4.3.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 536870912
vm.dirty_background_bytes = 41943040

-- postgresql.conf
checkpoint_timeout = 10min 
max_wal_size = 100GB
min_wal_size = 16GB
checkpoint_completion_target = 1
```

#### 4.3.2 checkpoint相关参数调整

```
tsdb=# select pg_current_wal_insert_lsn();select pg_sleep(300);select pg_current_wal_insert_lsn();
 pg_current_wal_insert_lsn 
---------------------------
 11C/61711838
(1 row)

Time: 0.653 ms
 pg_sleep 
----------
 
(1 row)

Time: 300034.425 ms (05:00.034)
 pg_current_wal_insert_lsn 
---------------------------
 120/71E7BC38
(1 row)


-- 查看写了多少WAL
tsdb=# select pg_size_pretty(pg_wal_lsn_diff('120/71E7BC38','11C/61711838'));
 pg_size_pretty 
----------------
 16 GB
(1 row)


checkpoint_timeout = 10min
max_wal_size = 3*2*wal_write_size = 96GB 
```

#### 4.3.3 测试结果



## 5. 结果汇总

| batch_size | block_size(kb) | hugepagesize(MB) | TPS   | latency average(MS) |
| ---------- | -------------- | ---------------- | ----- | ------------------- |
| 1          | 32             | 2                | 87325 | 0.641               |
| 1          | 8              | 1024             | 91498 | 0.612               |



## 参考

> <https://www.youtube.com/watch?v=Lbx-JVcGIFo>
>
> <https://www.slideshare.net/PostgreSQL-Consulting/how-does-postgresql-work-with-disks-a-dbas-checklist-in-detail-pgconfus-2015>
>
> <https://www.postgresql.org/message-id/50E4AAB1.9040902@optionshouse.com>
>
> <https://www.postgresql-archive.org/Two-Necessary-Kernel-Tweaks-for-Linux-Systems-td5738537.html>
>
> <https://www.postgresql-archive.org/Linux-kernel-impact-on-PostgreSQL-performance-td5786701i160.html#a5787696>
>
> <https://access.redhat.com/articles/425823#WRITE_EXPIRE>
>
> <https://www.enterprisedb.com/docs/en/9.6/asguide/EDB_Postgres_Advanced_Server_Guide.1.36.html>
>
> <https://www.enterprisedb.com/docs/en/9.4/oracompat/Database_Compatibility_for_Oracle_Developers_Guide.1.306.html>
>
> <https://www.enterprisedb.com/docs/en/9.4/oracompat/Database_Compatibility_for_Oracle_Developers_Guide.1.306.html>