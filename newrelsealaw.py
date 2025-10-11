#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ==================== 匯入套件 ==================== #
from os import listdir
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta,timezone
import time
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
GMAIL_KEY = os.getenv('GMAIL_KEY')
MAIL_TO = os.getenv('MAIL_TO')
# recipient_email = os.getenv('MAIL_TO_LAW')
MAIL_TO_LAW = os.getenv('MAIL_TO_LAW')


# In[2]:


# 設定日期條件 
target_date = (datetime.now(timezone(timedelta(hours=8))) - timedelta(days=1)).date()

# In[3]:


# ==================== 工具函數 ==================== #
def parse_roc_date(roc_date_str, delimiter='.'):
    """ROC民國年轉換成西元日期"""
    roc_year, month, day = map(int, roc_date_str.split(delimiter))
    return datetime(roc_year + 1911, month, day).date()


# In[4]:


# ==================== Selenium Driver ==================== #
def setup_driver(headless=True):
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    if headless:
        options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


# In[5]:


# ==================== 爬蟲：金管會 ==================== #
def fetch_fsc(target_date):
    driver = setup_driver(headless=True)
    url = "https://law.fsc.gov.tw/index.aspx"
    driver.get(url)
    time.sleep(2)

    rows = driver.find_elements(By.CSS_SELECTOR, '#tbdy > tr')
    data = []
    for row in rows:
        try:
            date_text = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.strip()
            law_date = parse_roc_date(date_text)

            if law_date >= target_date:
                title_element = row.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a')
                title = title_element.text.strip()
                href = title_element.get_attribute('href')
                data.append({
                    "發布日期": law_date.strftime('%Y-%m-%d'),
                    "標題": title,
                    "連結": f'<a href="{href}">前往查看</a>'
                })
        except Exception as e:
            print(f"⚠️ FSC 資料解析錯誤：{e}")

    driver.quit()
    return pd.DataFrame(data)


# In[6]:


def fetch_mol(target_date):
    # ====================== 爬蟲主程式 ====================== 勞動部  #
    driver = setup_driver(headless=True)
    url = "https://laws.mol.gov.tw/index.aspx"
    driver.get(url)
    time.sleep(2)

    rows = driver.find_elements(By.CSS_SELECTOR, '#form1 > div.container > table > tbody >tr ')
    data = []
    print(f'rows = {rows}')
    def parse_roc_date(roc_date_str):
        roc_year, month, day = map(int, roc_date_str.split('.'))
        return datetime(roc_year + 1911, month, day).date()
    # #form1 > div.container > table > tbody
    for row in rows[1:]:
        try:
            date_text = row.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.strip()
            law_date = parse_roc_date(date_text)
            if law_date >= target_date:
                title_element = row.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a')
                title = title_element.text.strip()
                href = title_element.get_attribute('href')
                if not href.startswith("http"):
                    href = "https://law.fsc.gov.tw/" + href
                data.append({
                    "發布日期": law_date.strftime('%Y-%m-%d'),
                    "標題": title,
                    "連結": f'<a href="{href}">前往查看</a>'
                })
        except Exception as e:
            print(f"⚠️ 無法解析某列資料：{e}")
    driver.quit()
    return pd.DataFrame(data)


# In[7]:


# ====================== 爬蟲主程式 ====================== 中央銀行 #
def fetch_cbc(target_date):
    driver = setup_driver(headless=True)
    url = "https://www.law.cbc.gov.tw/"
    driver.get(url)
    time.sleep(2)

    # 設定日期條件
    # target_date = (datetime.now() - timedelta(days=1)).date()

    rows = driver.find_elements(By.CSS_SELECTOR, '#pageMainContent > div > div > div.col-10.page-main-col > div > div.news-list-table-div.list-table-div > table')
    data = []
    for row in rows:
        try:
            date_text = row.find_element(By.CSS_SELECTOR, 'td.news-list-row-date').text.strip()
            law_date = parse_roc_date(date_text)
            if law_date >= target_date:
                title_element = row.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a')
                title = title_element.text.strip()
                href = title_element.get_attribute('href')
                data.append({"發布日期": law_date.strftime('%Y-%m-%d'),
                    "標題": title,
                    "連結": f'<a href="{href}">前往查看</a>'})
        except Exception as e:
            print(f"⚠️ 無法解析cbc某列資料：{e}")
    driver.quit()
    # 轉成 DataFrame
    return  pd.DataFrame(data)


# In[8]:


# ====================== 爬蟲主程式 ====================== 銀行公會  #
def fetch_ba(target_date):
   driver = setup_driver(headless=True)
   url = "https://www.ba.org.tw/PublicInformation/PublicinfoAll"
   driver.get(url)
   time.sleep(2)

   rows = driver.find_elements(By.CSS_SELECTOR, '#maincontent > form > div > div.main_Content_txt > table > tbody >tr ')
   data = []
   def parse_roc_date(roc_date_str):
       roc_year, month, day = map(int, roc_date_str.split('/'))
       return datetime(roc_year , month, day).date()
   # #form1 > div.container > table > tbody
   for row in rows[1:]:
       try:
           date_text = row.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.strip()
           print(date_text)
           law_date = parse_roc_date(date_text)
           print(law_date)
           if law_date >= target_date:
               title_element = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a')
               title = title_element.text.strip()
               href = title_element.get_attribute('href')
               print(title,href)
               data.append({
                   "發布日期": law_date.strftime('%Y-%m-%d'),
                   "標題": title,
                   "連結": f'<a href="{href}">前往查看</a>'
               })
       except Exception as e:
           print(f"⚠️ 無法解析某列資料：{e}")
   driver.quit()
   return  pd.DataFrame(data)


# In[9]:


# ====================== 爬蟲主程式 ====================== 證券期貨相關  #
def fetch_selaw(target_date):
    driver = setup_driver(headless=True)
    url = "https://www.selaw.com.tw/Chinese/RegulatoryInformation"
    driver.get(url)
    time.sleep(2)
    rows1 = driver.find_elements(By.CSS_SELECTOR, '#regulatoryInformationDiv > table >tbody >tr')
    data = []
    # def parse_roc_date(roc_date_str):
    #     roc_year, month, day = map(int, roc_date_str.split('.'))
    #     return datetime(roc_year+1911 , month, day).date()
    for row in rows1[1:]:
        try:
            date_text = row.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.strip()
            law_date = parse_roc_date(date_text)
            if law_date >= target_date:
                title_element = row.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a')
                title = title_element.text.strip()
                href = title_element.get_attribute('href')
                data.append({
                    "發布日期": law_date.strftime('%Y-%m-%d'),
                    "標題": title,
                    "連結": f'<a href="{href}">前往查看</a>'
                })
        except Exception as e:
            print(f"⚠️ 無法解析某列資料：{e}")

    driver.quit()
    return  pd.DataFrame(data)


# In[10]:


# ==================== 郵件寄送 ==================== #
def send_fsa_news(df_list, recipient_email, subject, target_date,unit_list):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    if df_list:
        html_content = f"""
        <html>
        <body>
            <h3>{unit_list[0]}最新公告（{target_date} 後）</h3>
            {df_list[0].to_html(index=False, escape=False)}

            <h3>{unit_list[1]}最新公告（{target_date} 後）</h3>
            {df_list[1].to_html(index=False, escape=False)}

            <h3>{unit_list[2]}最新公告（{target_date} 後）</h3>
            {df_list[2].to_html(index=False, escape=False)}

            <h3>{unit_list[3]}最新公告（{target_date} 後）</h3>
            {df_list[3].to_html(index=False, escape=False)}

            <h3>{unit_list[4]}最新公告（{target_date} 後）</h3>
            {df_list[4].to_html(index=False, escape=False)}
        </body>
        </html>
        """
    else:
        html_content = f"""
        <html><body>
            <h3 style="text-align:center;color:#333;">本日 {target_date} 無新公告</h3>
        </body></html>
        """
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    try:
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.login(SENDER_EMAIL, GMAIL_KEY)
        smtp_server.send_message(msg)
        smtp_server.quit()
        print('📧 郵件發送成功！')
    except Exception as e:
        print(f'⚠️ 郵件發送失敗：{str(e)}')


# In[11]:


#寄送E-mail
if __name__ == "__main__":
# --- IGNORE ---
    # target_date = (datetime.now() - timedelta(days=1)).date()
    # print(f"📌 查詢發布日期 > {target_date} 的法規公告：")

    fsc_df = fetch_fsc(target_date)
    mol_df = fetch_mol(target_date)
    cbc_df = fetch_cbc(target_date)
    ba_df = fetch_ba(target_date)
    selaw_df = fetch_selaw(target_date)
    subject='金融相關政府機關法規修訂'
    df_list = [fsc_df, mol_df, cbc_df, ba_df, selaw_df]
    unit_list = ['金管會', '勞動部', '中央銀行', '銀行公會', '證券期貨相關']
    send_fsa_news(df_list, MAIL_TO_LAW, subject, target_date, unit_list)

