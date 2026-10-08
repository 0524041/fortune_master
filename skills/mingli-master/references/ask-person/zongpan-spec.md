# 總盤結構說明書（zongpan-spec）

> 用途：排盤程式（問人總盤程式）輸出**怎麼讀**——每一行代表什麼、要解什麼、對應哪份知識。
> 輸出格式＝分層：必讀摘要（Layer 0）＋按需細節（Layer 1 子命令）。全走 txt/md，不用 JSON。
> 解盤主軸仍是 `pan-reading.md` 八步；本檔只負責「總盤資訊 ↔ 知識檔案」對照。

## 一、Layer 0 必讀摘要：逐行解義

第一行 `# 問人總盤摘要 <國曆生辰> <城市> <性別> <曆制> 真太陽<時>`：
- **基本輸入**，用來核對盤面來源與曆制。無此行的輸出不可用（可能是快取錯人）。

八字行 `八字：<四柱>｜日主<X>｜身強<N>分<等級>｜喜<X>忌<Y>｜調候<Z>｜格局｜合沖｜神煞`：
- 四柱＋日主＝定調第一步；身強分數／喜忌＝用神初判；調候＝寒暖修正。
- 對應知識：`bazi.md`（讀法）＋`shenqiang.md`（三得）＋`tiaohou.md`（調候）＋`shishen_combo.md`（十神組合）。

大運行 `大運<順逆><N>歲起：<運1> → <運2> → ...`：
- 十年氣候線。當前運與下一步運決定「這五年」節奏；八字一律以立春為界。
- 對應知識：`suiyun.md`（體用與應期）＋`pan-reading.md` §七。

紫微行 `紫微：命<支><主星>｜身<支><主星>｜<局>｜生年四化落宮`：
- 命身定氣質，生年祿權科忌定一生課題（忌最重，落哪宮哪領域先修）。
- 對應知識：`ziwei.md`（讀法）＋`star_detail.md`（單星）＋`fusha.md`（輔煞夾宮）。

財官象行 `財官象：財帛<星>｜官祿<星>｜遷移<星>`：
- 三個最常問的宮位速覽；只給主星與重點，要看全宮用 `ziwei show --palaces`。
- 對應知識：`caiyun.md`（財）＋`pan-reading.md` §六（領域答什麼）。

大限行 `大限<age> <宮><干支><星>｜限四化<祿權科忌>｜<當年>流年<宮><干支>忌<星>`：
- 紫微十年大限＋當年流年落宮與流忌；與八字大運同年疊到＝加權。
- 對應知識：`ziwei.md` §運限＋`pan-reading.md` §七。

財語義行 `財語義：<verdict>（<reasons>）`：
- 排盤程式的財運語義初判（同向／分歧／單邊／缺料）；LLM 只覆核不重算。
- 對應知識：`caiyun.md` §三（裁決規則）＋§四（轉譯動作）。

六壬行 `六壬：<課體>｜初<支><六親>中<支><六親>末<支><六親>｜本命<干支>行年<干支>`：
- 一生動態人事：初傳早年、中傳中年、末傳晚年；行年＝逐年之應。
- 對應知識：`aux-charts.md` §二＋`liuren.md` 第十節（終身課）。

奇門行 `奇門<局>：命<N>宮<方><門><星><神>｜<age>行<N>宮...｜<某方><門><神>忌`：
- 方位行動指南：命宮＝一生基本樣貌；大限宮隨年齡移動；忌方避開。
- 對應知識：`aux-charts.md` §三＋`qimen.md` §四九宮象意。

警示行 `警示：<warnings>`：
- 校驗警示（如近節氣交界）。有值＝全盤標低置信，說明原因，不遮掩。
- 對應知識：`verification.md` §一四驗。

## 二、Layer 1 細節子命令：拿什麼、解什麼、讀哪裡

| 子命令 | 觸發問題 | 內容 | 解讀知識 |
|---|---|---|---|
| `bazi show` | 身強弱、格局、用神 | 四柱藏干十神納音長生旬空＋五行分＋三得＋用忌調候＋神煞合沖 | `bazi.md`＋`shenqiang/shishen_combo/waige/shensha_use/dizhi_relations` |
| `bazi show --year YYYY` | 流月應期 | 原局＋該年干支＋12流月干支十神 | `bazi.md` §0＋`suiyun.md` |
| `ziwei show` | 性格、單宮細斷 | 十二宮干支主星亮度輔煞四化，一行一宮 | `ziwei.md`＋`star_detail.md`＋`fusha.md` |
| `ziwei show --palaces X,Y` | 指定領域（如財運四宮） | 只出指定宮 | 同上＋`pan-reading.md` §二（三方四正速查） |
| `ziwei show --patterns` | 格局真假 | 格局名／吉凶／required 成立／bonus／breaking | `ziwei.md`（required 全滿足才成立；breaking 有一即降級） |
| `yun year YYYY` | 單年細斷 | 八字歲運／紫微運限／宮位細節／輔助／流月（--full） | `suiyun.md`＋`pan-reading.md` §七 |
| `yun decade --from A --to B` | 多年運 | 總表＋每年塊（同單年豐富） | 同上 |
| `aux liuren [--at-year]` | 過程人事、逐年應 | 終身課全文：四課三傳天地盤神煞年命 | `aux-charts.md` §二＋`liuren.md` §十 |
| `aux qimen` | 方位行動 | 九宮＋命宮＋大限每宮9年 | `aux-charts.md` §三＋`qimen.md` |
| `aux hepan` | 合盤 | 吃兩份盤比對 | `hepan.md`＋`fuqi_stars.md` |

## 三、問項→取用表（LLM 自決）

| 問什麼 | 先跑 | 補什麼子命令 |
|---|---|---|
| 性格／方向 | `summary` | 不夠再 `ziwei show --palaces 命宮,遷移,福德` |
| 事業 | `summary` | `ziwei show --palaces 官祿,命宮,財帛`＋`bazi show` |
| 財運 | `summary` | `ziwei show --palaces 財帛,田宅,官祿,福德`＋`caiyun.md` |
| 感情 | `summary` | `ziwei show --palaces 夫妻,福德,遷移`＋`zuhe` 合盤 |
| 健康 | `summary` | 疾厄看盤：`ziwei show --palaces 疾厄,福德`＋`bazi show`（調候寒暖） |
| 考試文書 | `summary` | `ziwei show --palaces 父母,官祿`＋`bazi show` |
| 多年運／應期 | `summary` | `yun decade --from A --to B`（可加 `--full`）；逐年再加 `aux liuren --at-year` |
| 方位居住 | `summary` | `aux qimen`（方位獨有）＋`ziwei show --palaces 田宅,遷移` |
| 非六問議題 | 歸宮引導 | 見 `zongpan-layered` 七之二：十二宮全覆蓋，真歸不進去回問聚焦 |

## 四、續問與快取

- 同盤續問：只補子命令細節，不重跑 summary。
- 換人／換事：重跑 summary；換事若為具體事件，轉問事軸（`ask-event/_index.md`）。
- 使用者資料（姓名、基本資訊、關係）存本機快取；LLM 應說明「資料僅留存本機」。