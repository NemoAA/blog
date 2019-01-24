## Advanced Password Checks

## 高级密码校验

12 Jan 2018
Tags: [postgres](https://paquier.xyz/tag/postgres), [postgresql](https://paquier.xyz/tag/postgresql), [pg_plugins](https://paquier.xyz/tag/pg_plugins), [passwordcheck](https://paquier.xyz/tag/passwordcheck)

[passwordcheck](https://www.postgresql.org/docs/devel/static/passwordcheck.html) is a PostgreSQL contrib module able to check if raw password strings are able to respect some policies. For encrypted password, which is what should be used in most cases to avoid passing plain text passwords over the wire have limited checks, still it is possible to check for example for MD5-hashed entries if they match the user name. For plain text password, things get a bit more advanced, with the following characteristics:

`passwordcheck`是一个PostgreSQLcontrib模块，能够检查原始密码字符串是否能够符合某些策略。对于加密密码(这是在大多数情况下应使用的，以避免通过线路传递明文密码的检查有限)，仍然可以检查(例如，MD5散列值是否与用户名匹配)。对于明文密码，情况会更高级一些，具有以下特征：

- Minimum length of 8 characters.
- 最小长度8字节
- Check if password has the user name.
- 检查密码是否包含了用户名
- Check if password includes both letters and non-letters.
- 检查密码是否包含字母和非字母
- Optionally use cracklib for more checks.
- 可选择使用cracklib做更多的检查

Note that all those characteristics are decided at compilation time and that it is not possible to configure it, except by forking the code and creating your own module. [passwordcheck_extra](https://github.com/michaelpq/pg_plugins/tree/master/passwordcheck_extra) is a small module that I have written to make things more flexible with a set of configuration parameters aimed at simplifying administration:

请注意，所有这些特性都是在编译时确定的，之后不能再对其进行配置，除非通过复制代码然后创建您自己的模块。passwordcheck_tra是我编写的一个小模块，它通过一组旨在简化管理的配置参数使事情变得更加灵活：

- Minimum length of password.
- 密码的最小长度
- Maximum length of password.
  密码的最大长度
- Define a custom list of special characters.
- 定义特殊字符串的自定义列表
- Decide if password should include at least one special character, one lower-case character, one number or one upper-case character (any combination is possible as there is one switch per type).
- 决定密码是否应该包含至少一个特殊符号，一个小写字符，一个数字或一个大写字符（由于每种字符都有一个开关因此可以任意组合）

In order to enable this module, you should update shared_preload_libraries and list it:

为了启用这个模块，你应该修改shared_preload_libraries，如下操作 ：

```
shared_preload_libraries = 'passwordcheck_extra'
```

And then this allows for more fancy checks than the native module, for example here to enforce only numbers to be present, with a length enforced between 4 and 6 (don’t do that at home):

然后，这允许比原生模块执行更多特定的检查，例如，此处强制包含数字，强制长度在4到6之间(不要在家里执行)：

```
=# LOAD 'passwordcheck_extra';
LOAD
=# SET passwordcheck_extra.restrict_lower = false;
SET
=# SET passwordcheck_extra.restrict_upper = false;
SET
=# SET passwordcheck_extra.restrict_special = false;
SET
=# SET passwordcheck_extra.minimum_length = 4;
SET
=# SET passwordcheck_extra.maximum_length = 6;
SET
=# CREATE ROLE hoge PASSWORD 'foobar';
ERROR:  22023: Incorrect password format: number missing
=# CREATE ROLE hoge PASSWORD 'fooba1';
CREATE ROLE
```

One property to note is that all error messages concatenate, so for example if all the previous parameters are switched to true, you get more advanced knowledge of what is missing (error message format is split into multiple lines for the reader’s sake):

需要注意的一个属性是，所有错误消息都是串联的，因此，例如，如果所有先前的参数都切换为true，您就可以更深入地了解所缺少的内容(为了方便读者，错误消息格式被分成多行)：

```
=# CREATE ROLE hoge PASSWORD '1234';
ERROR:  22023: Incorrect password format:
    lower-case character missing,
    upper-case character missing,
    special character missing (needs to be one listed in "!@#$%^&*()_+{}|<>?=")
```

More fancy things could be done, like using counters to decide at least a number of character for each type to be present. Have fun.

还可以做更多新奇的事情，比如使用计数器来决定每个类型至少有多少个字符。玩得开心!