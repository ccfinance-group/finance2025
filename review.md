# Code Review Note

## About dependencies management

- requirements.txt 不完整，應包含主要 package 與各 dependencies 的版本資訊

- `pip freeze > requirements.total.txt`

- 更完整的 dependencies management: 可使用 [poetry](https://python-poetry.org/)

## Markdown Issue

- `README` 應該是對 Repo 功能的簡要說明與使用方式範例，而不是照抄程式碼上去
  (eg. 完全沒有提及如何執行這份程式？)

- 段落跟段落之間應留白

- code block 對 language 標示的格式有誤：(`python=` -> `python` 或 `py`, [ref](https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml))

  ```python=
  import os
  import pandas as pd
  from selenium import webdriver
  ```

  改為

  ```python
  import os
  import pandas as pd
  from selenium import webdriver
  ```

## Variable Management

- 如果有環境變數 (env)，應提供 `.env.example` / `.env.tpl`，以供使用者參考
- 環境變數習慣上採全大寫
- OpenAI client 可以仿照 selenium driver 的邏輯，寫成一個 factory function
- `start_day` 應該改為一個可傳入的變數，不適合放在 global variable

## summarize_text

- 讓 openAI client, model 作為可傳入的參數，增加彈性
- model string typing: 引用官方提供的 ChatModel Literal 作為參考
- `silent` flag: 提供一個開關，讓使用者決定要不要處裡 exception -> 增加 function 使用的彈性

## crawl_main_site

- `if date_obj >= startday:` 可以用反向的 condition 進行 early return (continue)

```py
for item in range(2, 17):
    try:
        # ...code
        if date_obj >= startday:
            link.click()
            title = driver.find_element('css selector', '#ap > div.maincontent > div.subject > h3').text
            content = driver.find_element('css selector', '#ap > div.maincontent > div.page-edit ').text
            driver.back()
            sleep(1)
            # ... and a lot of code

# 改成
for item in range(2, 17):
    try:
        # ...code
        if not date_obj >= startday:
            continue
        
        # 減少一層 indent
        link.click()
        title = driver.find_element('css selector', '#ap > div.maincontent > div.subject > h3').text
        content = driver.find_element('css selector', '#ap > div.maincontent > div.page-edit ').text
        driver.back()
        sleep(1)
        # ... and a lot of code
```

- 改用 map 把整個 for 迴圈包起來，並以 `_parse_element` 這個 function 來專門處理 for 迴圈內的操作
- 應用 `filter` / `map` / `starmap` 整理資料
- 不應該對 `summarize_text` 做 try-catch，已經在 summarize_text 裡做好了
- 把 summarize_text 的部分移除， craw_main_site function 職責單一，只進行爬蟲。summarize 的部分留給 main function
- 回傳的 data type 盡量越簡單的越好 （eg. 回傳原生的 dictionary instead of pd Frame）

## crawl_sub_site

- 因爬蟲操作類似，應該把這個 function 變成一次只爬一個對象網站
- `any` 使用的不錯，GJ!
- 三個不同 url 的 result list 用 `iterable.chain` 整理成一個 structure
- 對於 "不會變動的 list 資料" (eg. `keywords`)，使用 tuple 取代 list，使用的 memory 較少，增加空間效能
- `keywords` 也可以考慮使用 `frozenset`，加快搜尋效能

## send_mail

- 有時候整理一些比較複雜的資料 (eg. `MIMEMultipart`)，可以考慮把他再抽成一個小 inner function，維持 SRP 精神 + 減少太多零碎操作散佈在主要 function
