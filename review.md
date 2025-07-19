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
