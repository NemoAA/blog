## 1 环境信息

| IP               | 系统       | 数据库          | 内存 | CPU     |
| ---------------- | ---------- | --------------- | ---- | ------- |
| 192.168.6.111/12 | centos 7.4 | PostgreSQL 10.4 | 2GB  | 2核(HT) |

## 2 odyssey安装

### 2.1 建立用户

```
groupadd postgres
useradd -g postgres postgres
passwd postgres
```

### 2.2 安装依赖包

> 安装需要gcc 4.6+ 和openssl 1.0.*版本,直接yum install 即可安装

#### 2.2.1 安装cmake

```
cd /opt/soft
wget https://cmake.org/files/v3.8/cmake-3.8.2.tar.gz
tar zxvf cmake-3.8.2.tar.gz
cd /opt/soft/cmake-3.8.2
./bootstrap
make -j2 && make install -j2
```

### 2.3 安装odyssey

```
cd /opt/soft/
git clone git://github.com/yandex/odyssey.git
cd odyssey
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```

### 2.4 配置odyssey

```
 -- 拷贝相关文件
 mkdir -p /usr/local/odyssey/bin
 mkdir -p /usr/local/odyssey/conf
 cp /opt/soft/odyssey/build/sources/odyssey /usr/local/odyssey/bin
 cp /opt/soft/odyssey/build/sources/odyssey /usr/bin/
 chmod a+x /usr/bin/odyssey
 cp /opt/soft/odyssey/odyssey.conf /usr/local/odyssey/conf
 cp -r /opt/soft/odyssey/scripts /usr/local/odyssey/
 cp -r /opt/soft/odyssey/third_party  /usr/local/odyssey/
 
 -- 修改权限
 chown -R postgres:postgres /usr/local/oddyssey/
 chmod 775 -R /usr/local/oddyssey/
```

### 2.5 启动odyssey

```
/usr/bin/odyssey /usr/local/oddyssey/conf/odyssey.conf
```

