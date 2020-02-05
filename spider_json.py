"""
用来爬取新闻的爬虫，在学长学姐的基础上稍做了修改
"""
import requests
import jieba
import wordcloud
from requests import RequestException
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from jieba import analyse
import json
import model


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
    """
    获取给定新闻链接的具体内容，并且返回一个包含该条新闻详细信息的字典
    """
    # 获取新闻的详细信息
    html = get_response(link)
    # 使用beautifulsoup进行解析
    soup = BeautifulSoup(html, "lxml")

    # 标题
    title = soup.select('.main-title')
    # 可能有小部分标题的标签不是上述格式 对其进行补充
    if not title:
        title = soup.select('#artibodyTitle')
    if title:
        title = title[0].text
    # print(title)

    # 日期
    date = soup.select('.date')
    # 可能有小部分日期的标签不是上述格式 对其进行补充
    if not date:
        date = soup.select('#pub_date')
    if date:
        date = date[0].text
    # print(date)
    news_dict = {'link': link, 'title': title, 'date': date}
    """
    连续的IO太过消耗资源
    file_name = "sinanews.txt"
    file = open(file_name, 'a', encoding='utf-8')
    file.write(title + " " + date + " " + link + '\n')
    file.close()
    """
    return news_dict


def get_page_news():
    """
    获取浏览器当前页的所有新闻
    """
    news_list = []
    # 获取当前页面所有包含新闻的a标签
    all_news = browser.find_elements_by_xpath('//div[@class="d_list_txt"]/ul/li/span/a')
    for news in all_news:
        link = news.get_attribute('href')  # 得到新闻url
        # 调试用，打印爬取到的相关信息
        # print(link, news.text)
        new_dict = get_news(link)
        news_list.append(new_dict)
    return news_list


if __name__ == '__main__':
    # 结果列表，最后序列化入
    result_list = []
    # 设置一个浏览器选项
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
    result_list += get_page_news()
    for i in range(2):
        try:
            # 找到下一页按钮 并点击
            '''
            <a href="javascript:void(0)" οnclick="newsList.page.next();return false;">下一页</a>
            '''
            browser.find_element_by_xpath('//*[@id="d_list"]/div/span[15]/a').click()
            # 获取下一页新闻的url
            result_list += get_page_news()
        except NoSuchElementException:
            print("NoSuchElementException")
            browser.close()
            break
    # 在这里将结果写入json文件或者存入数据库
    for result in result_list:
        sina_news = model.SinaNews(id=None, title=result['title'], date=result['date'], link=result['link'])
        sina_news.save()
    # 对结果进行分析，形成词云
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
