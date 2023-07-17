import os
import random
import shutil

import requests
import re
from bs4 import BeautifulSoup
import datetime
import json
import time
import shutil
import traceback

KEYS = ['deepfake detection', "forgery detection", "action recognition", "domain generalization", "anomaly detection"]
data, papers = {}, {}
DateNow = datetime.date.today()
DateNow = str(DateNow)
DateNow = DateNow.replace('-', '.')
per_key_papers = 100  # 只取15条


# 对字典排序
def sort_papers(papers):
    output = dict()
    # keys = list(papers.keys())
    pattern = re.compile(u'\|\*\*(.*?)\*\*\|')
    sort_dict = sorted(papers.items(), key=lambda x:datetime.datetime.strptime(re.match(pattern,x[1]).group(0).replace("*","").replace("|",""), '%Y-%m-%d'), reverse=True)
    for key, value in sort_dict:
        output[key] = papers[key]
    return output

# 参考连接 https://zhuanlan.zhihu.com/p/425670267
# 转换日期为标准格式 https://blog.csdn.net/weixin_43751840/article/details/89947528
def get_paper_from_arxiv(key):
    query_key = key.replace(" ", "+")
    url = f"https://arxiv.org/search/cs?query={query_key}&searchtype=title&abstracts=show&order=-submitted_date&size=25"
    res = requests.get(url)
    content = BeautifulSoup(res.text, 'html.parser')
    data[key], papers[key] = {}, {}
    count = 1

    # 正则匹配http
    pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')  # 匹配模式
    for arxiv_result in content.find(name="ol").find_all(name='li'):
        if count > per_key_papers: break
        paper_url = arxiv_result.find(attrs={'class': 'list-title'}).a['href']
        abstract = arxiv_result.find(class_="abstract-full")  # 只返回当前节点的text不包括子节点
        code_url = re.search(pattern, abstract.text)
        code_url = code_url.group() if code_url else "-"
        if abstract.a: abstract.a.extract()  # 去除a标签里的额外文本
        abstract = abstract.text.strip()
        title = arxiv_result.find(class_='title')  # class是关键字所以要加下划线_
        title = title.text.strip()  # replace("<span class=\"search-hit mathjax\">Source</span>","").replace("</span>")text直接取出来了
        author = [au.strip() for au in arxiv_result.find(class_='authors').text.replace("\n", "").split(",")]
        # author = ",".join(author)
        author = author[0].replace("Authors:", "") + "et.al"  # 只取一作
        submit_date = [item.text.replace("\n", "").replace("  ", "") for item in arxiv_result.select("p.is-size-7")]
        time_format = datetime.datetime.strptime(submit_date[0].split(";")[0], 'Submitted %d %B, %Y')
        format_date = f"{time_format.year}-{time_format.month}-{time_format.day}"
        if len(submit_date) > 1:
            comments = submit_date[1]
            # 有时代码链接在commnets里
            if code_url == "-":
                code_url = re.search(pattern, comments)
                code_url = code_url.group() if code_url else "-"
            comments = comments.replace(";", ".").split(",")[0].split(".")[0].replace("Comments:", "").replace("Accepted at ", "").replace("Accepted to ", "")
            if "pages" in comments:
                comments = "-"
        else:
            comments = "-"
        # json_res.append(result)
        # f.write("|Publish Date|Title|Authors|PDF|Code|Comments|\n" + "|---|---|---|---|\n")
        code_url = f"[code]({code_url})|" if code_url != "-" else "-|"
        if title not in papers:
            # 会议相关折叠
            comments = f"<details><summary>detail</summary>{comments}</details>" if comments != "-" else "-"
            #comments = f"<details>{comments}</details>" if comments != "-" else "-"
            papers[key][title] = f"|**{format_date}**|**{title}**|{author}|[paper]({paper_url})|" + code_url + f"{comments}|\n"
            data[key][title] = {'date':format_date, 'author':author, 'paper_url':paper_url, 'code_url':code_url, 'comments':comments}
        # print(code_url)
        count += 1


def get_paper_from_google(key):
    headers = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.61',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 Edg/86.0.622.63',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36 Edg/86.0.622.43',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.63',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4346.0 Safari/537.36 Edg/89.0.731.0',
        ]
    query_key = key.replace(" ", "+")
    query_domain = random.choice(["scholar.lanfanshu.cn"]) # "scholar.google.com.hk",
    url = f"https://{query_domain}/scholar?as_vis=0&q=allintitle:+{query_key}&hl=zh-CN&scisbd=1&as_sdt=0,5"
    header = random.choice(headers)
    print(url,header)
    #url = f"https://sc.panda321.com/scholar?as_vis=0&q=allintitle:+{query_key}&hl=zh-CN&scisbd=1&as_sdt=0,5"
    res = requests.get(url, headers={"User-Agent": header}, timeout=10)
    content = BeautifulSoup(res.text, 'html.parser')
    body = content.find(id="gs_res_ccl_mid")
    # 谷歌学术爬虫
    now = datetime.datetime.today()
    count = 1
    for div in body.find_all(class_="gs_r gs_or gs_scl"):
        if count > per_key_papers: break
        main = div.find(id=div.attrs['data-cid'])
        paper_url = main.attrs['href']
        title = main.text.strip()
        submit_date = div.find(class_="gs_age").text.strip()
        author_and_comment = div.find(class_="gs_a").text.strip()
        author = author_and_comment.split(",")[0] + " et.al"
        comment = " ".join([item.strip() for item in author_and_comment.split("-")[1:]])
        # code_url = f"https://paperswithcode.com/api/v1/papers/{query_title}/repositories/"
        code_url = f"https://paperswithcode.com/api/v1/search/?q={title}&page=1"
        code_res = requests.get(code_url, timeout=5).json()
        if code_res['count'] != 0:
            code_res = code_res['results'][0]
            if "proceeding" in code_res:
                comment = code_res["proceeding"]
            if "repository" in code_res and code_res["repository"] is not None:
                code_url = code_res["repository"]["url"]
            else:
                code_url = "https://paperswithcode.com/paper/" + code_res["paper"]['id']
        else:
            code_url = "-"
        #     if code_res.status_code == 200:
        #         code_res = code_res.json()['results']
        #         code_res = sort()
        if "arXiv " in comment:
            comment = "-"
        time_format = now - datetime.timedelta(days=int(submit_date.split(" ")[0]))
        format_date = f"{time_format.year}-{time_format.month}-{time_format.day}"
        # code_res.close()
        if title not in papers:
            # 会议相关折叠
            comment = f"<details><summary>detail</summary>{comment}</details>" if comment != "-" else "-"
            if code_url[-1] == '.': 
                code_url = code_url[:-1]
            code_url = f"[code]({code_url})|" if code_url != "-" else "-|"
            papers[key][title] = f"|**{format_date}**|**{title}**|{author}|[paper]({paper_url})|" + code_url + f"{comment}|\n"
            data[key][title] = {'date': format_date, 'author': author, 'paper_url': paper_url, 'code_url': code_url, 'comments': comment}
        print(code_url)
        count += 1



def json_to_md(data):
    with open("papers.json", "r") as f:
        content = f.read()
        if not content:
            data = {}
        else:
            data = json.loads(content)

    md_filename = "README.md"

    # clean README.md if daily already exist else create it
    with open(md_filename, "w+", encoding='utf_8') as f:
        f.write(f"## CV Papers Daily\n")
        #f.write("<details>\n")
        #f.write("  <summary>Table of Contents</summary>\n")
        #f.write("  <ol>\n")
        for keyword in data.keys():
            day_content = data[keyword]
            if not day_content:
                continue
            kw = keyword.replace(" ", "-")
            f.write(f"- [{keyword}](#{kw})\n")
            #f.write(f"    <li><a href=#{kw}>{keyword}</a></li>\n")
        #f.write("  </ol>\n")
        #f.write("</details>\n\n")
        f.write("\n\n")
        # pass

    # write data into README.md
    with open(md_filename, "a+",encoding='utf_8') as f:

        f.write("## Updated on " + DateNow + "\n\n")

        for keyword in data.keys():
            day_content = data[keyword]
            if not day_content:
                continue
            # the head of each part
            f.write(f"## {keyword}\n\n")
            f.write("|Date|Title|Authors|PDF|Code|Comments|\n")
            # "|---|---|---|---|---|---|\n"
            f.write("|:------|:---------------------|:---|:-|:-|:---|\n")
            # sort papers by date
            day_content = sort_papers(day_content)

            for _, v in day_content.items():
                if v is not None:
                    v = v.replace(u'\xa0', '')
                    f.write(v)
            f.write(f"\n")


def update_history_data(data):
    with open("history.json", "w+") as f:
        content = f.read()
        if not content: #or datetime.date.today().day == 1:
            history = {}
        else:
            history = json.loads(content)
    f.close()
    for k in data.keys():
        if k not in history:
            history[k] = data[k]
        else:
            history[k].update(data[k])

    json.dump(history, open("history.json", "w"))


if __name__ == "__main__":
    sleep_time = [30,35,40,45,50]
    for key in KEYS:
        get_paper_from_arxiv(key)
        try:
            get_paper_from_google(key)
            time.sleep(random.choice(sleep_time))
        except Exception as e:
            traceback.print_exc()
            print(e)
            print("google 禁止访问")
    json.dump(papers, open("papers.json", "w"))
    json_to_md(papers)
    shutil.copy("README.md", "docs/index.md")
    # 更新历史记录保存数据, 每月1号重置一次
    update_history_data(data)

