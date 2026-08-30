# CLAUDE.md

閃電霹靂車周邊商品瀏覽網頁。純靜態站，GitHub Pages 部署。
使用者導向說明在 `README.md`；本檔記錄**動手前必須知道、否則會做錯的事**。

## 專案結構

```
index.html          介面全部（無框架、無 build step，改完直接生效）
products.json       商品資料（翻譯後）← 網頁實際讀這個
products.raw.json   翻譯前備份 ← 重跑翻譯的來源，不要手改
scripts/            爬蟲與資料處理
update.sh           一鍵重抓 → 整併 → 翻譯 → 顯示差異
verify.sh           檢驗線上版是否與本機一致
```

資料流：`scrape_*.py` → `build.py` → `translate.py` → `products.json`

## 絕對不要做的事

### 1. 不要編造商品資料

只收錄實際抓到的。缺欄位就留空，**不要用既有知識補寫**。
使用者明確要求過這點，且驗證成本極高（日文商品名很難事後查核）。

### 2. 不要從機體名反推作品系列

多數商品的 `series` 是 `unknown`，這是**刻意的**，不是待辦事項。
多數商品名不寫系列別（「アスラーダG.S.X」不註明是 TV 版），
而同一機體會跨作品登場（νアスラーダ 在 SIN 與 SAGA 都有），反推必然出錯。
只在標題有明確作品標記時才標系列。

### 3. 不要用詞彙表翻譯整句

`translate.py` 的 `translate()` 是**逐詞替換**，只適合名詞短語（商品名）。
用在完整日文句子上會產出中日夾雜的破碎句：

> ✗ 阿斯拉が唄い、リタが立ち上がる！感動のペルー戦拉力形態登場！

商品描述一律人工逐句翻譯，寫進 `scripts/desc_zh.json`，key 用 JAN 碼。
新增描述時照做，不要圖快走 `translate()`。

### 4. 不要繞過 Cloudflare

hobbysearch（1999.co.jp）的**商品詳情頁**有 Cloudflare challenge。
列表頁沒擋，資料都從列表頁取得。不要嘗試繞過驗證。
這也是為什麼只有青島官方的商品有描述。

### 5. 不要把圖片下載進 repo

商品圖是熱連結到來源網站，未複製儲存——這是版權考量下的刻意選擇，
使用者確認過。已實測兩站在跨網域 referer 下都正常回圖。

## 容易踩的坑

### git：email privacy 會擋 push

使用者的 GitHub 帳號禁止公開真實 email。commit 必須用 noreply 位址：

```bash
git -c user.name="chuehnone" \
    -c user.email="1897025+chuehnone@users.noreply.github.com" commit ...
```

用帳號的真實 email 會被 remote rejected（Cloudflare 的 beacon token 之類的
公開識別碼可以留在 repo，但真實 email 不要寫進公開文件）。

### 部署網址不是 github.io

帳號層級設了自訂網域，實際網址是
**https://chuehnone.viovie.co/cyber-formula-goods/**
（github.io 會導向這裡）。寫連結時用自訂網域。

### CDN 快取 10 分鐘

Pages 回 `cache-control: max-age=600`。推送後立刻看到舊版**不是部署失敗**。
用 `./verify.sh --watch` 等，或比對雜湊確認，不要憑肉眼下結論。

### 改 products.json 前先確認來源

要重跑翻譯時，從 `products.raw.json` 復原再跑，不要在已翻譯的檔案上再跑一次
（詞彙表會重複替換，造成累積誤差）。`update.sh` 已處理好這個順序。

### 文件裡不要寫死件數

`README.md` 與本檔**刻意不寫商品件數、分類數、抓取日期**——資料會變，
寫死就會過期，而過期的文件比沒有文件更誤導。

需要數字時用：

```bash
python3 scripts/stats.py
```

網頁使用者看頁尾即可（頁尾的件數與日期由 `products.json` 動態產生）。

統計兩站件數時用「來源含該站」定義（故兩數相加會大於總數，因有商品兩站都收錄）。
不要改成互斥計數，那會讓「可交叉比對」的說法失去依據。

### 外部連結帶 UTM 參數

所有導向來源網站的連結都經過 `index.html` 的 `withUtm()` 加上
`utm_source=cyber-formula-goods` 等三個參數，讓來源網站知道流量從這裡來。

在**顯示層**處理，不寫進 `products.json`——資料檔會被重抓覆蓋，
且原始資料應保持乾淨。新增外連時記得包 `withUtm()`，
可用這段檢查有無遺漏：

```js
[...document.querySelectorAll('a[target="_blank"]')]
  .filter(a => !a.href.startsWith(location.origin))
  .filter(a => !new URL(a.href).searchParams.has('utm_source')).length  // 應為 0
```

已實測兩站帶 UTM 後回應正常（青島回應大小完全相同，hobbysearch 商品頁正常顯示）。

外連的 `rel` 是 `noopener`（安全防護，必須保留）**但不含 `noreferrer`**——
加了 `noreferrer` 瀏覽器就不送 Referer 標頭，來源網站會把流量歸為直接流量，
只看到 `utm_source` 字串而不知道網站在哪，UTM 就失去意義。
另明示 `referrerpolicy="strict-origin-when-cross-origin"`：跨網域只送 origin
（`https://chuehnone.viovie.co/`），不洩漏使用者正在看哪個商品頁。

實測方式：本機起一個回顯 Referer 的 server，從頁面發請求比較兩種 policy。
`no-referrer` 收到「未送出」，`strict-origin-when-cross-origin` 收到來源網址。

### 網站分析：Cloudflare Web Analytics

`index.html` 末端有一段載入 beacon 的 script。**token 需手動填入**
（`const TOKEN = ''`），未填或在本機（localhost / 127.0.0.1 / file://）時
自動不載入，避免開發流量污染統計。

選它的理由：不使用 cookie、不追蹤個人，因此**不需要 cookie 同意橫幅**。

**已查證的限制**：Cloudflare Web Analytics 不支援自訂事件（截至 2026），
只記 pageview。所以看不到「哪些商品被點最多」。
那需要 Cloudflare Zaraz，但本站直連 GitHub Pages（`server: GitHub.com`，
無 `cf-ray` 標頭），沒有經過 Cloudflare，故用不了。
若日後真的需要事件追蹤，改用 Umami 或 GA4，不要試圖用 Zaraz。

### 變動紀錄（changelog）

`scripts/changelog.py` 比對新資料與 git HEAD（即線上版），把差異寫進
`products.json` 的 `meta.changes`，並在有變動的商品上加 `changeType` 欄位。
網頁讀同一個檔案渲染「最近變動」區塊與卡片徽章，不需額外請求。

**只記「這次 vs 上次」**，不累積歷史——過去的變動看 `git log` 即可。
無變動時會清掉 `meta.changes` 與所有 `changeType`，網頁自動隱藏該區塊。

`update.sh` 已串接，不需手動執行。注意它依賴 git HEAD 當基準：
**若在同一次更新中重複執行，第二次會比對到已 commit 的新資料而顯示無變動**。

庫存變動的標記優先度高於價格（`tag_products()`）——商品快沒了比便宜了更需要知道。

### 搜尋會忽略分隔符

`index.html` 的 `compact()` 把 `. 空格 - _ / · ・ ‧` 去掉後再比對一次，
所以「CFC」搜得到「C.F.C.」、「AKF11」搜得到「AKF-11」。
原字串比對仍優先，這只是額外的 fallback。

改搜尋邏輯時記得兩種比對都要保留——商品名裡大量使用帶點的縮寫
（C.F.C.、G.S.X、D.D.T）與帶連字號的型號（AKF-11、SF-03、00-X3）。

### 分類判定依賴標題括號

`build.py` 的 `detect_kind()` 讀商品名結尾的 `(プラモデル)` 這類標記。
已知會壞的形態：
- `(完成品)★宮沢模型限定版` — 括號後有尾綴（已修，容許 `★` 尾綴）
- `(リフティングターンモード)` — 括號內是形態名不是類別（靠站方分類參數補救）

改這個函式時，一併確認 `strip_kind()` 不會把限定版等資訊一起刪掉。

## 常見任務

### 重抓商品資料

```bash
./update.sh              # 完整，約 9 分鐘
./update.sh --quick      # 跳過分類版爬蟲，約 1 分鐘，結果相同
./update.sh --push       # 完成後自動 commit + push
```

流程：抓兩來源 → `build.py` 整併 → `translate.py` 翻譯 → 更新抓取日期 →
列出與線上版的差異。中間產物在 `scripts/.cache/`（已 gitignore）。
預設不自動 commit，先看差異再決定。

`--quick` 少跑 `scrape2.py`（站方分類版），目前分類判定已能從商品名補上，
兩者結果一致。要納入新商品類型時跑完整版比較保險。

### 加入新的翻譯詞彙

`translate.py` 跑完會列出「殘留假名詞」。把它們補進 `scripts/translate.py`
的 `EXTRA` 詞彙表，再跑 `./update.sh --quick`。

詞彙表按長字串優先排序（`VOCAB_SORTED`），避免短詞先替換破壞長詞。
新增商品**描述**時見上面第 3 點，不要走詞彙表。

## 驗證要求

改完一定要實測，不要只看程式碼就宣稱完成：

```bash
./serve.sh            # 本機起 server（file:// 會被 CORS 擋掉 products.json）
./verify.sh           # 推送後確認線上版與本機一致
```

**截圖判讀注意**：商品圖是白底商品照，在縮圖尺寸的截圖下常看起來像沒載入。
判斷圖片是否正常要用 `naturalWidth`（>0 即載入成功），或放大截圖確認，
不要憑縮圖就斷定圖片壞掉——這個誤判在本專案發生過三次。

## 資料來源

| 來源 | 提供 |
|---|---|
| [青島官方](https://www.aoshima-bk.co.jp/special/product/cyberformula/) | 定價、發售月、系列編號、JAN、官方描述（權威） |
| [hobbysearch](https://www.1999.co.jp/) | 廣度、實際售價、折扣、庫存 |

兩站都有的商品：以官方欄位為準，售價與庫存取 hobbysearch。
實際件數用 `python3 scripts/stats.py` 可查。
兩站 robots.txt 皆允許一般 UA；爬蟲內建 1.5–2 秒延遲，不要拿掉。

## 已驗證過的非問題

以下幾點看起來可疑，但查證後確認正常，不要「順手修掉」：

- **菅生あすか 相關商品**：她是本作角色（菅生明日香），不是雜訊
- **CM-xx 系列塗料**：Creos 的本作專用色，是周邊商品不是雜訊
- **シュピーゲル HP-022**：在青島官方閃電霹靂車專頁內，確為本作
- **SIN 系列完成品**：Variable Action 系列，標題明載作品名
