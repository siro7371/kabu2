import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="みんかぶ銘柄チェッカー", layout="wide")

class MinkabuScraper:
    def __init__(self, code):
        self.code = code
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        self.base_url = f"https://minkabu.jp/stock/{code}"
        self.yutai_url = f"https://minkabu.jp/stock/{code}/yutai"

    def get_soup(self, url):
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.encoding = "utf-8"
            return BeautifulSoup(res.text, "html.parser")
        except:
            return None

    def scrape_data(self):
        soup = self.get_soup(self.base_url)
        if not soup or "指定されたページは見つかりませんでした" in soup.text:
            return None

        # 銘柄名
        name_tag = soup.find("p", class_="md_stockBoard_stockName")
        name = name_tag.text.strip() if name_tag else "不明"

        # 株価
        price_tag = soup.find("div", class_="stock_price")
        price = price_tag.text.strip() if price_tag else "取得不可"

        # 利回り・配当（テーブルからテキスト検索）
        dividend_yield = "－"
        dividend_value = "－"
        tables = soup.find_all("table", class_="md_table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                if "配当利回り" in row.text:
                    dividend_yield = row.find("td").text.strip()
                if "1株配当" in row.text:
                    dividend_value = row.find("td").text.strip()

        # 優待情報
        yutai_soup = self.get_soup(self.yutai_url)
        yutai_content = "なし"
        yutai_month = "－"
        
        if yutai_soup:
            y_month = yutai_soup.find("div", class_="ly_content_main")
            if y_month:
                # 簡易的に最初のテーブルの内容を取得
                y_table = yutai_soup.find("table", class_="md_table")
                if y_table:
                    yutai_content = y_table.get_text(separator=" ").strip()[:100] + "..."

        return {
            "銘柄コード": self.code,
            "銘柄名": name,
            "株価": price,
            "配当利回り": dividend_yield,
            "1株配当": dividend_value,
            "優待内容": yutai_content
        }

# UI部分
st.title("📈 みんかぶ情報チェッカー")
code_input = st.sidebar.text_input("銘柄コードを入力")

if code_input:
    scraper = MinkabuScraper(code_input)
    data = scraper.scrape_data()
    if data:
        st.dataframe(pd.DataFrame([data]).T, use_container_width=True)
        st.link_button("みんかぶで詳細を見る", f"https://minkabu.jp/stock/{code_input}")
    else:
        st.error("データが見つかりませんでした。")

st.caption("【免責事項】本ツールは学習用であり、取得データの正確性を保証しません。みんかぶの利用規約を遵守してください。")
