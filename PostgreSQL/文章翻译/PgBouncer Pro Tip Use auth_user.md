# PgBouncer Pro Tip: Use auth_user

> [文章翻译自](http://richyen.com/pgbouncer/postgres/2018/11/21/pgbouncer_auth_user.html )

## 介绍

任何一个超过一百个用户的在生产环境中运行数据库都应该考虑使用连接池来控制资源的使用。`PgBouncer`就是这样一个很棒的工具，它很轻巧，可以为具有特定需求的DBA提供了一些很好的功能。 

我要分享的这些功能之一是`auth_user`和`auth_query`组合，它可以替代使用`userlist.txt`的默认身份验证过程。你可能会问：“`userlist.txt`有什么问题吗”。首先，它使用户/角色管理有点繁琐。每次向PG添加新用户时，都需要将其添加到`PgBouncer`中的`userlist.txt`。每次更改密码时，也必须在`userlist.txt`中更改密码。假如你总共管理30多台服务器，这将是一个系统管理员的噩梦。使用`auth_user`和`auth_query`，可以集中管理密码并从清单中提取任意一项。

##  什么是auth_user？ 

在`pgbouncer.ini`的`[databases]`部分中，通常会指定一个`user =`和`password =`，`PgBouncer`将使用该用户连接到Postgres数据库。如果该部分留空，则需要在连接字符串处声明用户/密码（即`psql -U <username> <database>` ）。发生这种情况时，`PgBouncer`将在`userlist.txt`所提供的用户名/密码中查找，以验证身份凭据是否正确，然后将用户名/密码发送到Postgres以进行实际的数据库登录。 

当提供`auth_user`时，`PgBouncer`仍将从连接字符串中读取身份凭据，但不是与`userlist.txt`进行比较，而是使用指定的`auth_user`（最好是非超级用户）登录Postgres并运行`auth_query`以提取所需用户相应md5密码的哈希值。此时将执行验证，如果正确，则允许指定的用户登录。 

## 一个例子 

假设已安装并运行Postgres，可以使用以下步骤运行`auth_user`和`auth_query`组合：

- 创建一个Postgres用户以用作`auth_user`     

- 在Postgres中创建用户/密码查找函数    

- 配置`pgbouncer.ini `

### 1.创建一个Postgres用户以用作auth_user 

在你的终端中，创建myauthuser用户：

```sql
psql -c“CREATE ROLE myauthuser WITH PASSWORD 'abc123'”
```

请注意，myauthuser应该是一个无特权的用户，没有权限来读/写任何表。 myauthuser用于协助`PgBouncer`身份验证。

出于此示例的目的，我们还将拥有一个名为mydbuser的数据库用户，可以使用以下命令创建： 

```sql
CREATE ROLE mydbuser WITH PASSWORD 'mysecretpassword'
GRANT SELECT ON emp TO mydbuser;
```

### 2.在Postgres中创建用户/密码查找函数

在`psql`提示符下，创建一个myauthuser用户执行用户/密码查找的函数：  

```sql
CREATE OR REPLACE FUNCTION user_search(uname TEXT) RETURNS TABLE (usename name, passwd text) as
$$
  SELECT usename, passwd FROM pg_shadow WHERE usename=$1;
$$
LANGUAGE sql SECURITY DEFINER;
```

如文档中所述，`SECURITY DEFINER`子句允许非特权myauthuser查看`pg_shadow`的内容，否则这些内容仅限于管理员用户。 

### 3.配置pgbouncer.ini  

配置`pgbouncer.ini`中`[databases]`部分，例如：

```shell
[databases]
foodb = host=db1 dbname=edb auth_user=myauthuser
```

然后，在`[pgbouncer]`部分配置`auth_query`： 

```shell
auth_query = SELECT usename, passwd FROM user_search($1)
```

### 4.尝试登陆

```shell
PGPASSWORD=thewrongpassword psql -h 127.0.0.1 -p 6432 -U mydbuser -Atc 'SELECT '\''success'\''' foodb
psql: ERROR:  Auth failed
PGPASSWORD=mysecretpassword psql -h 127.0.0.1 -p 6432 -U mydbuser -Atc 'SELECT '\''success'\''' foodb
success
```

如上所见，为mydbuser提供了错误的密码导致`pg_shadow`查找失败，并且用户无法登录。后续的`psql`调用使用了正确的密码，并成功登录。 

## 一些说明

我见过一些客户试图实现这个功能，但有一个常见错误就是未能在Postgres中正确设置`pg_hba.conf`。 请记住，一旦验证了提供的身份凭据，`PgBouncer`将尝试使用指定的用户登录。 因此，如果你的`auth_user`是myauthuser并且你的`pg_hba.conf`是`host all myauthuser 127.0.0.1/32 md5` ，但你想最终使用mydbuser登录，你将无法这样做，因为在`pg_hba.conf` 中没有mydbuser用户的认证，你可能会看到报错： 

```shell
server login failed: FATAL no pg_hba.conf entry for host "127.0.0.1", user "mydbuser", database "edb", SSL off
```

另外，请确保`pgbouncer.ini` 中`auth_type`未设置为`trust`   - 相反，应该在`pg_hba.conf`中为`auth_user`设置信任，并将其限制为`PgBouncer`的IP。 将`auth_type`设置为md5，以便使用密码请求对您的登录尝试提出提示。 