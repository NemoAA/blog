## Backup and Restore a PostgreSQL Cluster With Multiple Tablespaces Using pg_basebackup

## 使用pg_basebackup对PostgreSQL多表空间集群进行备份还原 

By [Avinash Vallarapu](https://www.percona.com/blog/author/avi-vallarapu/) [Backups](https://www.percona.com/blog/category/backups/), [PostgreSQL](https://www.percona.com/blog/category/postgresql/) [backup](https://www.percona.com/blog/tag/backup/), [database recovery](https://www.percona.com/blog/tag/database-recovery/) [0 Comments](https://www.percona.com/blog/2018/12/21/backup-restore-postgresql-cluster-multiple-tablespaces-using-pg_basebackup/#respond)

pg_basebackup is a widely used PostgreSQL backup tool that allows us to take an ONLINE and CONSISTENT file system level backup. These backups can be used for point-in-time-recovery or to set up a slave/standby. You may want to refer to our previous blog posts, [PostgreSQL Backup Strategy](https://www.percona.com/blog/2018/09/25/postgresql-backup-strategy-enterprise-grade-environment/), [Streaming Replication in PostgreSQL](https://www.percona.com/blog/2018/09/07/setting-up-streaming-replication-postgresql/) and [Faster PITR in PostgreSQL](https://www.percona.com/blog/2018/06/28/faster-point-in-time-recovery-pitr-postgresql-using-delayed-standby/) where we describe how we used pg_basebackup for different purposes. In this post, I’ll demonstrate the steps to restore a backup taken using [pg_basebackup](https://www.postgresql.org/docs/10/app-pgbasebackup.html) when we have many tablespaces that store databases or their underlying objects.

A simple backup can be taken using the following syntax.

`pg_basebackup`是一款广泛运用于`PostgreSQL`备份的工具，它允许我们做一个在线的具有一致性的文件系统级别备份。这些备份可用于时间点恢复或安装从库。您可能想要参考我们以前的博客文章，[PostgreSQL备份策略](https://www.percona.com/blog/2018/09/25/postgresql-backup-strategy-enterprise-grade-environment/)，[PostgreSQL流复制](https://www.percona.com/blog/2018/09/07/setting-up-streaming-replication-postgresql/)和[PostgreSQL中更快的PITR](https://www.percona.com/blog/2018/06/28/faster-point-in-time-recovery-pitr-postgresql-using-delayed-standby/)，在这些文章中，我们描述了为了达到不同的目的怎样使用pg_basebackup。在这篇文章中，我将演示当我们有多个存储数据库或其对象的表空间时，使用pg_baseBackup生成的备份进行恢复时的步骤。 

可以使用下面的语法生成一个简单备份

```
Tar and Compressed Format
$ pg_basebackup -h localhost -p 5432 -U postgres -D /backupdir/latest_backup -Ft -z -Xs -P
Plain Format
$ pg_basebackup -h localhost -p 5432 -U postgres -D /backupdir/latest_backup -Fp -Xs -P
```



Using a tar and compressed format is advantageous when you wish to use less disk space to backup and store all tablespaces, data directory and WAL segments, with everything in just one directory (target directory for backup).

当您希望使用较少的磁盘空间来备份和存储所有表空间、数据目录和WAL日志时，使用tar和压缩格式是有利的，因为所有内容都在一个目录中(备份的目标目录)。

Whereas a plain format stores a copy of the data directory as is, in the target directory. When you have one or more non-default tablespaces, tablespaces may be stored in a separate directory. This is usually the same as the original location, unless you use --tablespace-mapping  to modify the destination for storing the tablespaces backup.

而普通格式则在目标目录中按原样存储数据目录的副本。当您有一个或多个非默认表空间时，表空间可能存储在单独的目录中。这通常与原始位置相同，除非您使用`--tablespace-mapping`来修改用于存储表空间备份的目标目录。

PostgreSQL supports the concept of tablespaces. In simple words, a tablespace helps us maintain multiple locations to scatter databases or their objects. In this way, we can distribute the IO and balance the load across multiple disks.

PostgreSQL支持表空间的概念。简而言之，表空间帮助我们维护多个位置以分散数据库或它们的对象。通过这种方式，我们可以在多个磁盘之间分配IO和均衡负载。

To understand what happens when we backup a PostgreSQL cluster that contains multiple tablespaces, let’s consider the following example. We’ll take these steps:

为了了解备份包含多个表空间的PostgreSQL集群时会发生什么，让我们考虑以下示例。我们将采取以下步骤：

- Create two tablespaces in an existing master-slave replication setup.
- 在一个运行中的主备流复制环境下创建2个表空间
- Take a backup and see what is inside the backup directory.
- 运行备份看看备份目录里是什么
- Restore the backup.
- 恢复这个备份
- Conclude our findings
- 总结

### Create 2 tablespaces and take a backup (tar format) using pg_basebackup

### 创建2个表空间并使用pg_basebackup进行备份（tar格式）

#### 步骤1：

I set up a replication cluster using PostgreSQL 11.2. You can refer to our blog post [Streaming Replication in PostgreSQL](https://www.percona.com/blog/2018/09/07/setting-up-streaming-replication-postgresql/) to reproduce the same scenario. Here are the steps used to create two tablespaces:

我使用PostgreSQL11.2设置了一个复制集群。您可以参考我们的博客文章[PostgreSQL流复制](https://www.percona.com/blog/2018/09/07/setting-up-streaming-replication-postgresql/)来重现相同的场景。以下是用于创建两个表空间的步骤：

  

```
$ sudo mkdir /data_pgbench
$ sudo mkdir /data_pgtest
$ psql -c "CREATE TABLESPACE data_pgbench LOCATION '/data_pgbench'"
$ psql -c "CREATE TABLESPACE data_pgtest LOCATION '/data_pgtest'"
$ psql -c "select oid, spcname, pg_tablespace_location(oid) from pg_tablespace"
oid | spcname | pg_tablespace_location
-------+--------------+------------------------
1663 | pg_default |
1664 | pg_global |
16419 | data_pgbench | /data_pgbench
16420 | data_pgtest | /data_pgtest
(4 rows)
```

####步骤2：

Now, I create two databases in two different tablespaces, using [pgbench](https://www.postgresql.org/docs/10/pgbench.html) to create a few tables and load some data in them.

现在，我在两个不同的表空间中创建两个数据库，使用[pgbench](https://www.postgresql.org/docs/10/pgbench.html)创建几个表并在其中加载一些数据。

```
$ psql -c "CREATE DATABASE pgbench TABLESPACE data_pgbench"
$ psql -c "CREATE DATABASE pgtest TABLESPACE data_pgtest"
$ pgbench -i pgbench
$ pgbench -i pgtest
```

In a master-slave setup built using streaming replication, you must ensure that the directories exist in the slave, before running a "CREATE TABLESPACE ..."  on the master. This is because, the same statements used to create a tablespace are shipped/applied to the slave through WALs – this is unavoidable. The slave crashes with the following message, when these directories do not exist:

在使用流复制构建的主-从设置中，在主机上运行`Create TABLESPACE...`之前，必须确保表空间目录存在于从机的目录上。这是因为，用于创建表空间的语句是通过WALs传送/应用于从机的-这是不可避免的。当这些目录不存在时，从机将崩溃，并显示以下消息：

```
2018-12-15 12:00:56.319 UTC [13121] LOG: consistent recovery state reached at 0/80000F8
2018-12-15 12:00:56.319 UTC [13119] LOG: database system is ready to accept read only connections
2018-12-15 12:00:56.327 UTC [13125] LOG: started streaming WAL from primary at 0/9000000 on timeline 1
2018-12-15 12:26:36.310 UTC [13121] FATAL: directory "/data_pgbench" does not exist
2018-12-15 12:26:36.310 UTC [13121] HINT: Create this directory for the tablespace before restarting the server.
2018-12-15 12:26:36.310 UTC [13121] CONTEXT: WAL redo at 0/9000448 for Tablespace/CREATE: 16417 "/data_pgbench"
2018-12-15 12:26:36.311 UTC [13119] LOG: startup process (PID 13121) exited with exit code 1
2018-12-15 12:26:36.311 UTC [13119] LOG: terminating any other active server processes
2018-12-15 12:26:36.314 UTC [13119] LOG: database system is shut down
2018-12-15 12:27:01.906 UTC [13147] LOG: database system was interrupted while in recovery at log time 2018-12-15 12:06:13 UTC
2018-12-15 12:27:01.906 UTC [13147] HINT: If this has occurred more than once some data might be corrupted and you might need to choose an earlier recovery target.
```

#### 步骤3：

Let’s now use pg_basebackup to take a backup. In this example, I use a tar format backup.

现在，让我们使用pg_baseBackup进行备份。在本例中，我使用tar格式的备份。

 

```
$ pg_basebackup -h localhost -p 5432 -U postgres -D /backup/latest_backup -Ft -z -Xs -P
94390/94390 kB (100%), 3/3 tablespaces
```

In the above log, you could see that there are three tablespaces that have been backed up: one default, and two newly created tablespaces. If we go back and check how the data in the two tablespaces are distributed to appropriate directories, we see that there are symbolic links created inside the pg_tblspc directory (within the data directory) for the oid’s of both tablespaces. These links are directed to the actual location of the tablespaces, we specified in Step 1.

在上面的日志中，您可以看到已经备份了三个表空间：一个默认表空间和两个新创建的表空间。如果我们返回检查这两个表空间中的数据是如何分布到适当的目录中的，我们会看到在pg_tblspc目录(在数据目录中)中为这两个表空间的OID创建了符号链接。这些链接指向我们在步骤1中指定的表空间的实际位置。

```
$ ls -l $PGDATA/pg_tblspc
total 0
lrwxrwxrwx. 1 postgres postgres 5 Dec 15 12:31 16419 -> /data_pgbench
lrwxrwxrwx. 1 postgres postgres 6 Dec 15 12:31 16420 -> /data_pgtest
```

#### 步骤4：

Here are the contents inside the backup directory, that was generated through the backup taken in Step 3.

以下是备份目录中的内容，该目录是通过在步骤3中执行的备份生成的。

 

```
$ ls -l /backup/latest_backup
total 8520
-rw-------. 1 postgres postgres 1791930 Dec 15 12:54 16419.tar.gz
-rw-------. 1 postgres postgres 1791953 Dec 15 12:54 16420.tar.gz
-rw-------. 1 postgres postgres 5113532 Dec 15 12:54 base.tar.gz
-rw-------. 1 postgres postgres 17097 Dec 15 12:54 pg_wal.tar.gz
```

Tar Files : 16419.tar.gz and 16420.tar.gz are created as a backup for the two tablespaces. These are created with the same names as the OIDs of their respective tablespaces.

Let’s now take a look how we can restore this backup to completely different locations for data and tablespaces.

 Tar 文件：16419.tar.gz和16420.tar.gz是作为这两个表空间的备份创建的。这些对象的名称与各自表空间的OID相同。

现在让我们看看如何将此备份恢复到完全不同的数据和表空间位置。  

### Restore a backup with multiple tablespaces

### 恢复一个具有多个表空间的备份

#### 步骤1：

In order to proceed further with the restore, let’s first extract the base.tar.gz file. This file contains some important files that help us to proceed further.

为了进一步进行恢复，让我们首先提取base.tar.gz文件。此文件包含一些重要文件，这些文件可帮助我们进一步进行操作。

 

```
$ tar xzf /backup/latest_backup/base.tar.gz -C /pgdata
$ ls -larth /pgdata
total 76K
drwx------. 2 postgres postgres 18 Dec 14 14:15 pg_xact
-rw-------. 1 postgres postgres 3 Dec 14 14:15 PG_VERSION
drwx------. 2 postgres postgres 6 Dec 14 14:15 pg_twophase
drwx------. 2 postgres postgres 6 Dec 14 14:15 pg_subtrans
drwx------. 2 postgres postgres 6 Dec 14 14:15 pg_snapshots
drwx------. 2 postgres postgres 6 Dec 14 14:15 pg_serial
drwx------. 4 postgres postgres 36 Dec 14 14:15 pg_multixact
-rw-------. 1 postgres postgres 1.6K Dec 14 14:15 pg_ident.conf
drwx------. 2 postgres postgres 6 Dec 14 14:15 pg_dynshmem
drwx------. 2 postgres postgres 6 Dec 14 14:15 pg_commit_ts
drwx------. 6 postgres postgres 54 Dec 14 14:18 base
-rw-------. 1 postgres postgres 4.5K Dec 14 16:16 pg_hba.conf
-rw-------. 1 postgres postgres 208 Dec 14 16:18 postgresql.auto.conf
drwx------. 2 postgres postgres 6 Dec 14 16:18 pg_stat
drwx------. 2 postgres postgres 58 Dec 15 00:00 log
drwx------. 2 postgres postgres 6 Dec 15 12:54 pg_stat_tmp
drwx------. 2 postgres postgres 6 Dec 15 12:54 pg_replslot
drwx------. 4 postgres postgres 68 Dec 15 12:54 pg_logical
-rw-------. 1 postgres postgres 224 Dec 15 12:54 backup_label
drwx------. 3 postgres postgres 28 Dec 15 12:57 pg_wal
drwx------. 2 postgres postgres 4.0K Dec 15 12:57 global
drwx------. 2 postgres postgres 32 Dec 15 13:01 pg_tblspc
-rw-------. 1 postgres postgres 55 Dec 15 13:01 tablespace_map
-rw-------. 1 postgres postgres 24K Dec 15 13:04 postgresql.conf
-rw-r--r--. 1 postgres postgres 64 Dec 15 13:07 recovery.conf
-rw-------. 1 postgres postgres 44 Dec 15 13:07 postmaster.opts
drwx------. 2 postgres postgres 18 Dec 15 13:07 pg_notify
-rw-------. 1 postgres postgres 30 Dec 15 13:07 current_logfiles
```



#### 步骤2：

The files that we need to consider for our recovery are :

恢复时需要考虑的文件包括：

- backup_label
- tablespace_map

When you open the backup_label file, we see the start WAL location, backup start time, etc. These are some details that help us perform a point-in-time-recovery.

当您打开BACKUP_LABEL文件时，我们将看到开始WAL的位置、备份开始时间等。以下是一些帮助我们执行时间点恢复的详细信息。

 

```
$ cat backup_label
START WAL LOCATION: 0/B000028 (file 00000001000000000000000B)
CHECKPOINT LOCATION: 0/B000060
BACKUP METHOD: streamed
BACKUP FROM: master
START TIME: 2018-12-15 12:54:10 UTC
LABEL: pg_basebackup base backup
START TIMELINE: 1
```

  Now, let us see what is inside the tablespace_map file

现在，让我们看下`tablespace_map`文件里是什么

```
$ cat tablespace_map
16419 /data_pgbench
16420 /data_pgtest
```

In the above log, you could see that there are two entries – one for each tablespace. This is a file that maps a tablespace (oid) to its location. When you start PostgreSQL after extracting the tablespace and WAL tar files, symbolic links are created automatically by postgres – inside the pg_tblspc directory for each tablespace – to the appropriate tablespace location, using the mapping done in this files.

在上面的日志中，您可以看到有两个条目-每个表空间一个条目。这是一个将表空间(OID)映射到其位置的文件。在解压缩表空间和WAL TAR文件之后启动PostgreSQL时，Postgres会自动创建符号链接(在pg_tblspc目录内为每一个表空间)，并使用此文件的映射将其创建到相应的表空间位置。

#### 步骤3：

Now, in order to restore this backup in the same postgres server from where the backup was taken, you must remove the existing data in the original tablespace directories. This allows you to extract the tar files of each tablespaces to the appropriate tablespace locations.

The actual commands for extracting tablespaces from the backup in this case were the following:

  现在，为了在进行备份的同一Postgres服务器中恢复此备份，您必须删除原始表空间目录中的现有数据。这允许您将每个表空间的tar文件提取到相应的表空间位置。

在这种情况下，用于从备份提取表空间的实际命令如下： 

  

```
$ tar xzf 16419.tar.gz -C /data_pgbench (Original tablespace location)
$ tar xzf 16420.tar.gz -C /data_pgtest  (Original tablespace location)
```

In a scenario where you want to restore the backup to the same machine from where the backup was originally taken, we must use different locations while extracting the data directory and tablespaces from the backup. In order to achieve that, tar files for individual tablespaces may be extracted to different directories than the original directories specified in tablespace_map file, upon which we can modify the tablespace_map file with the new tablespace locations. The next two steps should help you to see how this works.

在您希望将备份恢复到最初进行备份的同一台计算机的情况下，在从备份中提取数据目录和表空间时，我们必须使用不同的位置。为了实现这一点，可以将各个表空间的tar文件提取到与`tablesspace_map`文件中指定的原始目录不同的目录中，基于此点我们可以使用新的表空间位置来修改`tablesspace_map`文件 。接下来的两个步骤将帮助您了解这是如何工作的。

##### 步骤3a:

Create two different directories and extract the tablespaces to them.

创建两个不同的目录，提取表空间到目录中。

 

```
$ tar xzf 16419.tar.gz -C /pgdata_pgbench (Different location for tablespace than original)
$ tar xzf 16420.tar.gz -C /pgdata_pgtest  (Different location for tablespace than original)
```

##### 步骤3b：

Edit the tablespace_map file with the new tablespace locations. Replace the original location of each tablespace with the new location, where we have extracted the tablespaces in the previous step. Here is how it appears after the edit.

使用新的表空间位置编辑`tablesspace_map`文件。将每个表空间的原始位置替换为新位置，新位置是我们在上一步中提取表空间的目录。以下是它在编辑后的内容。

```
$ cat tablespace_map
16419 /pgdata_pgbench
16420 /pgdata_pgtest
```

#### 步骤4：

Extract pg_wal.tar.gz from backup to pg_wal directory of the new data directory.

从备份中提取`pg_wal.tar.gz`到新数据目录的`pg_wal`目录下

```
$ tar xzf pg_wal.tar.gz -C /pgdata/pg_wal
```

#### 步骤5：

Create recovery.conf to specify the time until when you wish to perform a point-in-time-recovery. Please refer to our previous [blog post](https://www.percona.com/blog/2018/06/28/faster-point-in-time-recovery-pitr-postgresql-using-delayed-standby/) – Step 3, to understand recovery.conf for PITR in detail.

创建`recovery.conf`来指定要执行时间点恢复的时间。请参考我们之前的[博客文章](https://www.percona.com/blog/2018/06/28/faster-point-in-time-recovery-pitr-postgresql-using-delayed-standby/)第3步，详细了解用于PITR的`recovery.conf`。

#### 步骤6：

Once all of the steps above are complete you can start PostgreSQL.
You should see the following files renamed after recovery.

完成上述所有步骤后，就可以启动PostgreSQL了。
您应该会看到在恢复后重命名的以下文件。

```
backup_label   --> backup_label.old
tablespace_map --> tablespace_map.old
recovery.conf  --> recovery.done
```

To avoid the exercise of manually modifying the tablespace_map file, you can use --tablespace-mapping . This is an option that works when you use a plain format backup, but not with tar. Let’s see why you may prefer a tar format when compared to plain.

为了避免手动修改`tablesspace_map`文件，可以使用`--tablesspace-mapping`。这是一个在使用纯格式备份时可以使用的选项，但不适用于tar。让我们看看为什么与普通格式相比，您可能更喜欢tar格式。

### Backup of PostgreSQL cluster with tablespaces using plain format

### 使用plain格式备份多表空间PostgreSQL集群

Consider the same scenario where you have a PostgreSQL cluster with two tablespaces. You might see the following error when you do not use --tablespace-mapping .

考虑具有两个表空间的PostgreSQL集群的相同场景。当不使用`--tablesspace-mapping`，您可能会看到以下错误。

```
$ pg_basebackup -h localhost -p 5432 -U postgres -D /backup/latest_backup -Fp -Xs -P -v
pg_basebackup: initiating base backup, waiting for checkpoint to complete
pg_basebackup: checkpoint completed
pg_basebackup: write-ahead log start point: 0/22000028 on timeline 1
pg_basebackup: directory "/data_pgbench" exists but is not empty
pg_basebackup: removing contents of data directory "/backup/latest_backup"
```

What the above error means is that the pg_basebackup is trying to store the tablespaces in the same location as the original tablespace directory. Here /data_pgbench is the location of tablespace : data_pgbench. And, now, pg_basebackup is trying to store the tablespace backup in the same location. In order to overcome this error, you can apply tablespace mapping using the following syntax.

上面的错误意味着`pg_basebackup`试图将表空间存储在与原始表空间目录相同的位置。`/data_pgbench`这是表空间：data_pgbench的位置。现在，`pg_basebackup`正在尝试将表空间备份存储在同一位置。为了克服这个错误，您可以使用以下语法做表空间映射。

```
$ pg_basebackup -h localhost -p 5432 -U postgres -D /backup/latest_backup -T "/data_pgbench=/pgdata_pgbench" -T "/data_pgtest=/pgdata_pgtest" -Fp -Xs -P
```

-T is used to specify the tablespace mapping. -T can be replaced by --tablespace-mapping.

`-T`用于指定表空间映射。`-T`可以替换为`--tablespace-mapping`。

The advantage of using -T ( --tablespace-mapping ) is that the tablespaces are stored separately in the mapping directories. In this example with plain format backup, you must extract all the following three directories in order to restore/recover the database using backup.

使用`-T`(`--tablesspace-mapping`)的优点是表空间分别存储在映射目录中。在这个使用`plain`格式备份的示例中，您必须提取以下三个目录，以便使用备份还原/恢复数据库。

- /backup/latest_backup

- /pgdata_pgtest

- /pgdata_pgbench

However, you do not need a tablespace_map  file in this scenario, as it is automatically taken care of by PostgreSQL.
  If you take a backup in tar format, you see all the tar files for base, tablespaces and WAL segments stored in the same backup directory, and just this directory can be extracted for performing restore/recovery. However, you must manually extract the tablespaces and WAL segments to appropriate locations and edit the tablespace_map file, as discussed above.

但是，在这种情况下，您不需要修改`tablespace_map`文件，因为它是由PostgreSQL自动处理的。
如果以tar格式进行备份，则会看到存储在同一备份目录中的`base`、`tablespaces `和`WAL`日志的所有tar文件，并且只能提取此目录以执行还原/恢复。但是，如前所述，您必须手动将`tablespaces `和`WAL`日志提取到适当的位置并编辑`tablesspace_map`文件。