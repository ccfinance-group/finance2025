from collections.abc import Sequence
from datetime import datetime, timedelta, date
import os
from time import sleep
from itertools import starmap, chain
import urllib3.util

from openai import OpenAI
from openai.types.shared import ChatModel
import pandas as pd
from selenium import webdriver

def init_driver(arguments: list[str] = None):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation']) #隱藏chrome 正受到

    options.add_argument('--headless')               # 加上這行
    options.add_argument('--disable-gpu')            # 加上這行
    options.add_argument('--window-size=1920,1080')  # 加上這行

    for arg in (arguments or []):
        options.add_argument(arg)

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver
    

def init_openai_client(**kwargs):
    params = dict(
        api_key=kwargs.pop('api_key', os.getenv('OPENAI_API_KEY')),
        organization=kwargs.pop('organization', os.getenv("OPENAI_ORGANIZATION")),
        project=kwargs.pop('project_id', os.getenv('OPENAI_PROJECT')),
        **kwargs,
    )
    return OpenAI(**params)


def summarize_text(
    text: str,
    *,
    client: OpenAI = None,
    model: ChatModel = "gpt-4o",
    silent: bool = False,
):
    client = client or init_openai_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一個專業的文章摘要助手，請提取文章的重點。"},
                {"role": "user", "content": f"請幫我摘要以下文章的重點, 200字以內：{text}"}
            ],
            temperature=0.5,
            max_tokens=150
        )
        return response.choices[0].message.content.strip().replace('\n', ' ')
    except Exception as e:
        print(e)

        if silent:
            return None

        raise e


def crawl_main_site(
    driver: webdriver.Chrome,
    start_day: datetime,
):
    driver.get('https://www.fsc.gov.tw/ch/home.jsp?id=131&parentpath=0,2')
    driver.implicitly_wait(5)

    def _parse_element(item_idx: int):
        try:
            date_text = driver.find_element('css selector', f'#messageform > div.newslist > ul > li:nth-child({item_idx}) > span.date').text

            # First check whether date >= start_day
            if not datetime.strptime(date_text, "%Y-%m-%d").date() >= start_day:
                return None
            
            unit_text = driver.find_element('css selector', f'#messageform > div.newslist > ul > li:nth-child({item_idx}) > span.unit').text
            link = driver.find_element('css selector', f'#messageform > div.newslist > ul > li:nth-child({item_idx}) > span.title > a')
            title_text = link.get_attribute('title')
            href = link.get_attribute('href')

            link.click()
            title = driver.find_element('css selector', '#ap > div.maincontent > div.subject > h3').text
            content = driver.find_element('css selector', '#ap > div.maincontent > div.page-edit ').text

            driver.back()
            sleep(1)

            return {
                'publish_date': date_text,
                'source': unit_text,
                'title': f'<a href="{href}" target="_blank">{title_text}</a>',
                'content': content,
            }

        except Exception as e:
            print(e)
            return None
        
    results = map(
        lambda item_idx: _parse_element(item_idx),
        range(2, 17),
    )

    # filter out None result
    results = filter(None, results)

    # add serial number for result
    results = starmap(
        lambda idx, result: {
            'serial_number': idx,
            **result,
        },
        enumerate(results, start=1),
    )

    return list(results)


def crawl_sub_site(
    driver: webdriver.Chrome,
    url: str,
    bureau: str,
    start_day: datetime,
    keywords: Sequence[str] = None,
):
    keywords = keywords or ('銀行股份有限公司', '證券', '期貨', '投信', '保險', '金融控股', '金控', '銀行', '投顧')
    
    driver.get(url)
    driver.implicitly_wait(5)

    def _parse_item(item_idx: int):
        date_text = driver.find_element('css selector', f'#messageform > div:nth-child(7) > div:nth-child({item_idx}) > div.pdate1').text
        title_element = driver.find_element('css selector', f'#messageform > div:nth-child(7) > div:nth-child({item_idx}) > div.ptitle1 > a')
        title_text = title_element.text

        if not all((
            datetime.strptime(date_text, "%Y-%m-%d").date() >= start_day,
            any(keyword in title_text for keyword in keywords),
        )):
            return None

        href = title_element.get_attribute('href')

        title_element.click()
        title = driver.find_element('css selector', '#maincontent > div:nth-child(1) > h3').text
        content = driver.find_element('css selector', '#maincontent > div.page_content > div:nth-child(2)').text
        driver.back()

        return dict(
            source=bureau,
            published_date=date_text,
            title=f'<a href="{href}" target="_blank">{title_text}</a>',
            content=content,
        )

    results = map(
        lambda idx: _parse_item(idx),
        range(5, 33, 2),
    )

    # filter out None
    results = filter(
        None,
        results,
    )

    return list(results)


def send_email(
    title: str,
    df: pd.DataFrame,
    *,
    mail_key: str = None,
    send_from: str = None,
    send_to: str = None,
):
    if df.empty:
        print(f"📭 無{title}，已略過寄信")
        return
    
    send_from = send_from or os.getenv('MAIL_SEND_FROM')
    send_to = send_to or os.getenv('MAIL_SEND_TO')
    mail_key = mail_key or os.getenv('MAIL_KEY')

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib

    def _prepare_msg():
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = send_from
        msg['To'] = send_to
        df['content'] = df['content'].str.replace('\n', '<br>')

        html = f"""
            <html>
            <head>
                <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0; }}
            
                th {{
                    background-color: #1a237e;
                    color: white;
                    text-align: center;
                    padding: 12px;
                    border: 1px solid #ddd;}}
                
                td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                    vertical-align: top;
                    white-space: pre-line;}}
                
                tr:nth-child(even) {{
                    background-color: #f2f2f2; }}
            
                h3 {{text-align: center;
                    color: #333;
                    margin: 20px 0;}}
                    
                
                </style>
            </head>
            <body>
                <h3>{title}</h3>
                {df.to_html(index=False, escape=False)}
            </body>
            </html>"""

        msg.attach(MIMEText(html, 'html', 'utf-8'))
        return msg
    
    try:
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.login(send_from, mail_key)
        smtp_server.send_message(_prepare_msg())
        smtp_server.quit()
        print(f'✅ 郵件發送成功：{title}')
    except Exception as e:
        print(f'❌ 郵件發送失敗：{e}')


def main():
    driver = init_driver()
    ai_client = init_openai_client(
        api_key=os.getenv('OPENAI_API_KEY'),
        organization=os.getenv("OPENAI_ORGANIZATION"),
        project=os.getenv('OPENAI_PROJECT'),
    )
    start_day = date.today() - timedelta(days=1)

    # handle main_site crawling
    main_results = crawl_main_site(
        driver,
        start_day=start_day,
    )
    main_results = map(
        lambda result: {
            'summary': summarize_text(
                result['content'],
                client=ai_client,
                silent=True,
            ) or '❌ 摘要失敗',
            **result,
        },
        main_results,
    )

    # handle sub_site crawling
    sub_results = chain(
        crawl_sub_site(
            driver,
            url='https://www.sfb.gov.tw/ch/home.jsp?id=104&parentpath=0,2,102',
            bureau='證期局',
            start_day=start_day,
        ),
        crawl_sub_site(
            driver,
            url='https://www.banking.gov.tw/ch/home.jsp?id=550&parentpath=0,524,547',
            bureau='銀行局',
            start_day=start_day,
        ),
        crawl_sub_site(
            driver,
            url='https://www.ib.gov.tw/ch/home.jsp?id=264&parentpath=0,2,262',
            bureau='保險局',
            start_day=start_day,
        ),
    )
    sub_results = starmap(
        lambda idx, result: {
            'serial_number': idx,
            'summary': summarize_text(
                result['content'],
                client=ai_client,
                silent=True,
            ) or '❌ 摘要失敗',
            **result,
        },
        enumerate(sub_results, start=1),
    )
    driver.quit()

    send_email(
        title='金管會重大裁罰',
        df=pd.DataFrame(main_results),
    )
    send_email(
        title='金管會非重大裁罰',
        df=pd.DataFrame(sub_results),
    )
    return
