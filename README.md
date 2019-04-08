## 爬虫项目之途虎养车

### 一,需求:

​	获取途虎养车所有产品的标题,价格,以及评论

### 二,环境:

1. python3.4
2. requests
3. 数据库,sqlite3
4. lxml 提供xpath

### 三,分析html:

​	其实爬虫主要就是分析网页,查看html 结构

我们进入主页:<https://www.tuhu.cn/>   既然我们要找的是商品,我点开首页,轮胎,查看所有轮胎![](<https://github.com/Tigercoll/my_picturelib/raw/master/tuhu_spider/1.png>)

一开始以为要选车型才能展示 所有轮胎,是我想多了.恩3227也商品 应该是所有关于轮胎的商品了.找到了商品页,我们就F12,分析网页结构,接下来就没什么难度了,可以用beautifulsoup,xpath,re 解析html.

我们换到其它商品,发现其它商品的结构与轮胎的不一样.除了轮胎商品,其它的页面结构都没有区别,只是url变换了而已.我们可以把他们归为一类.

这里唯一的难点就是如何找到这些商品的url.我也是偶然发现在https://item.tuhu.cn/页面里呈现了各个商品的url.

查看了商品,那么我们来看评论.F12 network 点击下一页,发现评论url:https://item.tuhu.cn/Comment/BrowseList.html?ProductID=AP-TH-CZSHZJ&pageNumber=2

观察发现AP-TH-CZSHZJ 应该是商品的ID,pageNumber=2 是页数,不过说来也奇怪3W 多条的评论,居然只能显示10页,还是很多类似商品公用一个评论的 ,为此我还特意问了他们客服.

![](<https://github.com/Tigercoll/my_picturelib/raw/master/tuhu_spider/2.png>)

商品ID 我们可以在展示页搜索到,然后用xpath匹配就可以了.

爬虫分析很重要,接下来就没什么难度了.把一些逻辑,要取的信息写成代码就好了.

### 四,上代码

```python
# 需要用到的库
import requests
# 解析网站
from lxml.etree import HTML
# 用sqlite 来存数据
import sqlite3
# 获取随即代理,防止被网站屏蔽
import random
# sleep等待时间
import time
```

```python
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36',
}
proxies_list =[
    {
    "http": "socks5://127.0.0.1:1080",
    "https": "socks5://127.0.0.1:1080",
},
    {
    "http": "http://117.191.11.102:8080",
    "https": "http://117.191.11.102:8080",
},
    {
        "http": "http://117.191.11.109:80",
        "https": "http://117.191.11.109:80",
    },
    {
        "http": "http://106.12.3.84:80",
        "https": "http://106.12.3.84:80",
    },
    {
        "http": "http://39.137.69.10:8080",
        "https": "http://39.137.69.10:8080",
    },
    {
        "http": "http://119.28.17.24:8118",
        "https": "http://119.28.17.24:8118",
    },
    {
        "http": "http://222.135.92.105:8060",
        "https": "http://222.135.92.105:8060",
    },
    {
        "http": "http://218.58.193.98:8060",
        "https": "http://218.58.193.98:8060",
    },
        ]

session = requests.Session()
# 必须要请求一次主页获取session值,不然会无线跳转报错
session.get(url='https://www.tuhu.cn/',headers=headers,proxies=random.choice(proxies_list))
```

获取轮胎页信息:

```python
def tires_spider():
    """
    获取轮胎数据
    只有轮胎是特殊页
    :return:
    """
    try:
        for i in range(1,166):
            # 从第一页开始到最后页
            tires_url = 'https://item.tuhu.cn/Tires/%s/f0.html'%i
            tires = session.get(url=tires_url,proxies=random.choice(proxies_list))
            # 打印url 方便查看哪一页出错
            print(tires_url)
            tires_html = HTML(tires.text).xpath('//*[@id="Products"]/table/tbody/tr')
            if tires_html:
                conn = sqlite3.connect('tuhu_db.sqlite3')
                with conn:
                    product_code_list = []
                    for tire in tires_html:
                        cur = conn.cursor()
                        product_name=is_null(tire.xpath('td[2]/a/div/text()'))
                        product_url=is_null(tire.xpath('td[2]/a/@href'))
                        product_price=is_null(tire.xpath('td[3]/div/strong/text()'))
                        ProductID=is_null(tire.xpath('td[3]/a/@data-pid'))
                        product_code = ProductID.split('|')[0]
                        # 存入数据库
                        insert_product_sql = "INSERT INTO product_des (product_name,product_url,product_price,product_code) VALUES (?,?,?,?)"
                        cur.execute(insert_product_sql, (product_name.strip(), product_url, product_price, product_code))
                        # 为了避免数据库锁死,存入列表后commit后再存评论
                        product_code_list.append(product_code)
                    conn.commit()
                    # 解析 评论
                for code in product_code_list:
                    parse_comment(code)
    except Exception as e:
        print(e)
        # 报错,把第几页写入文档,避免重新开始.当然可以扩展把i从文本中读取出来
        with open('1.txt','w') as f:
            f.write(str(i))
```

评论解析:

```python
def parse_comment(product_code):
    # 传入商品ID
    conn = sqlite3.connect('tuhu_db.sqlite3',timeout=3)
    with conn:
        cur = conn.cursor()
        repeat_sql='select * from Products WHERE "商品名称" = ?'
        cur.execute(repeat_sql,(product_code,))
        result = cur.fetchall()
        # 判断商品是否重复
        if not result:
            sql = "INSERT INTO Products ('商品名称') VALUES (?)"
            result = cur.execute(sql, (product_code,))
            Product_id = result.lastrowid
            print('开始爬取商品为%s的商品'%product_code)
            for i in range(1,11):
                comment_url = 'https://item.tuhu.cn/Comment/BrowseList.html?ProductID=%s&pageNumber=%s' % (product_code,i)
                comment_response  = session.get(url =comment_url,proxies=random.choice(proxies_list))
                print('comment_url:',comment_response.url)
                html = HTML(comment_response.text)
                try:
                    items = html.xpath('/html/body/div[1]/div')
                except:
                    break
                # 有第10页就没有评论的商品
                if items:
                    for item in items :
                        user = is_null(item.xpath('div[1]/span[2]/text()'))
                        address = is_null(item.xpath('div[1]/div[2]/span/text()'))
                        date =is_null(item.xpath('div[2]/div[1]/span[2]/text()'))
                        carDesc = is_null(item.xpath('div[2]/div[1]/span[3]/a/text()'))
                        shop = is_null(item.xpath('div[2]/div[1]/a/text()'))
                        comment_title = is_null(item.xpath('div[2]/div[2]/p/text()'))
                        sql = "INSERT INTO comments (product_id,user,address,date,carDesc,shop,comment_title) VALUES (?,?,?,?,?,?,?)"
                        cur.execute(sql,(Product_id,user,address,date,carDesc,shop,comment_title))
                conn.commit()
            print('%s的商品爬取结束' % product_code)
            print('休息15秒 防止IP被屏蔽')
            time.sleep(15)
        else:
            print('商品%s已存在跳过'%product_code)
```

因为获取到的xpath结果会有空列表,而空列表无法插入数据库:

```python
# 判断是否为空列表
def is_null(an_list):
    if an_list:
        return an_list[0]
    else:
        return ''
```

其他商品页就跟轮胎的类似,这里不再赘述,只是换一个xpath而已.

项目地址:<https://github.com/Tigercoll/tuhu_spider>欢迎沟通指教

<font color='red'>免责声明:仅用于个人学习、研究或欣赏。我们不保证内容的正确性。通过使用本站内容随之而来的风险与本站无关,转载请注明出处.</font>

