import requests
import jieba
import wordcloud
from requests import RequestException
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from jieba import analyse


def get_response(url):
    try:
        # 添加User-Agent，放在headers中，伪装成浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.130 Safari/537.36 Edg/79.0.309.71 '
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            return response.text
        return None
    except RequestException:
        return None


def get_news(link):
    # 获取新闻的详细信息
    html = get_response(link)
    # 使用beautifulsoup进行解析
    soup = BeautifulSoup(html, "lxml")

    # 标题
    '''
    <h1 class="main-title">证监会要求北京银行说明是否串通*ST康得管理层舞弊</h1>
    '''
    title = soup.select('.main-title')
    # 可能有小部分标题的标签不是上述格式 对其进行补充
    if not title:
        title = soup.select('#artibodyTitle')
    if title:
        title = title[0].text
    print(title)

    # 日期
    '''
    <span class="date">2019年07月20日 16:52</span>
    '''
    date = soup.select('.date')
    # 可能有小部分日期的标签不是上述格式 对其进行补充
    if not date:
        date = soup.select('#pub_date')
    if date:
        date = date[0].text
    print(date)

    # 来源
    '''
    <span class="source ent-source">中国证券报</span>
    '''
    # source = soup.select('.source')
    # 可能有小部分来源的标签不是上述格式 对其进行补充
    # if not source:
    #    source = soup.select('[data-sudaclick="media_name"]')
    # if source:
    #   source = source[0].text
    # print(source)

    # 正文
    # article = soup.select('div[class="article"] p')
    # 可能有小部分正文的标签不是上述格式 对其进行补充
    # if not article:
    #    article = soup.select('div[id="artibody"] p')
    # if article:
    # 把正文放在一个列表中 每个p标签的内容为列表的一项
    #    article_list = []
    #    for i in article:
    #        print(i.text)
    #        article_list.append(i.text)
    # 转为字典格式
    news = {'link': link, 'title': title, 'date': date}
    file_name = "sinanews.txt"
    file = open(file_name, 'a', encoding='utf-8')
    file.write(title + "    " + date + "    " + link + '\n')
    file.close()


def get_page_news():
    # 获取当前页面所有包含新闻的a标签
    news = browser.find_elements_by_xpath('//div[@class="d_list_txt"]/ul/li/span/a')
    for i in news:
        link = i.get_attribute('href')  # 得到新闻url
        print(link, i.text)
        # if not news_col.find_one({'link': link}):  # 通过url去重
        get_news(link)


if __name__ == '__main__':
    option = webdriver.ChromeOptions()
    option.add_argument('headless')  # 静默模式
    # 打开浏览器
    browser = webdriver.Chrome(options=option)
    browser.implicitly_wait(10)
    # 打开网址
    browser.get('https://news.sina.com.cn/roll/')
    f_name = "sinanews.txt"
    f = open(f_name, 'w', encoding='utf-8')
    f.truncate()
    f.close()
    # 获取当前页面新闻的url
    get_page_news()
    for i in range(2):
        try:
            # 找到下一页按钮 并点击
            '''
            <a href="javascript:void(0)" οnclick="newsList.page.next();return false;">下一页</a>
            '''
            browser.find_element_by_xpath('//*[@id="d_list"]/div/span[15]/a').click()
            # 获取下一页新闻的url
            get_page_news()
        except NoSuchElementException:
            print("NoSuchElementException")
            browser.close()
            break


textrank = analyse.textrank
adr = f_name
adrx = adr.replace('\\', '/')
print(adrx)
nmsg = open(adrx, "rb")
nmdsg = nmsg.read()
print("\nkeywords by textrank:")
keywords = textrank(nmdsg)
txt = ''
for keyword in keywords:
    print(keyword + "\n", )
    txt = txt + ' ' + keyword
w = wordcloud.WordCloud(width=1000, font_path="msyh.ttc", height=700)
w.generate(" ".join(jieba.cut(txt)))
w.to_file("aaaaa.png")
