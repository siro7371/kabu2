import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# ページ設定
st.set_page_config(page_title="株探銘柄チェッカー", layout="wide")

class KabutanScraper:
    def __init__(self, code):
        self.code = code
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.base_url = f"https://kabutan.jp/stock/?code={code}"
        self.yutai_url = f"https://kabutan.jp/stock/yutai/?code={code}"

    def get_soup(self, url):
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            res.raise_for_status()
            # 株探は基本的にUTF-8ですが、念のためレスポンスから推測
            res.encoding = res.apparent_encoding
            return BeautifulSoup(res.text, "html.parser")
        except Exception as e:
            return None

    def scrape_data(self):
        soup = self.get_soup(self.base_url)
        if not soup or "該当する銘柄が見つかりませんでした" in soup.text:
            return None

        # 銘柄名
        name = soup.find("div", class_="company_block").find("h3").text.replace(str(self.code), "").strip()
        
        # 現在の株価
        price_tag = soup.find("span", class_="kabuka")
        price = price_tag.text.strip() if price_tag else "取得不可"

        # 配当利回り・1株配当
        dividend_yield = "－"
        dividend_value = "－"
        
        # 基本情報テーブルから抽出
        kabuka_table = soup.find("div", id="stockinfo_i3")
        if kabuka_table:
            cells = kabuka_table.find_all("dd")
            if len(cells) >= 5:
                dividend_yield = cells[4].text.strip() # 利回り
                dividend_value = cells[3].text.strip() # 1株配当

        # 優待情報の取得
        yutai_soup = self.get_soup(self.yutai_url)
        yutai_content = "なし / 取得不可"
        yutai_month = "－"
        unit_shares = "100株" # デフォルト

        if yutai_soup:
            yutai_table = yutai_soup.find("table", class_="stock_table03")
            if yutai_table:
                # 権利確定月
                month_tag = yutai_soup.select_one(".yutai_get_month")
                if month_tag:
                    yutai_month = month_tag.text.strip()
                
                # 優待内容 (最初の項目を抽出)
                content_tag = yutai_table.find("dd")
                if content_tag:
                    yutai_content = content_tag.get_text(separator=" ").strip()

        return {
            "銘柄コード": self.code,
            "銘柄名": name,
            "株価 (円)": price,
            "配当利回り (%)": dividend_yield,
            "1株配当 (円)": dividend_value,
            "権利確定月": yutai_month,
            "単元株数": unit_shares,
            "優待内容": yutai_content
        }

# --- UI Setup ---
st.title("📊 株探 銘柄情報ダッシュボード")
st.sidebar.header("検索条件入力")

code_input = st.sidebar.text_input("銘柄コードを入力 (例: 7203, 9101)", placeholder="7203")

if code_input:
    with st.spinner(f"銘柄コード {code_input} のデータを取得中..."):
        scraper = KabutanScraper(code_input)
        data = scraper.scrape_data()

        if data:
            st.subheader(f"🔍 {data['銘柄名']} ({data['銘柄コード']}) の分析結果")
            
            # DataFrameに変換
            df = pd.DataFrame([data]).set_index("銘柄コード")
            
            # 表表示
            st.dataframe(df.T, use_container_width=True)

            # 外部リンクボタン
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("株探で詳細を見る (基本情報)", f"https://kabutan.jp/stock/?code={code_input}")
            with col2:
                st.link_button("株探で優待情報を見る", f"https://kabutan.jp/stock/yutai/?code={code_input}")
        else:
            st.error("銘柄情報が見つかりませんでした。コードが正しいか確認してください。")
else:
    st.info("左側のサイドバーに4桁の銘柄コードを入力してください。")

# --- Footer ---
st.markdown("---")
st.caption("【免責事項】")
st.caption("本アプリケーションで表示される情報は、株探 (kabutan.jp) のデータを参照していますが、その正確性や完全性を保証するものではありません。投資に関する最終決定は、利用者ご自身の判断において行ってください。本ツール利用によるいかなる損失も責任を負いかねます。")
