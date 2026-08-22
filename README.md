# 閃電霹靂車 周邊商品網頁

新世紀GPX Cyber Formula（サイバーフォーミュラ）周邊商品瀏覽介面。
商品資料為**實際抓取**，每筆可點擊前往來源頁。

🔗 **線上瀏覽：https://chuehnone.viovie.co/cyber-formula-goods/**

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

## 常用指令

```bash
./serve.sh          # 本機預覽
./update.sh         # 重抓商品資料（--quick 較快、--push 自動推送）
./verify.sh         # 檢驗線上版是否與本機一致（--watch 等到一致）
```

`update.sh` 跑完會列出與線上版的差異（新增／下架／價格／庫存異動），
預設不自動 commit。推送後 GitHub Pages 約 1–2 分鐘生效，
但 CDN 快取 10 分鐘，用 `./verify.sh --watch` 確認最可靠。

## 資料來源

| 來源 | 件數 | 提供 |
|---|---|---|
| [青島文化教材社（官方）](https://www.aoshima-bk.co.jp/special/product/cyberformula/) | 19 | 官方定價、發售月、系列編號、JAN、商品描述 |
| [ホビーサーチ hobbysearch](https://www.1999.co.jp/) | 387 | 商品廣度、實際售價、折扣、庫存狀態 |

合計 **391 件**，其中 15 件兩站都有（故上表兩數相加大於總數），可交叉比對價格。
抓取日期：2026-08-22。

價格與庫存為抓取當下狀態，非即時報價；實際交易請以來源網站為準。

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | 介面，無外部相依 |
| `products.json` | 商品資料（網頁讀這個） |
| `products.raw.json` | 翻譯前的原始資料備份 |
| `serve.sh` | 啟動本機預覽 server |
| `update.sh` | 一鍵重抓資料並更新 |
| `verify.sh` | 檢驗線上版是否與本機一致 |
| `scripts/` | 爬蟲、翻譯與 README 數字同步（見 `CLAUDE.md`） |
| `CLAUDE.md` | 開發規則與已知陷阱 |

## 翻譯

商品名稱、發售時期以**詞彙表逐詞替換**產生，角色與機體採台灣通行譯名
（阿斯拉、凰呀、風見隼人、布利德加賀等），未收錄的專有名詞保留日文原文。
官方商品描述為人工逐句翻譯。

新增欄位 `nameZh`、`descZh`、`releaseZh`、`seriesLineZh`；
原始日文欄位（`name`、`nameJa`、`desc`、`release`）皆保留未動。

> 要修改翻譯或重抓資料前，請先讀 [`CLAUDE.md`](CLAUDE.md)——
> 有幾個看似 bug 但其實是刻意設計的地方（例如 299 件商品的系列標為「未標示」）。

## 授權與聲明

本專案的**程式碼**（`index.html`、`scripts/`、`serve.sh` 等）以 MIT 授權釋出。

**商品資料與圖片不屬於本專案**：
- 商品資訊擷取自青島文化教材社官網與 hobbysearch，著作權歸各來源網站所有
- 商品圖片為熱連結（hotlink）至來源網站，未複製儲存於本 repo
- 作品《新世紀GPXサイバーフォーミュラ》相關權利屬 ©サンライズ 所有

本專案為個人非商業用途的資料整理與瀏覽介面，不從事銷售行為。
