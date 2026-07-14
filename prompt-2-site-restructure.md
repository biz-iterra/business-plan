# 【実装タスク】事業計画に基づくサイト再構成（窓の再構成＋①詳細改稿＋新規4ページ）

## 設計の正（必ず最初に両方読むこと）

1. `C:\Users\bizis\iterra.jp\iterra-business-design\docs\web\web-structure.md`
   … サイトツリー（§3）・各ページのセクション構成（§5）・修正リスト（§4）
2. `C:\Users\bizis\iterra.jp\iterra-business-design\docs\web\site-copy-draft.md`
   … 全ページの実テキストひな型（§0〜§8）。**コピーはこのひな型を使う**（たたき台だが、勝手な創作はせず、実装上の最小調整のみ可）

## 実装順（この順で。各ステップごとに `pnpm build` で検証）

### 1. `/business/`（窓）の再構成 … コピー§1

- 「選ばれる理由」「業務内容の例」「契約までの流れ(4step)」を削除（→ステップ2へ移設）
- 新構成：コーポレートITとは → 3事業の川の流れ → ①の階段＋2入口分岐ボタン → ラーニングバナー＋③の一言 → 料金の考え方(3行) → 相談への流れ(3step)＋CTA

### 2. `/business/hands-on-support/` の改稿 … コピー§2

- 既存の骨格（イントロ／共感／問題提起／メソッド4枚／差別化／進め方／FAQ／CTAフォーム）は活かす
- 追加：
  - 選ばれる理由（窓から移設・FeatureList）
  - 対応領域6枚（ServiceCards をこのページへ移設。**コピー§2-6の文面に差し替え＝「代行します」の語を使わない**）
  - 伴走の中身（コピー§2-7）
  - メソッドページへのCTA
  - assessment へのリンク

### 3. 新規ページ4枚（この順）

| ページ | コピー | 備考 |
|---|---|---|
| `/business/hands-on-support/assessment/` | §3 | 診断30万〜の正価明示 |
| `/business/hands-on-support/method/` | §4 | 3×3マトリクスは Table 部品 |
| `/business/hands-on-support/fit/` | §5 | **「力になれない会社」は置かない** |
| `/faq/` | §6 | |

### 4. ナビ更新（`SiteHeader.tsx`）

- 事業紹介ドロップダウンに「アセスメント」「ITERRAメソッド」「合う会社」を追加
- `/faq/` はナビに入れずフッターに追加

### 5. `/company/` に追記 … コピー§7

- わたしたちがしないこと5つ＋代表プロフィール枠

### 6. `/business/learning/` の末尾に1行だけ追加 … コピー§8

- それ以外は一切触らない

## 制約（違反したらやり直し）

- DS部品（`@iterra-inc/ui`）のみで組む。新規UIコンポーネントを作らない。色は soleil 基調
- 業種名（介護・小売等）を書かない／①の文脈で「代行します」と書かない／立ち上げ枠・料金一覧（伴走の月額）・従量ブロックを載せない
- 数字の掲示は診断30万〜・50万〜のみ。伴走は「月額固定・診断後に提案」の表現まで
- 新規ページは PageLayout に固有の title/description、PageHeader＋パンくず必須
- CTA の遷移先は `/contact/`（既存の `?inquiry=` パラメタを踏襲）

## 検証（必須）

- [ ] `pnpm build` → `dist/` を grep：「介護」「立ち上げ枠」「5社限定」が無いこと
- [ ] 全新規ページがビルドされ、内部リンク（窓→詳細→assessment→contact、fit→faq）が切れていないこと
- [ ] localhost:2010 で 窓→①→assessment→method→fit→faq の回遊を目視確認
