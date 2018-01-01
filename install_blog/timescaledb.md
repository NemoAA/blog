# timescaledb安装

## 1. 环境准备

| 系统                                       | 数据库           | timescaledb | 内存   | CPU       | 磁盘               |
| ---------------------------------------- | ------------- | ----------- | ---- | --------- | ---------------- |
| Red Hat Enterprise Linux Server release 7.3 (Maipo) | PostgreSQL 10 | 0.7.1       | 16GB | 2路,24core | 10000 RPM raid 0 |

## 2. timescaledb安装
### 2.1安装PostgreSQL数据库

#### 2.1.1 系统软件更新

```
yum -y install lrzsz sysstat e4fsprogs ntp readline-devel zlib zlib-devel openssl openssl-devel pam-devel libxml2-devel libxslt-devel python-devel tcl-devel gcc make flex bison perl perl-devel perl-ExtUtils* OpenIPMI-tools systemtap-sdt-devel smartmontools 
```

#### 2.1.2 下载源码包

```
cd /opt/soft
wget https://ftp.postgresql.org/pub/source/v10.1/postgresql-10.1.tar.gz
tar zxvf postgresql-10.1.tar.gz
```

#### 2.1.3 编译安装

```
--源码编译
cd /opt/soft/postgresql-10.1
./configure --prefix=/usr/local/pgsql --with-pgport=5432 
make && make install

-- 如果需要调试则按照如下方式编译
CFLAGS="-g -ggdb -fno-omit-frame-pointer" ./configure --prefix=/usr/local/pgsql --with-pgport=5432 -enable-debug
CFLAGS="-g -ggdb -fno-omit-frame-pointer" make world -j 64  
CFLAGS="-g -ggdb -fno-omit-frame-pointer" make install-world  

--安装contrib下扩展
cd contrib
make && make install
```

#### 2.1.4 创建用户

```
--创建用户
groupadd postgres
useradd -g postgres postgres

--创建相关目录
mkdir /home/postgres/log
mkdir /data/pgdata

--更改权限
chown postgres:postgres /home/postgres/*
chown postgres:postgres /data/pgdata
chown postgres:postgres /usr/local/pgsql/*
chmod -R 775 /home/postgres/*
chmod -R 0700 /data/pgdata
```

#### 2.1.5 设置环境变量

```
vi /home/postgres/.bash_profile

# add by postgres
export PGHOME=/usr/local/pgsql
export PGPORT=5432
export PGDATA=/data/pgdata
export DATE=`date +"%Y%m%d%H%M"`
export PGUSER=postgres
export PGHOST=localhost
export PGDATABASE=postgres
export PATH=$PGHOME/bin:$PATH:.
export MANPATH=$PGHOME/share/man:$MANPATH
export LD_LIBRARY_PATH=$PGHOME/lib:$LD_LIBRARY_PATH
export LANG=en_US.utf8
export PG_OOM_ADJUST_FILE=/proc/self/oom_score_adj
export PG_OOM_ADJUST_VALUE=0
```

#### 2.1.6 初始化数据库

```
su - postgres
initdb -D /data/pgdata -E UTF8 --locale=C -U postgres
```

### 2.2 安装timescaledb

#### 2.2.1安装cmake 

```
--安装c++编译器
yum install gcc-c++.x86_64 -y

--安装cmake
cd /opt/soft
wget https://cmake.org/files/v3.8/cmake-3.8.2.tar.gz
tar zxvf cmake-3.8.2.tar.gz
cd /opt/soft/cmake-3.8.2
./bootstrap
make && make install
```

#### 2.2.2 编译timescaledb源码

```
--下载源码
cd /opt/soft/postgresql-10.1/contrib/
git clone https://github.com/timescale/timescaledb

--编译源码
cd/opt/soft/postgresql-10.1/contrib/timescaledb
./bootstrap
cd /opt/soft/postgresql-10.1/contrib/timescaledb/build
make && make install
```

#### 2.2.3 设置postgresql.conf

```
vi $PGDATA/postgresql.conf
shared_preload_libraries = 'timescaledb'

--重启数据库生效
pg_ctl -mf restart
```

