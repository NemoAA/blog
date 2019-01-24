## Postgres migrating SQL_ASCII to UTF-8 with fix_latin 

> 文章翻译自https://www.endpoint.com/blog/2017/07/21/postgres-migrating-sqlascii-to-utf-8

By [Greg Sabino Mullane](https://www.endpoint.com/blog/authors/greg-sabino-mullane)   

July 21, 2017 

现在升级Postgres并不像以前那样麻烦，主要得益于pg_upgrade程序，但有时它根本无法使用。我们最近有一个现有的End Point客户端需要从当前的Postgres数据库（版本9.2）升级到最新版本（9.6-但很快就会发布10）。他们还希望从SQL_ASCII编码转向UTF-8。这意味着无法使用pg_upgrade进行升级，我们也借此机会启用了校验和（此更改无法通过pg_upgrade完成）。最后，将数据库服务器迁移到新硬件。在迁移过程中，有许多经验教训和波折，但在这篇文章中，我想重点谈谈最令人烦恼的问题之一，即数据库编码问题。

创建Postgres数据库时，会要设置特定编码。最常见的一个是“UTF8”（默认值）。 这涵盖了所有用户99％的需求。第二常见的是“SQL_ASCII”编码，应该命名为“危险不要使用此编码”，因为它会导致麻烦。SQL_ASCII编码不代表任何编码，只是存储你抛出的字节。这意味着数据库最终包含了大量不同的编码，创建了一个“byte soup ”，要转换成真正的编码（即UTF-8）很难实现。

有许多文本转换工具可以将一种编码转换为另一种编码。Unix上最受欢迎的一个是“iconv”。 虽然这个程序做得很好，但如果源文本使用一种编码，在遇到遇“byte soup ”时会失败。

对于此迁移，我们首先使用pg_dump旧数据库到新创建的UTF-8测试数据库，只是为了查看哪些表存在编码问题。 相当多，但不是全部！所以我们编写了一个脚本来并行导入表，并对问题进行了一些过滤。如上所述，iconv并不是特别有用，仔细查看表格，可以看出每个表格中有许多不同编码的证据：Windows-1252，ISO-8859-1，日语，希腊语和其它许多编码。 甚至还有大量的明显二进制数据（例如图像），它们只是以某种方式被推入文本字段。 这是SQL_ASCII的一个大问题：它接受所有内容，并且不进行任何验证。 即使添加了// IGNORE选项，iconv程序也无法处理这些表。 

为了更好地解释问题和寻找解决方案，让我们创建一个包含混杂编码的小文本文件。这里避免讨论UTF-8如何表示字符及其与Unicode的交互，因为Unicode是一个密集、复杂的主题，本文已经有足够干货了。 

首先，我们想要使用编码'Windows-1252'和'Latin-1'添加一些项目。这些编码系统试图扩展基本ASCII字符集以包含更多字符。由于这些编码发明早于UTF-8，因此它们以非常不优雅（且不兼容）的方式进行。使用“echo”命令是向文件添加任意字节的好方法，因为它允许直接十六进制输入： 

```
$ echo -e "[Windows-1252]   Euro: \x80   Double dagger: \x87" > sample.data
$ echo -e "[Latin-1]   Yen: \xa5   Half: \xbd" >> sample.data
$ echo -e "[Japanese]   Ship: \xe8\x88\xb9" >> sample.data
$ echo -e "[Invalid UTF-8]  Blob: \xf4\xa5\xa3\xa5" >> sample.data
```

这个文件看起来很难看。当我们直接查看文件时，请注意所有“错误”字符：

```
$ cat sample.data
[Windows-1252]   Euro: �   Double dagger: �
[Latin-1]   Yen: �   Half: �
[Japanese]   Ship: 船
[Invalid UTF-8]  Blob: ���� 
```

运行iconv几乎没有帮助： 

```
## With no source encoding given, it errors on the Euro:
$ iconv -t utf8 sample.data >/dev/null
iconv: illegal input sequence at position 23

## We can tell it to ignore those errors, but it still barfs on the blob:
$ iconv -t utf8//ignore sample.data >/dev/null
iconv: illegal input sequence at position 123

## Telling it the source is Window-1252 fixes some things, but still sinks the Ship:
$ iconv -f windows-1252 -t utf8//ignore sample.data
[Windows-1252]   Euro: €   Double dagger: ‡
[Latin-1]   Yen: ¥   Half: ½
[Japanese]   Ship: èˆ¹
[Invalid UTF-8]  Blob: ô¥£¥
```

在测试了一些其它工具之后，我们发现了一个好用的工具：Encoding :: FixLatin，一个Perl模块，它提供了一个名为“fix_latin”的命令行程序。 它不是像iconv一样具有权威性，而是尽力通过有根据的猜测来解决问题。 其文档提供了一个很好的总结： 

- 该脚本充当过滤器，获取可能包含ASCII，UTF8，ISO8859-1和CP1252字符混合的源数据，并且生成输出全部为ASCII / UTF8。       

- 多字节UTF8字符将保持不变（尽管过长的UTF8字节序列将转换为最短的正常形式）。 单字节字符将按如下方式转换：0x00  -  0x7F ASCII  - 通过未更改的0x80传递 -  0x9F使用CP1252映射转换为UTF8 0xA0  -  0xFF使用Latin-1映射转换为UTF8 

虽然这对于修复Windows-1252和Latin-1问题（因此至少占我们表格的不良编码的95％）非常有用，但它仍然允许“无效”的UTF-8传递通过。 这意味着Postgres仍然会拒绝接受它。 我们来看看测试文件： 

```
$ fix_latin sample.data
[Windows-1252]   Euro: €   Double dagger: ‡
[Latin-1]   Yen: ¥   Half: ½
[Japanese]   Ship: 船
[Invalid UTF-8]  Blob: ����

## Postgres will refuse to import that last part:
$ echo "SELECT E'"  "$(fix_latin sample.data)"  "';" | psql
ERROR:  invalid byte sequence for encoding "UTF8": 0xf4 0xa5 0xa3 0xa5

## Even adding iconv is of no help:
$ echo "SELECT E'"  "$(fix_latin sample.data | iconv -t utf-8)"  "';" | psql
ERROR:  invalid byte sequence for encoding "UTF8": 0xf4 0xa5 0xa3 0xa5
```

UTF-8规范相当密集，对编码器和解码器提出了许多要求。当然，程序如何实现这些需求(和可选的位)是不同的。但是在一天结束时，我们需要将这些数据导入UTF-8编码的Postgres数据库而不出现问题。如有疑问，请到源头！ Postgres源代码中负责拒绝不符合UTF-8编码的的相关文件（如上例所示）是src / backend / utils / mb / wchar.c分析该文件显示一小段代码，其工作是确保只接受“合法”的UTF-8： 

```
bool
pg_utf8_islegal(const unsigned char *source, int length)
{
  unsigned char a;

  switch (length)
  {
    default:
      /* reject lengths 5 and 6 for now */
      return false;
    case 4:
      a = source[3];
      if (a < 0x80 || a > 0xBF)
        return false;
      /* FALL THRU */
    case 3:
      a = source[2];
      if (a < 0x80 || a > 0xBF)
        return false;
      /* FALL THRU */
    case 2:
      a = source[1];
      switch (*source)
      {
        case 0xE0:
          if (a < 0xA0 || a > 0xBF)
            return false;
          break;
        case 0xED:
          if (a < 0x80 || a > 0x9F)
            return false;
          break;
        case 0xF0:
          if (a < 0x90 || a > 0xBF)
            return false;
          break;
        case 0xF4:
          if (a < 0x80 || a > 0x8F)
            return false;
          break;
        default:
          if (a < 0x80 || a > 0xBF)
            return false;
          break;
      }
      /* FALL THRU */
    case 1:
      a = *source;
      if (a >= 0x80 && a < 0xC2)
        return false;
      if (a > 0xF4)
        return false;
      break;
  }
  return true;
}
```

既然我们知道Postgres的UTF-8规则，我们如何确保我们的数据遵循它？虽然我们可以在fix_latin之后运行另一个独立过滤器，但这会增加迁移时间。所以我快速修补了fix_latin程序本身，在Perl中重写了那个C逻辑。添加了一个新选项“--strict-utf8”。它的工作是简单地执行Postgres源代码中的规则。如果一个字符无效，则将其替换为问号（替换字符还有其它选择，但我们认为简单的问号是快速而简单的，并且无论如何都不可能读取或甚至使用周围的数据）。

瞧！ 所有的数据现在都没有问题地进入Postgres。注意： 

```
$ echo "SELECT E'"  "$(fix_latin  sample.data)"  "';" | psql
ERROR:  invalid byte sequence for encoding "UTF8": 0xf4 0xa5 0xa3 0xa5

$ echo "SELECT E'"  "$(fix_latin --strict-utf8 sample.data)"  "';" | psql
                   ?column?
----------------------------------------------
  [Windows-1252]   Euro: €   Double dagger: ‡+
 [Latin-1]   Yen: ¥   Half: ½                +
 [Japanese]   Ship: 船                       +
 [Invalid UTF-8]  Blob: ????
(1 row)
```

这里有什么教训？ 首先，永远不要使用SQL_ASCII。它已经过时，很危险，并会造成很大的麻烦。其次，有多个客户端编码在使用，特别是对于旧数据，但是现在世界上已经基于UTF-8的标准化，所以你遇到SQL_ASCII，Windows-1252和其他异常的情况会很少。第三，不要害怕去数据源找问题。如果Postgres拒绝你的数据，这可能是一个很好的理由，所以找出原因。在这次迁移中还有其它挑战要克服，但编码肯定是最有趣的挑战之一。客户和我们的每个人都非常高兴终于转换成UTF-8了！ 
