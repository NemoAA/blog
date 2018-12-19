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
echo noop > /sys/block/sda/queue/scheduler
echo 256 > /sys/block/sda/queue/read_ahead_kb
echo 256 > /sys/block/sda/queue/nr_requests
echo 2 > /sys/block/sda/queue/rq_affinity
```

### 2.3 checkpoint 调整

```
postgres=# select pg_current_wal_insert_lsn();select pg_sleep(300);select pg_current_wal_insert_lsn();
 pg_current_wal_insert_lsn 
---------------------------
 96/1D95F8F8
(1 row)

Time: 0.977 ms
 pg_sleep 
----------
 
(1 row)

Time: 300091.978 ms (05:00.092)
 pg_current_wal_insert_lsn 
---------------------------
 97/3B62F338
(1 row)

Time: 0.413 ms
postgres=# select pg_current_wal_insert_lsn();select pg_sleep(300);select pg_current_wal_insert_lsn();
 pg_current_wal_insert_lsn 
---------------------------
 99/41BF0CB0
(1 row)

-- 查看写了多少WAL
postgres=# select pg_size_pretty(pg_wal_lsn_diff('97/3B62F338','96/1D95F8F8'));
 pg_size_pretty 
----------------
 4573 MB
(1 row)


checkpoint_timeout = 10min
max_wal_size = 3*2*wal_write_size = 26.8 
```

## 3. 生成测试数据

```
postgres=# create database tpcb;
CREATE DATABASE
[postgres@mdw log]$ pgbench -i -s 1000 tpcb -F 80

-- 测试语句
nohup pgbench -M prepared --progress-timestamp -P 1 -n -r -c 56 -j 56 -T 14400 tpcb > /home/postgres/tsdb/log/test_tpcb.log 2>&1 &
```

## 4. 测试

### 4.1 test-1

#### 4.1.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 536870912
vm.dirty_background_bytes = 41943040

-- postgresql.conf
checkpoint_timeout = 10min 
max_wal_size = 32GB
min_wal_size = 8GB
checkpoint_completion_target = 0.9
```

#### 4.1.2 测试结果

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.1-4h.png)

![1544596521762](https://github.com/NemoAA/blog/blob/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.1-4h-os.jpg?raw=true)

![](https://github.com/NemoAA/blog/blob/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.1-4h-cpu.jpg?raw=true)

![1544596470796](https://github.com/NemoAA/blog/blob/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.1-4h-disk.jpg?raw=true)

### 4.2 test-2

#### 4.2.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 536870912
vm.dirty_background_bytes = 41943040

-- postgresql.conf
checkpoint_timeout = 10min 
max_wal_size = 32GB
min_wal_size = 8GB
checkpoint_completion_target = 0.9
```

#### 4.2.2 测试结果

![1544597137401](https://github.com/NemoAA/blog/blob/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.2-1h-tps.jpg?raw=true)

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.2-os.jpg)

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.2-cpu.jpg)

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.2-disk.jpg)

### 4.3 test-3

#### 4.3.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 536870912
vm.dirty_background_bytes = 41943040

-- postgresql.conf
checkpoint_timeout = 60min
max_wal_size = 192GB
min_wal_size = 16GB
checkpoint_completion_target = 0.9
```

#### 4.3.2 测试结果

![1544605145191](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.3-tps.png)

![1544605246673](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.3-os.png)

![1544605251652](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.3-cpu.png)

![1544605259667](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.3-disk.png)

### 4.4 test-4

#### 4.4.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 2147483648 -- raid cache
vm.dirty_background_bytes = 41943040

-- postgresql.conf
checkpoint_timeout = 60min
max_wal_size = 192GB
min_wal_size = 16GB
checkpoint_completion_target = 0.9
```

#### 4.4.2 测试结果

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.4-tps.png)

![1544625362536](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.4-os.png)

![1544625417484](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.4-cpu.png)

![1544625556966](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.4-disk.png)

### 4.5 test-5

#### 4.5.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 2147483648 -- raid cache
vm.dirty_background_bytes = 41943040

echo 8 > /sys/block/sda/queue/iosched/writes_starved
echo 8000 > /sys/block/sda/queue/iosched/write_expire

-- postgresql.conf
checkpoint_timeout = 5min
max_wal_size = 32GB
min_wal_size = 8GB
checkpoint_completion_target = 0.9
full_page_writes = off
```

#### 4.5.2 测试结果

```
nohup pgbench -M prepared --progress-timestamp -P 1 -n -r -c 28 -j 28 -T 1800 tpcb > /home/postgres/tsdb/log/test_tpcb.log 2>&1 &
```

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.5-tps.png)

![1544888350492](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.5-os.png)

![1544888411168](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.5-cpu.png)

![1544888458229](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.5-disk.png)

### 4.6 test-6

#### 4.6.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 2147483648 -- raid cache
vm.dirty_background_bytes = 41943040

echo 8 > /sys/block/sda/queue/iosched/writes_starved
echo 8000 > /sys/block/sda/queue/iosched/write_expire

-- postgresql.conf
checkpoint_timeout = 5min
max_wal_size = 32GB
min_wal_size = 8GB
checkpoint_completion_target = 0.9
full_page_writes = off
```

#### 4.6.2 测试结果

```
nohup pgbench -M prepared --progress-timestamp -P 1 -n -r -c 28 -j 28 -T 14400 tpcb > /home/postgres/tsdb/log/test_tpcb.log 2>&1 &
```

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.6-tps.png)

![1544977069909](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.6-os.png)

![1544977113559](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.6-cpu.png)

![1544977142698](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.6-disk.png)
### 4.7 test-7

12小时不间断压测

#### 4.7.1 调整参数

```
 -- os-kernel
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs = 500
vm.dirty_bytes = 2147483648 -- raid cache
vm.dirty_background_bytes = 41943040

echo 8 > /sys/block/sda/queue/iosched/writes_starved
echo 8000 > /sys/block/sda/queue/iosched/write_expire

-- postgresql.conf
checkpoint_timeout = 5min
max_wal_size = 32GB
min_wal_size = 8GB
checkpoint_completion_target = 0.9
full_page_writes = off
```

#### 4.7.2 测试结果

```
nohup pgbench -M prepared --progress-timestamp -P 1 -n -r -c 28 -j 28 -T 14400 tpcb > /home/postgres/tsdb/log/test_tpcb.log 2>&1 &
```

![](https://raw.githubusercontent.com/NemoAA/blog/master/PostgreSQL/Performance-test-record/TPCB/result/tpcb-test-4.7-tps.png)

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