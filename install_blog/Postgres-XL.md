## 1 环境信息

| IP地址IP地址     | 系统版本     | 数据库版本               | CPU    | 内存    | 数据磁盘大小 |
| ------------ | -------- | ------------------- | ------ | ----- | ------ |
| 10.2.211.29  | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 256GB | 500G   |
| 10.2.211.30  | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 256GB | 500G   |
| 10.2.210.199 | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 256GB | 1000G  |
| 10.2.210.200 | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 256GB | 1000G  |
| 10.2.210.117 | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 64GB  | 1000G  |
| 10.2.210.118 | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 64GB  | 1000G  |
| 10.2.210.119 | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 64GB  | 1000G  |
| 10.2.210.120 | rhel-7.4 | postgres-xl-9.5r1.6 | 20core | 64GB  | 1000G  |

### 1.1 集群规划
| IP           | 角色             | 端口    | nodename   | data_directory                  |
| ------------ | -------------- | ----- | ---------- | ------------------------------- |
| 10.2.210.117 | gtm            | 6660  | gtm_master | /jboss/pgxl/data/gtm_master     |
| 10.2.210.118 | gtm_slave      | 6660  | gtm_slave  | /jboss/pgxl/data/gtm_slave      |
| 10.2.211.29  | coordinator    | 5432  | coord1     | /jboss/pgxl/data/coordinator    |
|              | datanode       | 6432  | dn1        | /jboss/pgxl/data/datanode       |
| 10.2.210.117 | datanode_slave | 16432 | dn1_slave  | /jboss/pgxl/data/datanode_slave |
|              | gtm proxy      | 6661  | gtm_pxy1   | /jboss/pgxl/data/gtm_proxy      |
| 10.2.211.30  | coordinator    | 5432  | coord2     | /jboss/pgxl/data/coordinator    |
|              | datanode       | 6432  | dn2        | /jboss/pgxl/data/datanode       |
| 10.2.210.118 | datanode_slave | 16432 | dn2_slave  | /jboss/pgxl/data/datanode_slave |
|              | gtm proxy      | 6661  | gtm_pxy2   | /jboss/pgxl/data/gtm_proxy      |
| 10.2.210.199 | coordinator    | 5432  | coord3     | /jboss/pgxl/data/coordinator    |
|              | datanode       | 6432  | dn3        | /jboss/pgxl/data/datanode       |
| 10.2.210.119 | datanode_slave | 16432 | dn3_slave3 | /jboss/pgxl/data/datanode_slave |
|              | gtm proxy      | 6661  | gtm_pxy3   | /jboss/pgxl/data/gtm_proxy      |
| 10.2.210.200 | coordinator    | 5432  | coord4     | /jboss/pgxl/data/coordinator    |
|              | datanode       | 6432  | dn4        | /jboss/pgxl/data/datanode       |
| 10.2.210.120 | datanode_slave | 16432 | dn4_slave  | /jboss/pgxl/data/datanode_slave |
|              | gtm proxy      | 6661  | gtm_pxy4   | /jboss/pgxl/data/gtm_proxy      |

### 1.2 整体架构图

![](https://raw.githubusercontent.com/NemoAA/blog/master/pic/Postgres-XL/pgxl_arch.png)

## 2 安装

### 2.1 设置host和语言环境

> 所有节点操作

```
--设置host 
vi /etc/hosts
加入
# add by pgxl
10.2.211.29     TK226-NW-F06-DX2-13
10.2.211.30     TK226-NW-F06-DX2-14
10.2.210.199    TK226-NW-F05-DX2-15
10.2.210.200    TK226-NW-F05-DX2-16
10.2.210.117    TK226-NW-F03-DX1-13
10.2.210.118    TK226-NW-F03-DX1-14
10.2.210.119    TK226-NW-F03-DX1-15
10.2.210.120    TK226-NW-F03-DX1-16

--设置语言环境
vi /etc/profile
加入
LANG=en_US.UTF-8

--生效
source /etc/profile
```

### 2.2 关闭防火墙和selinux

> 所有节点操作

```
--关闭防火墙
systemctl stop firewalld.service
iptables -F

--关闭selinux
setenforce 0
getenforce    
```

### 2.3 新建用户

> 所有节点操作

```
groupadd postgres
useradd -g postgres postgres
passwd postgres
```

### 2.4 配置互信

> 所有节点操作

```
--在每个服务器上运行
ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ""

ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.211.29
ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.211.30
ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.210.199
ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.210.200
ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.210.117
ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.210.118
ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.210.119
ssh-copy-id -i ~/.ssh/id_rsa.pub postgres@10.2.210.120
```

### 2.5 安装依赖包

> 所有节点操作

```
yum -y install lrzsz sysstat e4fsprogs ntp readline-devel zlib zlib-devel openssl openssl-devel pam-devel libxml2-devel libxslt-devel python-devel tcl-devel gcc make flex bison perl perl-devel perl-ExtUtils* OpenIPMI-tools systemtap-sdt-devel smartmontools
```

### 2.6 创建数据目录

> 所有节点操作,目录结构不一致,此次用软链接来解决

```
--10.2.211.29
ln -s /dbdata /jboss
mkdir -p /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
mkdir -p /usr/local/pgxl
chmod -R 775  /jboss/pgxl
chmod -R 775  /usr/local/pgxl
chmod 0700 /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
chown -R postgres:postgres /jboss/pgxl

--10.2.211.30
ln -s /dbdata /jboss
mkdir -p /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
mkdir -p /usr/local/pgxl
chmod -R 775  /jboss/pgxl
chmod -R 775  /usr/local/pgxl
chmod 0700 /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
chown -R postgres:postgres /jboss/pgxl

--10.2.210.199
mkdir -p /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
mkdir -p /usr/local/pgxl
chmod -R 775  /jboss/pgxl
chmod -R 775  /usr/local/pgxl
chmod 700 /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
chown -R postgres:postgres /jboss/pgxl

--10.2.210.200
mkdir -p /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
mkdir -p /usr/local/pgxl
chmod -R 775  /jboss/pgxl
chmod -R 775  /usr/local/pgxl
chmod 700 /jboss/pgxl/data/{coordinator,datanode,gtm_proxy}
chown -R postgres:postgres /jboss/pgxl

--10.2.210.117
mkdir -p /kpmon/pgxl/data/{gtm_master,dn1_slave}
mkdir -p /kpmon/pgxl/log
mkdir -p /usr/local/pgxl
chmod -R 775  /kpmon/pgxl
chmod -R 775  /usr/local/pgxl
chown -R postgres:postgres /kpmon/pgxl
chown -R postgres:postgres /usr/local/pgxl

--10.2.210.118
mkdir -p /kpmon/pgxl/data/{gtm_slave,dn2_slave}
mkdir -p /kpmon/pgxl/log
mkdir -p /usr/local/pgxl
chmod -R 775  /kpmon/pgxl
chmod -R 775  /usr/local/pgxl
chown -R postgres:postgres /kpmon/pgxl
chown -R postgres:postgres /usr/local/pgxl

--10.2.210.119
mkdir -p /kpmon/pgxl/data/dn3_slave
mkdir -p /kpmon/pgxl/log
mkdir -p /usr/local/pgxl
chmod -R 775  /kpmon/pgxl
chmod -R 775  /usr/local/pgxl
chown -R postgres:postgres /kpmon/pgxl
chown -R postgres:postgres /usr/local/pgxl

--10.2.210.120
mkdir -p /kpmon/pgxl/data/dn4_slave
mkdir -p /kpmon/pgxl/log
mkdir -p /usr/local/pgxl
chmod -R 775  /kpmon/pgxl
chmod -R 775  /usr/local/pgxl
chown -R postgres:postgres /kpmon/pgxl
chown -R postgres:postgres /usr/local/pgxl

```

### 2.7 编译安装

> 所有节点操作

```
--下载安装包
cd /opt/soft 
wget https://www.postgres-xl.org/downloads/postgres-xl-9.5r1.6.tar.bz2

tar jxvf postgres-xl-9.5r1.6.tar.bz2
cd /opt/soft/postgres-xl-9.5r1.6
./configure --prefix=/usr/local/pgxl --with-perl --with-tcl --with-python --with-openssl --with-pam --without-ldap --with-libxml --with-libxslt --with-wal-blocksize=8 --with-blocksize=8
make -j2 && make install

--安装contrib下插件
cd /opt/soft/postgres-xl-9.5r1.6/contrib
make -j2 && make install
```

### 2.8 设置环境变量

> 所有节点操作,**注意要改.bashrc** 

```
vi /home/postgres/.bashrc

# add by pgxl
export PGHOME=/usr/local/pgxl
export LD_LIBRARY_PATH=$PGHOME/lib:$LD_LIBRARY_PATH
export PATH=$PGHOME/bin:$PATH

```

### 2.9 系统参数调整

> 所有节点

```
-- 修改sysctl.conf
vi /etc/sysctl.d/99-sysctl.conf
加入

# add by Postgres-XL
net.ipv4.tcp_keepalive_intvl = 20
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_syncookies = 1    
net.ipv4.tcp_timestamps = 1 
net.ipv4.tcp_tw_recycle = 0 
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_congestion_control = htcp
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_max_orphans = 1048576
net.ipv4.tcp_max_syn_backlog = 20480
net.ipv4.tcp_max_tw_buckets = 400000
net.ipv4.tcp_no_metrics_save = 1
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65535 16777216

kernel.shmmax = 137438953472   
kernel.shmall = 53687091
vm.swappiness = 0
vm.zone_reclaim_mode = 0
vm.overcommit_memory = 2
vm.overcommit_ratio = 90
vm.vfs_cache_pressure = 150
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs=1000
vm.dirty_ratio = 80
vm.dirty_background_bytes = 102400000
kernel.sem=250 512000 100 2048
vm.nr_hugepages = 35000

-- 修改limits.conf
vi /etc/security/limits.d/20-nproc.conf

# add by Postgres-XL
* soft    nofile  655350
* hard    nofile  655350
* soft    nproc   655350
* hard    nproc   655350

--10.2.210.117-120修改如下
# add by Postgres-XL
net.ipv4.tcp_keepalive_intvl = 20
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_syncookies = 1    
net.ipv4.tcp_timestamps = 1 
net.ipv4.tcp_tw_recycle = 0 
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

kernel.shmmax = 34359738368   
kernel.shmall = 13421772
vm.swappiness = 0
vm.zone_reclaim_mode = 0
vm.overcommit_memory = 2
vm.overcommit_ratio = 90
vm.vfs_cache_pressure = 150
vm.dirty_writeback_centisecs = 100
vm.dirty_expire_centisecs=3000
vm.dirty_ratio = 80
vm.dirty_background_bytes = 102400000
kernel.sem=250 80000  32 320
vm.nr_hugepages = 6800

-- 修改limits.conf
vi /etc/security/limits.d/20-nproc.conf

# add by Postgres-XL
* soft    nofile  655350
* hard    nofile  655350
* soft    nproc   655350
* hard    nproc   655350
```

##  3 集群初始化及管理

### 3.1 配置pgxc_ctl.conf

> [配置文件下载地址](http://119.254.33.210/jira/browse/MORVAS-961)  

### 3.2 初始化集群

```
pgxc_ctl -c /home/postgres/pgxc_ctl/pgxc_ctl.conf init all
```

### 3.3 管理集群

```
--初始化集群
pgxc_ctl -c /home/postgres/pgxc_ctl/pgxc_ctl.conf init all

--启动
pgxc_ctl -c /home/postgres/pgxc_ctl/pgxc_ctl.conf start all

--停止
pgxc_ctl -c /home/postgres/pgxc_ctl/pgxc_ctl.conf stop all

--监控集群
pgxc_ctl -c /home/postgres/pgxc_ctl/pgxc_ctl.conf monitor all

```
