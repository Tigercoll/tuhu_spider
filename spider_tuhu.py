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

# 判断是否为空列表
def is_null(an_list):
    if an_list:
        return an_list[0]
    else:
        return ''

def parse_comment(product_code):
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
# 爬取途虎保养页面
def tuhu_by(end,start_url):
    # 循环所有的保养产品页面
    for i in range(1,end):
        start_url = start_url%i
        r = session.get(url=start_url,proxies=random.choice(proxies_list))
        # 解析页面里的产品
        html = HTML(r.text)
        products = html.xpath('//*[@id="Products"]/ul/li/div/form/input[1]/@value')
        for Product_name in set(products):
            parse_comment(Product_name)

def parase_response(start_url):
    flag = True
    try:
        # with open('2.txt','r') as f:
        #     start_url=f.read().strip()
        while flag:
            product_code_list = []
            print('start_url:',start_url)
            r = session.get(url=start_url,proxies=random.choice(proxies_list))
            print(r.status_code)
            if r.status_code != 200:
                # 被屏蔽后可以更换地址 待扩展
                raise  Exception('地址被屏蔽')
            print('解析页面获取商品')
            html = HTML(r.text)
            products_html = html.xpath('//*[@id="Products"]/ul/li/div')
            conn = sqlite3.connect('tuhu_db.sqlite3')
            with conn:
                cur = conn.cursor()
                if products_html:
                    for product in products_html:
                        product_name = is_null(product.xpath('a/text()'))
                        product_url = is_null(product.xpath('a/@href'))
                        product_price = is_null(product.xpath('div/strong/text()'))
                        product_code = is_null(product.xpath('form/input[1]/@value'))
                        insert_product_sql = "INSERT INTO product_des (product_name,product_url,product_price,product_code) VALUES (?,?,?,?)"
                        cur.execute(insert_product_sql, (product_name.strip(), product_url, product_price, product_code))
                        product_code_list.append(product_code)

                conn.commit()

            for code in product_code_list:
                parse_comment(code)
            # 如果没有下一页则循环
            start_url = is_null(html.xpath('//*[@class="last-child"]/@href'))
            if not start_url:
                flag = False
    except Exception as e:
        print(e)
        with open('2.txt','a') as f:
            f.write(start_url+str(e)+'\n')
        conn = sqlite3.connect('tuhu_db.sqlite3')
        conn.commit()
        conn.close()
# 获取轮胎数据
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
            print(tires.status_code)
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
                        insert_product_sql = "INSERT INTO product_des (product_name,product_url,product_price,product_code) VALUES (?,?,?,?)"
                        cur.execute(insert_product_sql, (product_name.strip(), product_url, product_price, product_code))
                        product_code_list.append(product_code)
                    conn.commit()
                    # 解析 评论
                for code in product_code_list:
                    parse_comment(code)
    except Exception as e:
        print(e)
        with open('1.txt','w') as f:
            f.write(str(i))
def main():
    #爬取轮胎页
    # tires_spider()
    # 保养URL:https://item.tuhu.cn/List/BY/1.html
    # 车品url:https://item.tuhu.cn/List/AP/1.html
    # 轮毂URL:https://item.tuhu.cn/List/Shipei/1.html
    # 美容url:https://item.tuhu.cn/List/Beauty/1.html
    # 玻璃URL:https://item.tuhu.cn/List/QCBL/1.html
    # 以上网站类似
    urls = ['https://item.tuhu.cn/List/BY/53.html','https://item.tuhu.cn/List/AP/24.html','https://item.tuhu.cn/List/Shipei/15.html','https://item.tuhu.cn/List/Beauty/3.html','https://item.tuhu.cn/List/QCBL/1.html']
    for url in urls:
        parase_response(url)



if __name__ == '__main__':
    main()