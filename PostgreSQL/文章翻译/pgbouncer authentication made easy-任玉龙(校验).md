# PGBOUNCER AUTHENTICATION MADE EASY

文章翻译自https://www.cybertec-postgresql.com/en/pgbouncer-authentication-made-easy/

Posted on [10. January 2019](https://www.cybertec-postgresql.com/en/pgbouncer-authentication-made-easy/) by [Laurenz Albe](https://www.cybertec-postgresql.com/en/author/cybertec_albe/)

pgbouncer是PostgreSQL中使用最广泛的连接池。

本博客将提供如何使用pgbouncer配置用户身份验证。

我使用Fedora Linux编写了这本书，并使用下载站点提供的PGDG Linux RPM包安装了pgbouncer。

但它在任何地方都应该非常类似。

## 什么是连接池？

将max_connections设置为高值会影响性能，如果所有这些连接同时处于活动状态，甚至会使数据库瘫痪。

此外，如果数据库连接是短期的，那么仅仅打开数据库连接就会浪费大量的数据库资源。

为了解决这两个问题，我们需要一个连接池。连接池是客户机和数据库之间的代理:客户机连接到连接池，连接池通过一组相对稳定的持久数据库连接(“连接池”)处理SQL请求。

由于客户机连接到pgbouncer，因此它必须能够对它们进行身份验证，因此我们必须相应地对其进行配置。

## 非常简单的方法(身份验证文件)

![img](https://ws3.sinaimg.cn/large/006tNc79ly1fzaugxqfw4j31uo0u0kf4.jpg)

如果数据库用户数量很少且密码不经常更改，则此方法非常有用。

为此，我们在pgbouncer配置目录中创建一个配置文件userlist.txt(在我的系统/etc/pgbouncer下)。
该文件包含数据库用户及其密码，因此pgbouncer可以在不求助于数据库服务器的情况下对客户机进行身份验证。
它是这样的:

```
"laurenz" "md565b6fad0e85688f3f101065bc39552df"
"postgres" "md553f48b7c4b76a86ce72276c5755f217d"
```

可以使用pg_shadow目录表中的信息手工编写文件，也可以自动创建文件。
要想成功，你需要：

（1）PostgreSQL命令行工具psql
如果它不在你的环境变量路径上，你将不得不使用绝对路径(类似于/usr/pgsql-11/bin/psql或“C:\程序文件\PostgreSQL\11\bin\psql”)。
（2）对pgbouncer配置文件的写访问，这可能要求你以根用户或管理员的身份运行它。

然后你可以像这样简单地创建文件:

```
psql -Atq -U postgres -d postgres -c "SELECT concat('\"', usename, '\" \"', passwd, '\"') FROM pg_shadow"
```

创建了用户列表userlist.txt 之后，将以下内容添加到/etc/pgbouncer/pgbouncer.ini

```
[pgbouncer]
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt/userlist.txt
```

## 稍微复杂一点的方法(查询数据库)

![img](https://ws3.sinaimg.cn/large/006tNc79ly1fzauh4sbi1j32no0qmkbn.jpg)

如果用户和密码经常更改，那么必须一直更改用户列表就很烦人了。
在这种情况下，最好使用“身份验证用户”，该用户可以连接到数据库并从中获取密码。

你不希望每个人都看到你的数据库密码，因此我们只允许这个身份验证用户访问密码。
使用psql，我们作为超级用户连接到数据库，并运行以下操作:

```
CREATE ROLE pgbouncer LOGIN;
-- set a password for the user
\password pgbouncer
 
CREATE FUNCTION public.lookup (
   INOUT p_user     name,
   OUT   p_password text
) RETURNS record
   LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog AS
$$SELECT usename, passwd FROM pg_shadow WHERE usename = p_user$$;
 
-- make sure only "pgbouncer" can use the function
REVOKE EXECUTE ON FUNCTION public.lookup(name) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.lookup(name) TO pgbouncer;
```

pg_shadow只对超级用户开放，因此我们创建了一个安全定义函数，让pgbouncer访问密码。

然后我们必须创建一个userlist.txt文件，但它将只包含一个用户pgbouncer。

/etc/ pgbouncer/pgbouncer/pgbouncer.ini中的配置文件应该是这样的:

```
[pgbouncer]
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
auth_user = pgbouncer
auth_query = SELECT p_user, p_password FROM public.lookup($1)
```

现在，每当你以pgbouncer以外的用户身份进行身份验证时，数据库将查询该用户的当前密码。

由于auth_query连接将建立到目标数据库，因此需要将该函数添加到希望使用pgbouncer访问的每个数据库中。

## 使用pg_hba.conf进行高级身份验证

你可以使用pg_hba.conf文件确定pgbouncer将接受和拒绝哪些连接。虽然pgbouncer只接受PostgreSQL提供的认证方法的一个子集。

为了只允许来自两个应用服务器的连接，文件可以如下所示:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    mydatabase      appuser         72.32.157.230/32        md5
host    mydatabase      appuser         217.196.149.50/32       md5
```

如果文件名为/etc/pgbouncer/pg_hba.conf。你的pgbouncer.ini看起来是这样的:

```
[pgbouncer]
auth_type = hba
auth_hba_file = /etc/pgbouncer/pg_hba.conf
auth_file = /etc/pgbouncer/userlist.txt
```

当然，您也可以在这种情况下使用auth_query。