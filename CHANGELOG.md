# Changelog

本 repo 版本以 git tag 標記（語意化版號）。

## v0.8.2

- **修奇門旬首落中宮 crash**（`KeyError: 5`）：旬首儀落中五宮時值符為天禽，中宮無固定八門，值使改寄坤二（死門，與值使宮同例）。58,440 時刻 × 時盤/終身盤掃描全過（含 13,002 例落中宮）。
- 測試：`test_qimen.py` 新增回歸 1 條。

## v0.8.1

- **多年運總表** `scripts/decade.py`（`--from A --to B`，一年一行：八字流年幹支十神＋大運柱｜紫微大限宮＋流年宮＋流忌）：回答時間窗問題（前五年後五年）一次跑完，**禁逐年迴圈呼叫引擎**（N 年＝2N 次呼叫，又慢又易錯）。
- **引導修正**：問人總覽預設跑 `person_cast.py`（主盤＋雙輔助盤），`cast.py` 降為輕量選項；`pan-reading.md` 步驟 7–8 明寫觸發條件；`SKILL.md` 強約束新增 #5（總覽含輔助盤）＋#1（不翻引擎原始碼找答案）；`verification.md` 新增問人主盤×輔助盤裁決；`ziwei.md` 補頂層 JSON 鍵一覽（阻止 LLM 翻 `.sh`/bundle 找結構）。
- 測試：共 **142 條**（新增 `test_decade.py` 4 條）。

## v0.8.0

- **問事軸：大六壬（三式之一）全套引擎** `scripts/yijing/liuren_core.py` + CLI `liuren.py`。月將**中氣換將**、月將加占時旋**天地盤**、京房**四課**、**九宗門**取三傳（賊克／比用／涉害／遙克／昴星／別責／八專／伏吟／返吟）、十二天將（晝夜貴人順逆）、遁干／旬空／六親／神煞／本命行年／課體。純規則計算，零安裝。
- **四式融合入口** `scripts/yijing/event_cast.py`：同一時刻一次出**六爻＋梅花＋六壬＋奇門時盤**四盤，附客觀交叉（四柱一致／日柱一致／子時換日警示）。程式只算事實，不斷吉凶。
- **解讀思路** `references/ask-event/liuren.md`：讀課 SOP、盤面欄位意義、九宗門／課體、類神（用神）對照、十二天將、**多式綜合閱讀**、**矛盾裁決**、輸出品質。`_index.md`／`questioning.md`／`principles.md`／`verification.md`／`SKILL.md` 同步補六壬與多式。
- **古籍解讀精華** `references/ask-event/liuren-classics.md`：提煉安倍晴明《占事略決》、宋《六壬神定經》、清《壬學瑣記》之**讀課邏輯鏈**（干我支彼、旺相死囚休、神將內外戰、上下剋指向、年命切己）、十二天將旺衰斷、十二月將主事、三十六課體、應期法（河魁相乘／歲月日時為期）、神煞（德／鬼／殺／刑害）、取象派心法，並列 **流派衝突與本 skill 取捨**（貴人旦暮、比用陰陽 vs 五行、長生順布、伏吟末傳、涉害計法），原文不入 repo。
- **六壬引擎補強**：月令**旺相死囚休**（所勝所憂）與**月將主事**輸出；`wangxiang()` 以月支五行推五氣。
- **六壬終身課（問人輔助盤）**：`liuren.py --lifetime --time <出生時刻> --gender 男/女 [--at-year]`——以出生時刻起課讀一生；本命＝一生之應、行年＝逐年之應。讀法見 `liuren.md` 第十節（權重低於八字紫微，不翻轉主盤）。
- **三十六課體自動判定**：`compute_keti` 擴充——九宗門細分（知一／見機／察微／綴瑕／虎視／冬蛇掩目／蕪淫／帷薄／獨足／自任／自信／無依／無親）＋三合局（曲直/炎上/稼穡/從革/潤下）＋三交／連茹（進退）／間傳／元胎／亂首／龍戰／勵德／無祿／絕紀／斬關／高蓋駟馬／鑄印乘軒／斲輪織綬。對照 `liuren-classics.md` 第七節。
- **奇門遁甲引擎** `scripts/yijing/qimen_core.py` + CLI `qimen.py`：**拆補法**定局（節氣＋三元）、**轉盤**、**陽盤**（節氣陰陽遁）、子時換日；地盤三奇六儀、值符值使、天盤九星、八門、八神、格局（伏吟/反吟/門迫/五不遇時/天網四張/三奇六儀八門入墓/三奇得使/三遁/玉女守門/六儀擊刑/**十干克應全表 81 格**）、真太陽時。純算術、零安裝。
- **奇門終身盤**：`qimen.py --lifetime`——以生時局為本、**年干落宮為命宮**（《奇門遁甲統宗》）、**大限一宮9年**、各宮門星神干＋大限＋**六親宮**（年干父／合干母／月干兄弟／日干本人／時干子女；奇門原生區分雙胞胎）。
- **問人總入口** `scripts/person_cast.py`：主盤（八字＋紫微）＋輔助盤（**六壬終身課**＋**奇門終身盤**）。**主盤為骨幹、輔助補維度、不翻轉格局**。
- **解盤邏輯鏈文件**：`ask-event/qimen.md`（起局、四盤結構、九宮象意、用神取法、八門九星八神、吉凶格局、**方位行動指引**）；`ask-person/aux-charts.md`（主輔架構、六壬終身課與奇門終身盤讀法）。
- **雙胞胎處理**：奇門**六親宮**（月干兄弟 vs 日干本人）為原生區分法；六壬加**次客法**（`--twin N`，換將不換時；古籍自承多不驗，標低置信）；主用主盤（八字時柱進位／紫微借宮）。見 `twins.md` 第五節。
- **驗證基準**：六壬以獨立排盤工具的 720 課結構資料為回歸基準（天地盤／四課／十二天將 **720/720 全對**；三傳 **≥97%**）；奇門以獨立排盤案例對照（陰遁7局上元、值符天冲3宮、值使傷門4宮全中）。
- 測試：共 **138 條**（六壬 11、奇門 7、四式合盤）。
- **問事軸分工（更新）**：成敗細節聽六爻、方向大勢聽梅花、過程人事／來意／結局聽六壬、方位行動聽奇門；多式同向＝高置信，矛盾裁決見 `verification.md`。

## v0.7.1

- **問事軸：用神選定決策樹**（`yongshen.md` 首節）：領域明確→領域用神／領域不明但事體存在→世爻為用（自占吉凶以世爻為用）／完全無焦點→不起卦。古籍依據 5 源以上（世為己應為人／自占以世為用／世應論用神／用神不現尋伏神或再占）；紅線禁為填表編領域。
- **問事軸：引導檢查點**（`liuyao.md` 第五節三道門，不過門不起卦）：用神選定句→澄清兩問（問不出轉世爻為用＋低置信並明示）→現實錨定料；`questioning.md` 可起卦標準同步，明事體缺領域可起（世爻為用）。
- **問事軸：推理自檢＋說過程**：六爻自檢五段／梅花推理三段（agent 內部）；每條斷語附怎麼看出＋結尾邀核對（`liuyao.md` 二b、`meihua.md` 第七節）。
- **問事軸：打架裁決**（`verification.md` 問事補充，本 skill 口徑）：問句漂移→分工（成敗聽六爻／大勢聽梅花；靜卦配變卦互補）→純度加權→同純度真矛盾以六爻為主。
- 測試：文件守衛 4 條（決策樹／檢查點／梅花引導／裁決順序）。

## v0.7.0

- **知識補血（Phase 1，research-first，禁硬猜）**：四域並行研究，每主張 ≥5 獨立來源一致才入庫（報告存 `.scratch/research/`）。新增資料表 `data/shishen_combo.json`（十神組合 7 條）、`data/congge.json`（從弱／從強／真假從＋行運）、`data/ziwei_combo.json`（六吉六煞／輔煞規則／夾宮名目／火貪五件套／疊忌／四化總義／三方權重）、`data/dizhi_xinghaipo.json`（三刑／六害／定性分工；六破備查待定）；新增說法檔 `shenqiang.md`／`shishen_combo.md`／`waige.md`／`suiyun.md`／`shensha_use.md`／`taimingshen.md`／`dizhi_relations.md`／`fusha.md`，`tiaohou.md` 加實戰四步。待定與未驗證（外格雜格／分宮細則／六破／胎息／火空則發）留 pending 區，不作斷語依據。
- **研究糾錯**：`ni_mind.md` 疾厄「子午流注」拆分為宮星＋化忌斷病位（子午流注另屬針灸模組）；合盤五步與流派口訣加出處性質註（後人整理、置信降一級）；`pan-reading.md` 定盤去倪氏 attribution。
- **鬆綁表達（Phase 2）**：禁模糊 → 三級置信（高／中／低）＋看不準單句；`output_lint.py --strict` 改為無標記模糊才擋，帶標記或然記 `notes`；`SKILL.md`／`liuyao.md`／`output-quality.md`／`glossary.md` 同步。
- **算法升級（Phase 3）**：八字加 `strength_classic` 三得標籤（得令／透干／通根／黨眾寡，與分數並陳）；`relations` 補三刑／自刑／六害（六破待定不入）；`cast.py` 加 `caiyun_semantic` 財運語義初判（同向／分歧／單邊／缺料＋進財窗／守財）；`caiyun.md`「矛盾未解」改為必須選邊＋理由＋置信標記。
- **接線**：兩軸入口與 `bazi.md`／`ziwei.md`／`pan-reading.md` 引用新表新欄位；主軸八步與分流結構不變。
- **未做（設計稿在 `.scratch/mingli-accuracy-spec.md` D19／D20）**：Phase 4 衝突解決矩陣、Phase 5 黃金回測集。
- 測試：新增 lint 置信制 2 條、新資料表 4 條、三得標籤 2 條、刑害 1 條、財運語義 1 條（5 態）。

## v0.6.0

- **命理融合主軸（問人）**：新增 `references/ask-person/pan-reading.md`——融合南派（三合）／北派（四化）／子平／倪海廈，八步主軸「**定盤→定調→定體用→量力量→定人事→追因果→定時間→交叉直答**」。取捨：**紫微定象、八字定勢；南派為主、北派四化為輔**；含 **三方四正速查**、十二宮意義、十神速查、四化讀法（生年→大限→流年；自化/來因宮僅參考）、各領域該答什麼、時間軸敘事（八字立春 vs 紫微正月初一）。`bazi.md`／`ziwei.md` 由「讀欄位」升級為「解讀思路」。
- **易經原理升級（問事）**：新增 `references/ask-event/principles.md`——繫辭「吉凶悔吝者，生乎動者也」「極數知來之謂占」「初筮告，再三瀆」；六爻源流（京房納甲→火珠林→《增刪卜易》／《卜筮正宗》；「動爻為重，靜爻為輕」「卦不妄成，爻不虛發」）；梅花源流（邵雍《觀梅數》、先天/後天之數、**《體用總訣》原文**、卦氣旺衰、心易三要＋十應、萬物類象）；倪海廈金錢卦與「人間道」。
- **讀盤強化**：`liuyao.md` 補原神／忌神／仇神與動靜輕重；`meihua.md` 補《體用總訣》原文、先天後天、卦氣旺衰、「用吉變凶／用凶變吉」；`questioning.md`／`_index.md` 補「不疑不卜、不戲占、一天不超過三卦」。
- 測試：104 條通過。

## v0.5.2

- **雙胞胎／多胞胎處理（問人）**：新增 `references/ask-person/twins.md`——先問性別組合／排行／時間差。**龍鳳胎不調盤**（男女大運／大限順逆自然分化）；同性別分四法：紫微**借宮立極**（南派預設）、**時辰遞推**（整盤重算）、**北派同盤**，八字**時柱進位**（子平法）。兩派不可混用。
- **腳本**：
  - `cast.py --twin-order N --twin-ziwei rebase|shift|none`：一次出雙胞胎雙盤；紫微預設 rebase（借宮）。
  - `bazi_pai.py --twin-order N`：**時柱進位**（如己卯→庚辰），年／月／日柱與大運不變，校驗標註「不與真實時支比對」；晚子時／跨兩日暫不支援並明確報錯。
  - 新增 `twin_adjust.py`：**借宮立極**變盤——星曜與宮干留在原支不動、只旋十二宮名；大限自新命宮起並**沿用原局起運歲**；身宮支不動；格局／運限標「僅供參考」，`--at` 時移除並提示重排。
  - `ziwei_full.sh --hour-shift M`：**時辰遞推**（生時進位、整盤重算），bundle 已重建。
- **驗證**：實測確認「借宮」與「遞推」為不同方法（星曜位置不同）。測試 **104 條**（新增：八字時柱進位、借宮星曜不動／大限重錨／身宮不動、遞推整盤重算、cast 三模式與原時支交叉）。

## v0.5.1

- **主軸更明確（治分流不穩）**：`SKILL.md` 主軸改為「命＝人的常數（看生日、長期不變）／卜＝事的變數（看當下起卦、一事一卦、事畢卦止）」＋三秒判準＋**同主題雙問法對照表**（財／感情／事業／健康／官司）；補混合題規則與「交錯使用、取其意不取其名」。分流表加「先問到什麼」（問人：生日時分／性別／城市／曆制；問事：一事一問＋題型）。
- **輸出品質拉回常駐**：`SKILL.md` 常駐「輸出四條」——先直答／每句掛依據／能給應期就給／禁模糊（可能也許大概較像）與萬用話。`shared/output-quality.md` 同步明文禁模糊斷語，並補**占卜版反巴納姆對照**（氛圍話→具體象）。
- **取象題 SOP**：`liuyao.md` 分題型（成敗／時機／取象）＋六親六神取象規則（子孫＝飲食、父母＝場所訊息、兄弟＝第三人分帳…）＋「兩法交叉要綜合（同向／分歧）」；`meihua.md`、`questioning.md`、`ask-event/_index.md` 同步（起卦前先確認題型）。
- **時間依據原理**：問事以「**心動即占**」為前提，當下時間即時空氣場座標；**梅花**時間起卦＝農曆年支＋月＋日＋時支（程式換算），**六爻**以月建／日辰為旺衰背景（卦象來自搖卦，手搖優先）。起卦用當地時鐘、**不做真太陽時校正**；子時／整點交界記精確分鐘。依據優先序：心動＞銅錢＞外應報數＞當下時間。
- 測試：**100 條**（新增梅花農曆換算、六爻含時柱兩個回歸測試）。

## v0.5.0

- **易經補料**：六爻盤面新增【動爻爻辭】（底本《周易正義》武英殿十三經注疏本；64 卦×6 爻＋乾坤用九用六；新資料檔 `data/yaoci_64.json`，逐卦鎖定維基文庫 oldid、回讀原頁並跨來源校對）；無動爻時明示依月日旺衰／世應／用神推斷，不以「無動爻」當無訊號。梅花盤面補本卦／互卦／變卦的卦辭、象傳、諸事，並算好互卦／變卦對體的生剋疊加（不再讓 AI 心算）。
- **輸出品質統一**：`pan_output`＋`voice`＋`output_style` 合併為 `references/shared/output-quality.md`（先直答、每句掛依據、能給應期就給、反巴納姆、白話少反轉）。移除強制投資免責、健康就醫、翻轉條件與輸出格式模板；免責與健康提醒改由 agent 自行斟酌。
- **結構重整（按需載入）**：`references/` 改按軸分 `ask-person/`（八字／紫微／合盤／擇日／財運）、`ask-event/`（六爻／梅花／用神／起卦前引導）、`shared/`（輸出品質／交叉驗證／術語）；各軸新增 `_index.md` 入口。`workflow`＋`fuyan` 合併為 `shared/verification.md`。`SKILL.md` 由 82 行瘦身至 39 行，只留主軸（問人／問事）、分流、環境、3 條準確性強約束。
- 測試：98 條（新增爻辭完整性、動爻爻辭輸出、靜卦提示、梅花補料與五行疊加）。

## v0.4.2

- **修正「講了跟沒講一樣」**：命盤／流年新增輸出模板 `references/knowledge/pan_output.md`（定調→依據→應期→動作→翻轉），並把「結論先行、必給應期與可執行動作、禁巴納姆」寫進常駐層 `SKILL.md` 紅線。
- **免責收窄**：投資免責只限六爻／梅花**起卦問投資**；命盤／流年財運題不挾帶「不構成投資建議」。
- **新增財運 SOP** `references/methods/caiyun.md`：來源→守財→應期三問，串接紫微財務四宮與八字任財。
- `scripts/output_lint.py` 加 `--strict`：另驗空泛語／巴納姆／免責濫用（預設不變，向後相容）。
- 測試：新增 strict lint 案（共 93 條）。

## v0.4.1

- 六爻／梅花起卦**時間預設系統現在**（現在問＝現在起卦），不再要求使用者先給時間；`--time` 保留給「使用者提供實際起卦時刻」。
- `meihua.py` 無參數即時間起卦（系統現在）；`divine.py` 本已預設系統現在。
- 文件（SKILL.md / workflow / questioning）同步。

## v0.4.0

- **零安裝**：內嵌 `scripts/vendor/lunar_python`（純 Python、MIT、1.0M）與 `scripts/ziwei_full.bundle.mjs`（esbuild 打包 iztro/lunar-javascript、MIT、~880K）。**執行期只需系統 `python3` + `node`，免 pip/npm/venv。**
- 所有 Python 腳本改由 `scripts/vendor` 匯入 lunar_python；`cast.py` 改用當前 Python 直呼子工具。
- `ziwei_full.sh` 優先跑預打包 bundle（純 `node`），找不到才退回 tsx（開發）。
- `check_env.sh` 改檢查 python3／node／內嵌依賴；`setup.sh` 改為**開發用**（重建 vendor 與 bundle）。
- 測試：新增零安裝驗證（系統 python3 跑八字、純 node 跑 bundle）；共 90 條。

## v0.3.0

- 新增 `scripts/check_env.sh`：唯讀環境檢查（python3 / Node.js>=18 / npm / venv+lunar_python / node_modules），列出缺項並回傳退出碼。
- `scripts/setup.sh` 強化：硬性檢查 python3 與 Node.js>=18/npm（缺 node 直接失敗）；冪等（已裝則跳過）；結尾自動跑 `check_env.sh` 驗證。
- `scripts/ziwei_full.sh`：缺 `node_modules` 時給明確指引（不自動安裝）。
- SKILL.md / README 明示：**安裝外掛不會自動裝依賴**，首次使用前必須跑 `setup.sh`。
- 測試：新增 `test_check_env_passes_when_set_up`（共 87 條）。

## v0.2.2

- README 補 Codex 外掛安裝（Codex 讀 `.claude-plugin/marketplace.json`）與本地來源的肥大快取注意事項。
- 實測驗證：`codex plugin marketplace add` → `codex plugin add mingli-master@fortune-master` 安裝成功，`codex exec` 的 skill 清單出現 `mingli-master:mingli-master`；確認 Codex 可載入本 skill（無需另做 Codex 專屬外掛）。

## v0.2.1

- README 補各 agent 的安裝設定（Claude Code 外掛／skill、OpenCode、Codex、Pi、Gemini CLI、其他 agentskills.io 工具），附驗證方法。
- 驗證：`claude plugin validate`（marketplace 與 plugin 皆 passed）；`gemini skills list` 顯示 `mingli-master [Enabled]`；frontmatter 符合 OpenCode/Pi 限制（name 合規、description 286 字 ≤ 1024）。

## v0.2.0

- 發佈包裝：加入 Claude Code 外掛市集（`.claude-plugin/marketplace.json`）與外掛 manifest（`skills/mingli-master/.claude-plugin/plugin.json`），同時相容 Agent Skills 開放標準與 OpenCode 等。
- `SKILL.md` frontmatter 補上規格欄位：`license`、`compatibility`、`metadata`（version/author/repository）。
- README 補跨工具安裝矩陣（Claude Code 外掛／Claude、OpenCode、Codex `.agents/skills`）。
- `setup.sh` 有 lock 時改用 `npm ci`（依賴可重現）；`package-lock.json` 入版控。

## v0.1.0

首個版本。`mingli-master` skill：

- **八字**：真太陽時、四柱、納音/長生/十神支/旬空、胎元/胎息/命宮/身宮、身強弱、格局（月令取格）、用神（扶抑＋窮通寶鑑 120 格調候）、神煞、大運、校驗、流年＋12 流月。
- **紫微斗數**（南派三合為體、北派四化為用）：十二宮、全量格局、本命/大限/流年四化、運限六層（大限/小限/流年/流月/流日/流時）。
- **易經**：六爻（起卦＋排盤＋解卦 SOP）、梅花易數（時間/數字/隨機起卦、體用生剋）。
- **合盤**（8 項比對＋參考分）、**擇日**（通書→個人→紫微三層掃描）。
- 曆制支援：國曆/農曆（＋閏月）。
- 架構：排盤歸腳本、知識歸 `references/`、共用表歸 `data/`（單一真相）；86 條回歸測試。
- 已知發現並修正：八字大運起運由「中氣」改為「節」（原誤差 6 年）。
