# 閃電霹靂車 周邊商品網頁

新世紀GPX Cyber Formula（サイバーフォーミュラ）周邊商品瀏覽介面。
商品資料為**實際抓取**，每筆可點擊前往來源頁。

🔗 **線上瀏覽：https://chuehnone.viovie.co/cyber-formula-goods/**
（亦可由 https://chuehnone.github.io/cyber-formula-goods/ 進入，會導向上方自訂網域）

- 391 件商品，含官方模型、Figure、服飾、壓克力周邊、塗料等 18 個分類
- 中文為主標、日文原名為副標，兩者皆可搜尋
- 可依分類／機體／系列篩選，支援價格與折扣排序
- 每件商品可點擊前往青島官網或 hobbysearch 原始商品頁

## 開啟

```bash
./serve.sh          # 預設 8080；./serve.sh 3000 可指定 port
```

- 電腦：http://localhost:8080
- 手機：執行 `./serve.sh` 後會列出可用的內網／Tailscale 網址

不能直接雙擊 `index.html`——`file://` 會被 CORS 擋下 `products.json`。

## 資料來源

| 來源 | 件數 | 提供 |
|---|---|---|
| [青島文化教材社（官方）](https://www.aoshima-bk.co.jp/special/product/cyberformula/) | 19 | 官方定價、發售月、系列編號、JAN、官方商品描述 |
| [ホビーサーチ hobbysearch](https://www.1999.co.jp/) | 372 | 商品廣度、實際售價、折扣、庫存狀態 |

合計 **391 件**，其中 24 件同時有兩個來源（可交叉比對價格）。
抓取日期：2026-08-22。

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | 介面，無外部相依 |
| `products.json` | 商品資料（364KB） |
| `serve.sh` | 啟動本機 server |
| `scripts/scrape_ao.py` | 抓青島官網 |
| `scripts/scrape_hs.py` | 抓 hobbysearch（關鍵字全站） |
| `scripts/scrape2.py` | 抓 hobbysearch（帶站方分類） |
| `scripts/build.py` | 整併兩來源 → products.json |
| `scripts/translate.py` | 補上繁體中文翻譯欄位 |
| `scripts/desc_zh.json` | 官方商品描述的中文譯稿（人工逐句翻譯） |
| `products.raw.json` | 翻譯前的原始資料備份 |

## 重新抓取

```bash
cd scripts
python3 scrape_ao.py     # 青島官網，約 40 秒
python3 scrape_hs.py     # hobbysearch 全站，約 20 秒
python3 scrape2.py       # hobbysearch 分類版，約 8 分鐘
python3 build.py         # 整併，輸出 products.json
cp products.json ../products.raw.json
python3 translate.py ../products.json   # 補上中文欄位
```

爬蟲皆內建 1.5–2 秒延遲。兩站 robots.txt 均允許一般 UA 抓取。

## 資料處理原則

- **只收錄實際抓到的商品**，不以既有知識補寫未驗證項目。
- 分類依「商品標題結尾括號標記」與「站方分類參數」判定，非猜測。
- 系列（TV／11／ZERO／SAGA／SIN）只在標題有明確作品標記時標註；
  299 件標題未載明系列者維持「未標示」，不從機體反推——同一機體可能跨作品登場，反推會出錯。
- 青島官方資料視為權威，與 hobbysearch 重複時以官方欄位為準，售價與庫存則取 hobbysearch。

## 已知限制

- hobbysearch **商品詳情頁有 Cloudflare challenge**，未繞過；商品描述僅官方 19 件有。
- 價格與庫存是抓取當下狀態，非即時；點來源連結可查最新。
- 商品圖片為來源網站熱連結，版權屬各來源網站及 ©サンライズ。

## 翻譯

商品名稱、發售時期、系列行以**詞彙表逐詞替換**產生（`scripts/translate.py`），
角色與機體採台灣通行譯名（阿斯拉、凰呀、風見隼人、布利德加賀等），
未收錄的專有名詞保留日文原文。介面以中文為主標、日文原名為副標，兩者都可搜尋。

青島官方那 18 筆商品描述是**完整日文段落**，詞彙表替換會產出中日夾雜的破碎句，
因此改為人工逐句翻譯，存於 `scripts/desc_zh.json`（key 為 JAN 碼）。

新增的翻譯欄位：`nameZh`、`descZh`、`releaseZh`、`seriesLineZh`。
原始日文欄位（`name`、`nameJa`、`desc`、`release`）皆保留未動。

### 翻譯的限制

詞彙表方法適合名詞短語，不適合整句。若日後要翻譯更多長句描述，
應比照 `desc_zh.json` 的做法人工翻譯，不要依賴 `translate()`。

## 授權與聲明

本專案的**程式碼**（`index.html`、`scripts/`、`serve.sh`）以 MIT 授權釋出。

**商品資料與圖片不屬於本專案**：
- 商品資訊擷取自青島文化教材社官網與 hobbysearch，著作權歸各來源網站所有
- 商品圖片為熱連結（hotlink）至來源網站，未複製儲存於本 repo
- 作品《新世紀GPXサイバーフォーミュラ》相關權利屬 ©サンライズ 所有

本專案為個人非商業用途的資料整理與瀏覽介面，不從事銷售行為。
價格與庫存為抓取當下狀態，實際交易請以來源網站為準。
