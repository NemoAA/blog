#!/bin/bash
# kernel config
echo ''
echo '# add by flying'
echo net.ipv4.tcp_keepalive_intvl=20
echo net.ipv4.tcp_keepalive_probes=3
echo net.ipv4.tcp_keepalive_time=60
echo ''
echo net.ipv4.tcp_timestamps = 1
echo net.ipv4.tcp_tw_recycle = 0
echo net.ipv4.tcp_tw_reuse = 1
echo net.ipv4.ip_local_port_range = 1025 65535
echo net.ipv4.tcp_slow_start_after_idle = 0
echo net.ipv4.tcp_fin_timeout = 10
echo net.ipv4.tcp_early_retrans = 1
echo net.core.netdev_max_backlog = 50000
echo ''
echo net.ipv4.tcp_congestion_control = htcp
echo net.ipv4.tcp_max_syn_backlog = 4096
echo net.ipv4.tcp_max_tw_buckets = 400000
echo net.core.rmem_max = 16777216
echo net.core.wmem_max = 16777216
echo net.ipv4.tcp_rmem = 8388608 1258291 16777216
echo net.ipv4.tcp_wmem = 8388608 1258291 16777216

# calculate shm
page_size=`getconf PAGE_SIZE`
phys_pages=`getconf _PHYS_PAGES`
shmall=`expr $phys_pages / 2`
shmmax=`expr $shmall \* $page_size`
echo kernel.shmmax = $shmmax
echo kernel.shmall = $shmall
echo vm.zone_reclaim_mode = 0
echo vm.swappiness = 0
echo vm.overcommit_memory = 2
echo vm.overcommit_ratio = 80
echo vm.vfs_cache_pressure = 150
echo vm.dirty_writeback_centisecs = 100
echo vm.dirty_expire_centisecs=500
echo vm.dirty_ratio = 80
echo vm.dirty_background_bytes = 10485760
echo kernel.sem = 250 512000 100 2048
