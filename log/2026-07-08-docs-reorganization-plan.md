---
type: log
status: fixed
updated: 2026-07-08
truth: docs/HANDOFF.md 14章（実行後に追記される）
---

# ドキュメント再編 実行計画書（2026-07-08）

> **この文書は実行指示書。** 判断はすべて策定済み（Opus 4.8 セッションで本人承認済み）。
> 実行セッションは本書を上から順に、書いてあるとおりに実行すればよい。**本書に書いていない判断はしない。**
> 迷う箇所が出たら実行を止めて本人に確認する（勝手に補完しない）。

## 0. 背景と決定（承認済み）

- **問題**：ドキュメントの大量生産で粒度がバラつき、①用途（サマリー/詳細）の宣言がない ②検討の軌跡の置き場がなくHANDOFFが肥大化 ③タスクリストが3箇所（CLAUDE.md／HANDOFF 9章／work/business-plan-tasks.md）に散在。
- **決定（本人承認 2026-07-08）**：
  1. `work/` を廃止し、`docs/`（現行の正）＋`log/`（検討の軌跡）＋`data/`（作業データ）＋`docs/preview/`（HTML図解）に再編。
  2. **人間用／AI用のドキュメントは分けない**。1ファイル＝frontmatter（AI用メタ）＋本文（人間用の文章）。
  3. 用途（サマリー/詳細/補足）はフォルダでなく frontmatter＋README索引で表現。フォルダは「テーマ」で切る（最大3階層）。
  4. タスクは `docs/TODO.md` に一元化。
  5. 役目を終えた `work/lp-mockup.html`（介護特化のまま＝7/3転換で宙に浮いた）と `docs/MIGRATION.md`（移管完了済み）は archive へ。
- **不変のもの**：`docs/HANDOFF.md` のパス（全参照が生きる）／`deliverables/`／`personal-sessions/`／`archive/` の既存中身。HANDOFF本文1〜13章は**一切書き換えない**（14章の追記のみ）。

## 1. 最終形

```
iterra-business-design/
├── CLAUDE.md                  # 全文差し替え（§6）
├── README.md                  # 新設＝索引（§7）
├── docs/
│   ├── HANDOFF.md             # 14章を末尾追記のみ（§8）
│   ├── TODO.md                # ← work/business-plan-tasks.md（冒頭に§5のセクションを挿入）
│   ├── plan/                  # 10ファイル
│   ├── web/                   # 3ファイル
│   └── preview/               # HTML2ファイル
├── data/
│   └── finance-actual-forecast/   # ← work/finance-actual-forecast（フォルダごと）
├── deliverables/              # 変更なし
├── log/                       # 本計画書＋旧worklog2件
├── archive/                   # ＋lp-mockup.html・MIGRATION.md（README追記 §9）
└── personal-sessions/         # 変更なし
```

## 2. ファイル移動（git bash で実行）

```bash
cd /c/Users/bizis/iterra.jp/iterra-business-design
mkdir -p docs/plan docs/web docs/preview data

# --- docs/plan（9件＋改名1件）---
git mv work/business-plan.md        docs/plan/business-plan.md
git mv work/philosophy.md           docs/plan/philosophy.md
git mv work/method.md               docs/plan/method.md
git mv work/target-conditions.md    docs/plan/target-conditions.md
git mv work/service-definition.md   docs/plan/service-definition.md
git mv work/service-operations.md   docs/plan/service-operations.md
git mv work/pricing.md              docs/plan/pricing.md
git mv work/sales-process.md        docs/plan/sales-process.md
git mv work/lead-acquisition-v2.md  docs/plan/lead-acquisition.md   # v2サフィックス除去
git mv work/revenue-target.md       docs/plan/revenue-target.md

# --- docs/TODO.md ---
git mv work/business-plan-tasks.md  docs/TODO.md

# --- docs/web（3件）---
git mv work/web-structure.md        docs/web/web-structure.md
git mv work/lp-structure.md         docs/web/lp-structure.md
git mv work/site-copy-draft.md      docs/web/site-copy-draft.md

# --- docs/preview（未追跡ファイルなので通常mv＋add）---
mv work/accompaniment-tasks.html    docs/preview/
mv work/business-operations-map.html docs/preview/
git add docs/preview

# --- data ---
git mv work/finance-actual-forecast data/finance-actual-forecast

# --- archive行き（本人承認済みの推奨。理由は§9のREADME追記文）---
git mv work/lp-mockup.html          archive/lp-mockup.html
git mv docs/MIGRATION.md            archive/MIGRATION.md

# --- log行き（archiveに仮置きされていた「軌跡」を本来の場所へ）---
git mv archive/worklog-2026-06-21.md  log/2026-06-21-worklog.md
git mv archive/summary-20260623.md    log/2026-06-23-session-summary.md

# work/ が空になったことを確認して削除
ls work/ && echo "★空でない！中身を確認して止まる" || rmdir work
```

**注意**：`.claude/` 配下（settings.local.json とそのバックアップ）はこの再編と無関係。**触らない・コミットに含めない。**

## 3. frontmatter の付与

`docs/` 配下の全 md（HANDOFF.md を除く）の**先頭**に、以下のテンプレートで挿入する。既存本文は一切変えない。

```yaml
---
type: <下表>
status: draft
updated: 2026-07-08
parent: <下表>
truth: <下表>
---
```

| ファイル | type | parent | truth |
|---|---|---|---|
| docs/plan/business-plan.md | summary | （行ごと省略） | docs/HANDOFF.md（食い違えばHANDOFF優先） |
| docs/plan/philosophy.md | detail | docs/plan/business-plan.md 1章 | docs/HANDOFF.md 1〜2章 |
| docs/plan/method.md | detail | docs/plan/business-plan.md 2章 | docs/HANDOFF.md 12章 |
| docs/plan/target-conditions.md | detail | docs/plan/business-plan.md 3章 | docs/HANDOFF.md 13章 |
| docs/plan/service-definition.md | detail | docs/plan/business-plan.md 6章 | docs/HANDOFF.md 11章 |
| docs/plan/service-operations.md | detail | docs/plan/business-plan.md 6章 | docs/HANDOFF.md 13章 |
| docs/plan/pricing.md | detail | docs/plan/business-plan.md 6章 | docs/HANDOFF.md 13章 |
| docs/plan/sales-process.md | detail | docs/plan/business-plan.md 8章 | docs/HANDOFF.md 11章 |
| docs/plan/lead-acquisition.md | detail | docs/plan/business-plan.md 9章 | docs/HANDOFF.md 13章 |
| docs/plan/revenue-target.md | detail | docs/plan/business-plan.md 11章 | docs/HANDOFF.md 6章 |
| docs/web/web-structure.md | detail | docs/plan/business-plan.md 9章 | docs/HANDOFF.md 13章（サイト構成v2） |
| docs/web/lp-structure.md | detail | docs/web/web-structure.md | docs/HANDOFF.md 11章 |
| docs/web/site-copy-draft.md | supplement | docs/web/web-structure.md | docs/HANDOFF.md 12章 |
| docs/TODO.md | tasks | （行ごと省略） | （行ごと省略） |

- `status` は全ファイル `draft`（すべて本人の違和感出し待ちのたたき台のため）。
- summary と tasks では `parent` 行を書かない（空値の行を残さない）。

## 4. パス参照の更新

**対象＝ `docs/plan/` `docs/web/` `docs/TODO.md` `docs/preview/*.html` のみ。**
**HANDOFF.md・archive/・log/・personal-sessions/ は絶対に触らない**（旧パスは履歴として温存する方針）。

対象ファイル内の旧パス表記を以下の対応で置換する（バッククォート内・本文中どちらも）：

| 旧 | 新 |
|---|---|
| `work/business-plan-tasks.md` | `docs/TODO.md` |
| `work/lead-acquisition-v2.md` | `docs/plan/lead-acquisition.md` |
| `lead-acquisition-v2.md`（裸名） | `lead-acquisition.md` |
| `work/finance-actual-forecast` | `data/finance-actual-forecast` |
| `work/lp-mockup.html` | `archive/lp-mockup.html` |
| `work/`＋その他のmd名 | `docs/plan/`（plan10件）または `docs/web/`（web3件）＋同名 |
| `archive/business-plan.md`等 | そのまま（archiveは動いていない） |

手順：`grep -rn "work/" docs/ --include="*.md" --include="*.html" | grep -v HANDOFF` でヒットを列挙し、上表で全件置換 → 再grepで0件を確認。

さらに `data/finance-actual-forecast/` 内のスクリプト・README に `work/` 参照がないか `grep -rn "work/" data/` で確認（相対パスなら修正不要。絶対パスやwork/前提があれば `data/` に直す）。

## 5. docs/TODO.md の冒頭にセクション挿入

frontmatter の直後・既存本文の前に以下を挿入（既存本文＝旧business-plan-tasks.mdは温存）：

```markdown
# TODO — タスクの一元管理

> タスクはこのファイルだけで管理する。CLAUDE.md・HANDOFF にはタスクリストを作らない（2026-07-08 再編）。

## 次にやること（旧CLAUDE.md「次にやること」より移設）

1. たたき台への本人の違和感出し：`docs/plan/lead-acquisition.md`（営業・告知）／`docs/plan/pricing.md`（料金）／`docs/plan/service-operations.md`（本人/外注の業務分解）／`docs/web/web-structure.md`（サイト構成v2。▶要判断4つ＝診断金額明示・「力になれない会社」公開・立ち上げ枠非掲載・現行介護特化サイトの旧コンテンツの扱い）
2. 業種非依存の汎用モデルケース数字（特養C／HCチェーンHの代替。料金の対比材料・クロージング・想定モデルページの源泉）
3. 役員報酬を上げるタイミングと最適額のシミュレーション（法人税＋所得税＋社保の最小化）
4. ~~事業計画書（文章版）の条件ベース作り直し~~ → v3済（`docs/plan/business-plan.md`）。残＝本人の違和感出し
5. ポテンシャル診断の伴走期での組み込み方の具体化
6. 理念・コンセプト文書を「人間味のある言葉」へ書き直し（メソッド名は「ITERRAメソッド」で確定済み 2026-07-03）

---
```

## 6. CLAUDE.md 全文差し替え

以下で**全文置換**する：

````markdown
# iterra-business-design

ゼロベースで「事業の理念・コンセプト・商品・収益構造」を設計するプロジェクト。
**作業を始める前に、必ず `docs/HANDOFF.md`（決定の正）と `README.md`（ドキュメント索引）を読むこと。** 特に以下は提案の前提として常に効かせる。

## 揺らがせない前提（HANDOFF より）

- **判断基準（HANDOFF 1章 P-5）**：迷ったら ①全体の筋が通っているか ②現実で機能するか・根っこに効くか ③相手が主役か・対等か ④自分も伸びるか、で判断する。
- **絶対にしないこと（HANDOFF 2章）**：依存させない／形だけ出さない／手柄を取らない／単一の側面（金だけ・情だけ）で決めない／スキルを偉さ・序列にしない。この5つを上書き・緩和する提案をしない。
- **棄却済みの選択肢を蒸し返さない**：「育成→卒業」コンセプト、「工数×時給」課金は理由があって却下済み（HANDOFF 3章・4章）。覆すなら新事実が要る。
- **ターゲットは業種でなく顧客条件で選ぶ（2026-07-03 転換・HANDOFF 13章）**：介護＋小売の業種絞りはやめ、「条件（経営層の理解と予算／共に動く担当者／変化の過程／緊急度）に合う中小企業」へ。業種決め打ちへ戻す提案は実データなしにしない。定義の正は `docs/plan/target-conditions.md`。

## 進め方のルール

- たたき台を出す → 本人が違和感を起点に削る／直す、の反復で進める。
- 媚びない。合理と感情の両面で率直に。同意できない点は同意しない。
- 整った対句や借り物の専門用語より、本人が普段しゃべる言葉に寄せる（理念文言は最終的に本人が書き換える前提。Claudeはたたき台まで）。
- 抽象論で終わらせず、根本原因まで掘った具体を出す。

## ドキュメント運用ルール（2026-07-08 再編・HANDOFF 14章）

- **1トピック＝1ファイル。新ファイルを作る前に、既存ファイルへの追記を必ず検討する（デフォルトは追記）。**
- 新規ファイルを作ったら `README.md` の索引に1行追加する。索引に載らないファイルは作らない。
- `docs/` 配下の md には frontmatter（type / status / updated / parent / truth）を必ず付ける。type は summary｜detail｜supplement｜tasks。
- ファイル名にバージョン番号を付けない。旧版は `archive/` へ移し、そこで v1 等を付けて `archive/README.md` に「いつ・なぜ」を残す。
- セッションの検討経緯・ボツ案・途中経過は `log/YYYY-MM-DD-<テーマ>.md` に書く。`docs/HANDOFF.md` には決定の抽出（決定・なぜ・覆さない条件）だけを追記する（肥大化させない）。
- HTML の置き場は2つだけ：`docs/preview/`（mdの視覚化・モック。正はmd側＝冒頭コメントに出典mdを明記）／`deliverables/`（完成成果物）。
- タスクは `docs/TODO.md` に一元管理。CLAUDE.md・HANDOFF にタスクリストを作らない。

## ディレクトリ構造

```
iterra-business-design/
├── CLAUDE.md
├── README.md            # ドキュメント索引（地図）。新規ファイルは必ずここに登録
├── docs/                # 現行の正
│   ├── HANDOFF.md       # 最重要。決定事項・各決定の「なぜ」・覆さない条件
│   ├── TODO.md          # タスクの一元管理
│   ├── plan/            # 事業計画（サマリー＝business-plan.md＋詳細9件）
│   ├── web/             # サイト関連（構成・LP・コピー）
│   └── preview/         # HTML図解・モック（正はmd側）
├── data/                # 作業データ＋スクリプト（finance-actual-forecast）
├── deliverables/        # 完成成果物（keiei_model.xlsx ほか）
├── log/                 # 検討の軌跡（YYYY-MM-DD-テーマ.md）
├── personal-sessions/   # 個人的な仮セッションの成果物（別枠保管）
└── archive/             # 差し替え済み・棚上げ（消さず保管。理由は archive/README.md）
```

**`docs/` は「現行の正」だけを置く。** 差し替え・撤回したものは消さず `archive/` へ移し、`archive/README.md` に「いつ・なぜ」を残す。

## 成果物を触るときの注意

- `deliverables/keiei_model.xlsx`：**前提シートの黄色い入力セルだけを変える。数式は壊さない。** 検算は `openpyxl` で読み、LibreOffice等で再計算してから値を確認する。
- `deliverables/concept-visual.html`：循環図などのノード配置・矢印は座標を手調整せず三角関数で計算して生成する。編集後は必ずブラウザで表示確認する。
- **決定の「なぜ」を消さない。** 新しい判断をしたら `docs/HANDOFF.md` に追記し、「いつ・なぜ・覆さない条件」を残す。

## 次にやること

`docs/TODO.md` を見る（タスクはそこに一元管理。ここには書かない）。
````

## 7. README.md（新設・索引）

リポジトリ直下に以下の内容で新規作成：

````markdown
# iterra-business-design ドキュメント索引

新セッションはまず `docs/HANDOFF.md`（決定の正）→ この索引 → `docs/TODO.md` の順に読む。
カテゴリの意味：**docs/**＝現行の正／**log/**＝検討の軌跡／**archive/**＝差し替え済み（消さない）／**deliverables/**＝完成成果物／**data/**＝作業データ。
**新規ファイルを作ったら、必ずこの索引に1行追加すること。**

## docs/（現行の正）

| ファイル | 用途 | 内容 |
|---|---|---|
| `docs/HANDOFF.md` | 決定の正 | 全決定と「なぜ・覆さない条件」。最重要・別格 |
| `docs/TODO.md` | タスク | 未決事項・次にやることの一元管理 |
| `docs/plan/business-plan.md` | サマリー | 事業計画書 統合マスター v3（条件ベース）。全体はまずこれ |
| `docs/plan/philosophy.md` | 詳細 | MVV＋一言コンセプト（3＋1運用） |
| `docs/plan/method.md` | 詳細 | ITERRAメソッド（3軸×3フェーズ） |
| `docs/plan/target-conditions.md` | 詳細 | ターゲット条件 M1〜M4／Red Flags（ターゲット定義の正） |
| `docs/plan/service-definition.md` | 詳細 | Phase0診断・伴走の商品定義・契約 |
| `docs/plan/service-operations.md` | 詳細 | 業務分解（★本人コア／◆外注可／▲資産化） |
| `docs/plan/pricing.md` | 詳細 | 料金表・含む/含まない・内部検算 |
| `docs/plan/sales-process.md` | 詳細 | 無料相談→診断の売り方 |
| `docs/plan/lead-acquisition.md` | 詳細 | リード獲得（条件ベース・観測可能シグナル5つ・チャネル7つ） |
| `docs/plan/revenue-target.md` | 詳細 | 必要売上・個人サバイバル |
| `docs/web/web-structure.md` | 詳細 | サービスサイト構成 v2（9ページ） |
| `docs/web/lp-structure.md` | 詳細 | 無料相談LPの構成 |
| `docs/web/site-copy-draft.md` | 補足 | FV・トップ・メソッドのコピー案（本人の口調書き換え待ち） |
| `docs/preview/accompaniment-tasks.html` | プレビュー | 伴走業務 大中小分解の図解（正＝service-operations.md） |
| `docs/preview/business-operations-map.html` | プレビュー | 事業運営 業務体系マップ（正＝service-operations.md） |

## その他

| 場所 | 内容 |
|---|---|
| `deliverables/` | keiei_model.xlsx（経営シミュ・黄色セルのみ編集可）／jigyo-keikaku_format.xlsx（融資用）／concept-visual.html（コンセプト設計図） |
| `data/finance-actual-forecast/` | 法人＋個人 統合収支のデータ取込（クレカ明細CSV・Pythonスクリプト） |
| `log/` | セッションごとの検討の軌跡（YYYY-MM-DD-テーマ.md）。決定の抽出はHANDOFFへ |
| `archive/` | 差し替え済み・棚上げ文書。理由は `archive/README.md`。業種資産（介護・小売）は手札として保管 |
| `personal-sessions/` | 個人的な仮セッションの成果物（正でも引退でもない別枠） |
````

## 8. docs/HANDOFF.md への追記（末尾の斜体行の直前に挿入）

**1〜13章は一文字も変えない。** 末尾の `*この文書は仮置き(DRAFT v1)...*` 行の直前に以下を挿入：

```markdown
## 14. 2026-07-08 ドキュメント再編（構造のみ・決定内容の変更なし）

- **決定**：`work/` を廃止し、`docs/`（現行の正：plan／web／preview）＋`log/`（検討の軌跡）＋`data/`（作業データ）に再編。全mdにfrontmatter（type/status/updated/parent/truth）を付与し、`README.md`＝索引を新設。タスクは `docs/TODO.md` に一元化。
- **なぜ**：ドキュメントの大量生産で粒度がバラつき、①サマリー/詳細の区別が外から見えない ②検討の軌跡の置き場がなく本HANDOFFが肥大化 ③タスクが3箇所に散在、していたため。
- **運用（以後のルール）**：セッションの検討経緯・ボツ案は `log/` へ。本HANDOFFには**決定の抽出（決定・なぜ・覆さない条件）だけ**を追記する。人間用/AI用のドキュメントは分けない（1ファイル＝frontmatter＋本文）。
- **パス対応**：`work/*.md` → `docs/plan/` または `docs/web/`（`lead-acquisition-v2.md`→`lead-acquisition.md` に改名）／`work/business-plan-tasks.md`→`docs/TODO.md`／`work/finance-actual-forecast`→`data/`／`work/lp-mockup.html`（介護特化のまま宙に浮いていた）と `docs/MIGRATION.md`（役目終了）→`archive/`。**本文1〜13章の旧 `work/` パスは履歴として書き換えない。**
- **覆さない条件**：構造の再変更は、運用して具体的な不便（探せない・迷子になる等）が出たときのみ。思いつきでの再編はしない。

---
```

## 9. archive/README.md への追記

表の末尾に2行追加：

```markdown
| `lp-mockup.html` | work/ | 2026-07-08 再編。タイトルが「介護の現場ITを…」＝介護特化のままで、2026-07-03 条件ベース転換（HANDOFF 13章）により宙に浮いていた。条件ベース版モック作成時の参考として保管。 |
| `MIGRATION.md` | docs/ | 2026-07-08 再編。Claude Code への移管が完了し役目終了。 |
```

表の下の注記の後に1行追加：

```markdown
> worklog-2026-06-21.md と summary-20260623.md は 2026-07-08 再編で `log/` へ移動（「検討の軌跡」カテゴリ新設に伴い本来の置き場へ。archiveの役割＝差し替え済み成果物、とは別物のため）。
```

## 10. preview HTML の出典コメント確認

- `docs/preview/accompaniment-tasks.html`：冒頭に出典コメントあり（`work/service-definition.md`等）→ パスを `docs/plan/` に更新。
- `docs/preview/business-operations-map.html`：出典コメントなし → `<title>` 直後あたりに追加：
  `<!-- 出典：docs/plan/service-operations.md ／ docs/HANDOFF.md 13章。正はmd側（このHTMLは視覚化） -->`

## 11. メモリの更新

`C:\Users\bizis\.claude\projects\C--Users-bizis-iterra-jp-iterra-business-design\memory\` 内で旧パスを更新：

- `business-design-current-state.md`・`MEMORY.md`：`work/target-conditions.md` → `docs/plan/target-conditions.md`
- `finance-integrated-pl.md`・`MEMORY.md`：`work/finance-actual-forecast/` → `data/finance-actual-forecast/`
- `lead-acquisition-open-items.md`：`work/`・`lead-acquisition-v2` 参照があれば新パスへ
- `docs-reorganization-pending.md` を**削除**し、`MEMORY.md` から該当行を消す（実行完了で役目終了）
- 再編自体の新規メモリは**作らない**（HANDOFF 14章とREADMEに記録済み＝リポジトリが正）

## 12. 検証チェックリスト

- [ ] `work/` ディレクトリが存在しない
- [ ] `git status` で移動が rename として認識されている（大量の delete+add でない）
- [ ] `grep -rn "work/" docs/ README.md CLAUDE.md --include="*.md" --include="*.html" | grep -v HANDOFF` → **0件**
- [ ] `grep -rn "work/" data/` → 0件（またはスクリプトが相対パスで自己完結）
- [ ] `docs/` 配下の全md（HANDOFF除く）に frontmatter がある
- [ ] README.md の索引に載っている全ファイルが実在する（逆も：docs/配下に索引にないファイルがない）
- [ ] HANDOFF.md の diff が「14章の挿入のみ」である（`git diff docs/HANDOFF.md` で確認）
- [ ] `.claude/` 配下が git のステージに入っていない

## 13. コミット（検証が全部通ってから・本人に diff 概要を見せて確認後）

```
ドキュメント再編：work/廃止→docs/(正)+log/(軌跡)+data/(データ)へ再構成

- docs/plan・docs/web・docs/preview のテーマ別に現行の正を集約、全mdにfrontmatter付与
- README.md=索引を新設、タスクをdocs/TODO.mdに一元化
- log/新設（検討の軌跡。旧worklog2件をarchiveから移動）
- lp-mockup.html（介護特化のまま）とMIGRATION.md（役目終了）をarchiveへ
- 運用ルールをCLAUDE.mdに追加、決定はHANDOFF 14章に記録

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
```

`.claude/settings.local.json` とその doctor-backup はコミットに**含めない**。
