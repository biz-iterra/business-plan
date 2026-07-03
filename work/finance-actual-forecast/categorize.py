# -*- coding: utf-8 -*-
"""
法人/個人 統合収支 取り込みパイプライン（カード別→統合台帳）
- 各カードCSVを読み、利用日ベースの明細台帳 ledger_master.csv に統合
- ITERRA勘定科目への推定 + セグメント(法人/個人候補/要確認/除外)を付与
- 要確認は店名単位で重複排除し review_needed.csv に出力
再利用前提：カード追加時は SOURCES に1行足す。形式違いは loader を分岐。
"""
import csv, glob, os, re, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))

# 取り込み対象カード（順次追加）
SOURCES = [
    {
        "name": "セゾンAMEX法人",
        "owner": "法人",
        "loader": "saison",
        "glob": r"G:\マイドライブ\01_businessFile\00_ITERRA株式会社\20_税務関係(税理士共有)\クレジット明細\セゾンプラチナ（法人）\SAISON_*.csv",
    },
    {
        "name": "セゾンAMEX個人",
        "owner": "個人",
        "loader": "saison",
        "glob": r"G:\マイドライブ\01_businessFile\00_ITERRA株式会社\20_税務関係(税理士共有)\クレジット明細\セゾンプラチナ（個人）\SAISON_*.csv",
    },
    {
        "name": "OLIVE(SMCC)",
        "owner": "個人",  # 本人(石田優輝)名義・Oliveゴールド
        "loader": "olive",
        "glob": r"G:\マイドライブ\01_businessFile\00_ITERRA株式会社\20_税務関係(税理士共有)\クレジット明細\SMCC（OLIVE）\2*.csv",
    },
    {
        "name": "Amazonゴールド(SMCC)",
        "owner": "個人",  # 本人名義・Amazonマスター
        "loader": "olive",  # SMCC同形式
        "glob": r"G:\マイドライブ\01_businessFile\00_ITERRA株式会社\20_税務関係(税理士共有)\クレジット明細\SMCC（Amazon）\2*.csv",
    },
    {
        "name": "JALカード(UFJ NICOS)",
        "owner": "個人",  # 本人名義
        "loader": "nicos",
        "glob": r"G:\マイドライブ\01_businessFile\00_ITERRA株式会社\20_税務関係(税理士共有)\クレジット明細\UFJ NICOS\2*.csv",
    },
    {
        "name": "住信SBI(法人)",
        "owner": "法人",
        "type": "bank",
        "loader": "bank_sbi",
        "glob": r"G:\マイドライブ\00_myDrive\銀行入出金明細\SBIネット（法人）\nyushukinmeisai_*.csv",
    },
    {
        "name": "住信SBI(個人)",
        "owner": "個人",
        "type": "bank",
        "loader": "bank_sbi",
        "glob": r"G:\マイドライブ\00_myDrive\銀行入出金明細\SBIネット（個人）\nyushukinmeisai_*.csv",
    },
    {
        "name": "SMBC(法人)",
        "owner": "法人",
        "type": "bank",
        "loader": "bank_smbc",
        "glob": r"G:\マイドライブ\00_myDrive\銀行入出金明細\SMBC（法人）\*.csv",
    },
    {
        "name": "SMBC(個人_ときわ台)",
        "owner": "個人",
        "type": "bank",
        "loader": "bank_smbc_indiv",
        "glob": r"G:\マイドライブ\00_myDrive\銀行入出金明細\SMBC（個人_ときわ台支店）\*.csv",
    },
    {
        "name": "SMBC(個人_新宿西口)",
        "owner": "個人",
        "type": "bank",
        "loader": "bank_smbc_indiv",
        "glob": r"G:\マイドライブ\00_myDrive\銀行入出金明細\SMBC（個人_新宿西口支店）\*.csv",
    },
    {
        "name": "楽天銀行(個人)",
        "owner": "個人",
        "type": "bank",
        "loader": "bank_rakuten",
        # 全期間版(2019-2026)を work/_src/ にコピーして参照（G:\...\楽天\RbTorihiki-*.csv）。
        "glob": os.path.join(BASE, "_src", "RbTorihiki-*.csv"),
    },
]

DATE = re.compile(r"^\d{4}/\d{2}/\d{2}$")

# (キーワード, 勘定科目, セグメント)。上から順に最初の一致を採用。
# セグメント: 法人 / 個人候補 / 要確認 / 除外
RULES = [
    # --- 除外（支出でない） ---
    ("ご入金", "（入金・支出でない）", "除外"),
    ("ご返済", "（返済・支出でない）", "除外"),
    ("キャッシング", "借入金（キャッシング）", "除外"),
    ("リボ切替", "（リボ振替・二重計上のため除外）", "除外"),
    ("リボ残高", "（リボ振替・二重計上のため除外）", "除外"),
    # --- 租税公課（法人） ---
    ("法人税", "租税公課・法人税等", "法人"),
    ("地方法人税", "租税公課・法人税等", "法人"),
    ("消費税", "租税公課・消費税", "法人"),
    ("地方税共同機構", "租税公課・地方税", "法人"),
    ("ELTAX", "租税公課・地方税", "法人"),
    ("eLTAX", "租税公課・地方税", "法人"),
    ("地方税", "租税公課・地方税", "法人"),
    ("中央区", "租税公課・地方税", "法人"),
    # --- ソフトウェア利用料（法人） ---
    ("エックスサーバー", "通信費・サーバー/ドメイン", "法人"),
    ("WORKSPACE", "ソフトウェア利用料・Google Workspace", "法人"),
    ("GOOGLE*CLOUD", "ソフトウェア利用料・Google Cloud", "法人"),
    ("GOOGLE *CLOUD", "ソフトウェア利用料・Google Cloud", "法人"),
    ("YOUTUBEPREMIUM", "ソフトウェア利用料・YouTube Premium", "要確認"),
    ("ITA IFS", "外貨積立（個人・USD建て650+200→2026/7〜200USD・法人カード払い）", "個人候補"),
    ("ITA", "外貨積立（個人・USD建て貯蓄）", "個人候補"),
    ("ANTHROPIC", "ソフトウェア利用料・生成AI(Claude)", "法人"),
    ("CLAUDE", "ソフトウェア利用料・生成AI(Claude)", "法人"),
    ("OPENAI", "ソフトウェア利用料・生成AI", "法人"),
    ("ZOOM", "ソフトウェア利用料・Zoom", "法人"),
    ("FREEE", "ソフトウェア利用料・freee", "法人"),
    ("FEEEP", "ソフトウェア利用料・その他SaaS", "要確認"),
    # --- 通信費（法人） ---
    ("03PLUS", "通信費・IP電話(03Plus)", "法人"),
    ("ドコモレンタル", "通信費・機器レンタル", "法人"),
    ("ドコモ", "通信費・携帯電話", "法人"),
    # --- 水道光熱費（法人・社宅按分） ---
    ("CDエナジー", "水道光熱費・電気", "法人"),
    ("エナジー", "水道光熱費・電気", "法人"),
    ("東京ガス", "水道光熱費・ガス", "法人"),
    ("水道", "水道光熱費・水道", "法人"),
    # --- 地代家賃（法人） ---
    ("BIZ SPOT", "地代家賃・コワーキング(BIZ SPOT)", "法人"),
    ("IIOFFICE", "地代家賃・コワーキング(IIOFFICE)", "法人"),
    ("バーチャルオフィス", "地代家賃・バーチャルオフィス(レゾナンス)", "法人"),
    ("レゾナンス", "地代家賃・バーチャルオフィス(レゾナンス)", "法人"),
    # --- 旅費交通費（法人寄り・近距離移動） ---
    ("LUUP", "旅費交通費・シェアサイクル(LUUP)", "法人"),
    ("UBER", "旅費交通費・タクシー/配車", "法人"),
    ("GOアプリ", "旅費交通費・タクシー/配車(GO)", "法人"),
    ("タクシー", "旅費交通費・タクシー/配車", "法人"),
    ("タイムズカー", "旅費交通費・レンタカー", "法人"),
    ("レンタカー", "旅費交通費・レンタカー", "要確認"),
    ("ENTERPRISE RENT", "旅費交通費・レンタカー(海外)", "要確認"),
    ("えきねっと", "旅費交通費・電車/新幹線", "法人"),
    ("スマートEX", "旅費交通費・電車/新幹線", "法人"),
    ("EXPRESS予約", "旅費交通費・電車/新幹線", "法人"),
    ("モバイルSUICA", "旅費交通費・電車/Suica", "法人"),
    ("ターミナル", "旅費交通費・電車/駅", "法人"),
    ("PASMO", "旅費交通費・交通系IC(PASMO)", "要確認"),
    ("SUICA", "旅費交通費・交通系IC(Suica)", "要確認"),
    ("空港", "旅費交通費・空港", "要確認"),
    ("SPLITIT", "スマホ分割(Googleストア・月3,012×24・端末72,280・個人)", "個人候補"),
    ("GOOGLE PAYMENT", "（要確認）Google課金(広告/Play等・要特定)", "要確認"),
    ("GOOGLE PAY", "（要確認）Google課金(広告/Play等・要特定)", "要確認"),
    # --- 旅行・宿泊（要確認：出張 or 私的） ---
    ("トラベル", "旅費交通費・宿泊/旅行手配", "要確認"),
    ("ツアー", "旅費交通費・宿泊/旅行手配", "要確認"),
    ("旅行手配", "旅費交通費・宿泊/旅行手配", "要確認"),
    ("タイムデザイン", "旅費交通費・宿泊/旅行手配", "要確認"),
    ("星野リゾート", "旅費交通費・宿泊", "要確認"),
    ("リゾート", "旅費交通費・宿泊", "要確認"),
    ("AIRBNB", "旅費交通費・宿泊", "要確認"),
    ("BOOKING.COM", "旅費交通費・宿泊", "要確認"),
    ("AGODA", "旅費交通費・宿泊", "要確認"),
    ("HOTEL", "旅費交通費・宿泊", "要確認"),
    ("ホテル", "旅費交通費・宿泊", "要確認"),
    ("青年館", "旅費交通費・宿泊", "要確認"),
    ("旅行保険", "旅費交通費・海外旅行保険", "要確認"),
    ("/AIR", "旅費交通費・航空/旅行", "要確認"),
    # --- 広告宣伝費（法人） ---
    ("プリントパック", "広告宣伝費・印刷", "法人"),
    ("印刷", "広告宣伝費・印刷", "法人"),
    # --- 会議費/接待交際費（要確認：金額で会議/接待を後判定） ---
    ("焼肉", "接待交際費or会議費・飲食", "要確認"),
    ("割烹", "接待交際費or会議費・飲食", "要確認"),
    ("鉄板焼", "接待交際費or会議費・飲食", "要確認"),
    ("レストラン", "接待交際費or会議費・飲食", "要確認"),
    ("RESTAURANT", "接待交際費or会議費・飲食", "要確認"),
    ("ワイン", "接待交際費or会議費・飲食", "要確認"),
    ("醸造", "接待交際費or会議費・飲食", "要確認"),
    ("BRASSERIE", "接待交際費or会議費・飲食", "要確認"),
    ("楽天ペイ", "接待交際費or会議費・飲食(楽天ペイ)", "要確認"),
    ("スターバックス", "会議費・飲食（スターバックス）", "要確認"),
    ("カフェ", "会議費・飲食（その他）", "要確認"),
    ("コーヒー", "会議費・飲食（その他）", "要確認"),
    ("食堂", "会議費・飲食（その他）", "要確認"),
    ("PHO", "会議費・飲食（その他）", "要確認"),
    ("VENDOR", "会議費・自販機/飲食", "法人"),
    # --- Amazon（業務/私的が品目混在・要注文履歴で分割） ---
    ("AMAZON.CO.JP", "（要明細）Amazon・業務/私的混在（注文履歴で分割）", "要確認"),
    ("AMAZON", "（要明細）Amazon・業務/私的混在（注文履歴で分割）", "要確認"),
    ("AMZN", "（要明細）Amazon・業務/私的混在（注文履歴で分割）", "要確認"),
    # --- 個人候補（私的性が強い・役員貸付/賞与候補） ---
    ("ZOZOTOWN", "（個人候補）衣服", "個人候補"),
    ("LACOSTE", "（個人候補）衣服", "個人候補"),
    ("SHIPS", "（個人候補）衣服", "個人候補"),
    ("アウトレット", "（個人候補）衣服/物販", "個人候補"),
    ("OUTLET", "（個人候補）衣服/物販", "個人候補"),
    ("A AND F", "（個人候補）衣服/物販", "個人候補"),
    ("AND-PLANTS", "（個人候補）植物/雑貨", "個人候補"),
    ("ビックカメラ", "（個人候補）家電", "個人候補"),
    ("テックランド", "（個人候補）家電", "個人候補"),
    ("ビックカメラ", "（個人候補）家電", "個人候補"),
    ("ポニークリーニング", "（個人候補）クリーニング", "個人候補"),
    ("クリーニング", "（個人候補）クリーニング", "個人候補"),
    # --- 生活費（個人候補・主に個人カード） ---
    ("オーケー", "（個人候補）食料品/スーパー", "個人候補"),
    ("マルマンストア", "（個人候補）食料品/スーパー", "個人候補"),
    ("成城石井", "（個人候補）食料品/スーパー", "個人候補"),
    ("西友", "（個人候補）食料品/スーパー", "個人候補"),
    ("ライフ", "（個人候補）食料品/スーパー", "個人候補"),
    ("イオン", "（個人候補）食料品/スーパー", "個人候補"),
    ("まいばすけっと", "（個人候補）食料品/スーパー", "個人候補"),
    ("ストア", "（個人候補）食料品/スーパー", "個人候補"),
    ("大丸", "（個人候補）百貨店", "個人候補"),
    ("伊勢丹", "（個人候補）百貨店", "個人候補"),
    ("高島屋", "（個人候補）百貨店", "個人候補"),
    ("ファミリーマート", "（個人候補）コンビニ", "個人候補"),
    ("ローソン", "（個人候補）コンビニ", "個人候補"),
    ("セブン", "（個人候補）コンビニ", "個人候補"),
    ("ドラッグ", "（個人候補）ドラッグストア", "個人候補"),
    ("マツモトキヨシ", "（個人候補）ドラッグストア", "個人候補"),
    ("ウエルシア", "（個人候補）ドラッグストア", "個人候補"),
    ("薬", "（個人候補）ドラッグ/薬局", "個人候補"),
]

# 名義別の既定セグメント（明示ルールに当たらなかった店）
DEFAULT_SEG = {"個人": "個人候補", "法人": "要確認"}

def categorize(name, owner="法人"):
    u = unicodedata.normalize("NFKC", name).upper()
    for kw, cat, seg in RULES:
        if kw.upper() in u:
            return cat, seg
    return "（未分類）", DEFAULT_SEG.get(owner, "要確認")

# 銀行(法人口座)用ルール: (キーワード, 科目, セグメント)。flow(入金/出金)も渡して判定。
RULES_BANK_IN = [   # 入金側
    ("ポイントキコウ", "売上高・既存受託(ポイント機構)", "法人"),
    ("アイスリーエクスペリエンス", "売上高・I3エクスペリエンス", "法人"),
    ("ピカソインターナシヨナル", "売上高・ピカソ", "法人"),
    ("グロ-シング", "売上高(グローシング)", "法人"),
    ("グローシング", "売上高(グローシング)", "法人"),
    ("コウムブ", "緊急小口資金(借入金・収支外)", "除外"),
    ("オオサカチユウオウ", "(要確認)入金(大阪中央)", "要確認"),
    ("預金機", "現金入金(ATM/預金機)・要確認", "要確認"),
    ("ザ(カ", "売上高・ザ(株)", "要確認"),
    ("ザ（カ", "売上高・ザ(株)", "要確認"),
    ("サカモト", "売上高or入金(サカモト)", "要確認"),
    ("利息", "雑収入・受取利息", "法人"),
    ("イシダ", "役員借入(本人→法人・収支外)", "役員借入"),
    ("イテラ", "自社間振替(要確認・相殺候補)", "除外"),
    ("クレデイセゾン", "カード返金/CB(セゾン・収支外)", "除外"),
    ("コワー", "立替返金(コワーキング・収支外)", "除外"),
    ("ゼイムシヨ", "税務署からの還付(戻し・収支外)", "除外"),
    ("ATM", "現金入金(ATM・要確認)", "要確認"),
]
RULES_BANK_OUT = [  # 出金側
    ("口座振替 セゾン", "カード決済(セゾン法人)・カード台帳と二重計上→除外", "除外"),
    ("口座振替　セゾン", "カード決済(セゾン法人)・カード台帳と二重計上→除外", "除外"),
    ("グラントン", "03plus延滞の立替(MAサポート負担→補填回収済・収支外)", "除外"),
    ("セゾン", "カード決済(セゾン法人・明細取込済→二重計上回避)", "除外"),
    ("ニコス", "カード決済(JAL/NICOS)・個人カードを法人口座から?要確認", "要確認"),
    ("アプラス", "カード決済(アプラス)・要確認", "要確認"),
    ("クレデイセゾン", "カード決済(セゾン法人・ショッピング+キャッシング返済→二重計上回避)", "除外"),
    ("コウセイロウドウシヨウ", "法定福利費・社会保険料", "法人"),
    ("ネンキン", "法定福利費・社会保険料", "法人"),
    ("ゼイリシ", "支払報酬料・税理士", "法人"),
    ("国税", "租税公課・国税", "法人"),
    ("地方税", "租税公課・地方税", "法人"),
    ("市税", "租税公課・地方税", "法人"),
    ("県税", "租税公課・地方税", "法人"),
    ("モバイルレジ", "租税公課・公金(モバイルレジ)", "要確認"),
    ("ジエイリース", "個人住居の家賃/保証を法人が支払＝役員貸付(ジェイリース)", "役員貸付"),
    ("リンクス.エステート", "個人住居の不動産費を法人が支払＝役員貸付(リンクス)", "役員貸付"),
    ("リンクス", "個人住居の不動産費を法人が支払＝役員貸付(リンクス)", "役員貸付"),
    ("ノムラフドウサン", "個人住居の不動産費を法人が支払＝役員貸付(野村不動産)", "役員貸付"),
    ("フドウサン", "個人住居の不動産費を法人が支払＝役員貸付", "役員貸付"),
    ("トクチヨー", "(要確認)カ)トクチョー振込", "要確認"),
    ("イシダ", "役員勘定(出金=役員報酬/役員貸付・要確認)", "要確認"),
    ("イテラ", "自社間振替(要確認・相殺候補)", "除外"),
    ("オカダ", "外注費(オカダ・人名)", "法人"),
    ("ワタナベ", "外注費(ワタナベ・人名)", "法人"),
    ("サガワ", "外注費(サガワ・人名)", "法人"),
    ("フクシマ", "外注費(フクシマ・人名)", "法人"),
    ("ジエイリース", "地代家賃・要確認", "要確認"),
    ("ご返済", "借入金返済(日本政策金融公庫・法人契約・元本＝収支外)", "除外"),
    ("ネット法人東京", "法定福利費・社会保険料(Pay-easy/ネット法人東京)", "法人"),
    ("支払機", "現金引出(ATM/支払機・使途要確認)", "要確認"),
    ("預金機", "現金(ATM/預金機)・要確認", "要確認"),
    ("カード手数料", "支払手数料・カード手数料", "法人"),
    ("ナチユレ", "外注費(ナチュレ)", "法人"),
    ("タナカ", "外注費(タナカ・人名)", "法人"),
    ("フシミ", "外注費(フシミ・人名)", "法人"),
    ("トウキヨウコウムブ", "緊急小口資金(借入金・収支外)", "除外"),
    ("コウムブ", "緊急小口資金(借入金・収支外)", "除外"),
    ("振込サービス", "(要確認)振込サービス・相手先が明細に出ず要特定", "要確認"),
    ("ATM", "現金引出(ATM・使途要確認)", "要確認"),
    ("振込手数料", "支払手数料・振込手数料", "法人"),
    ("ATM手数料", "支払手数料・ATM手数料", "法人"),
    ("利息", "支払利息or受取(要確認)", "要確認"),
]

# 個人口座用ルール。明細取込済カード(セゾン/SMCC=ミツイスミトモ/NICOS)の引落は除外（二重計上防止）。
RULES_BANK_IN_INDIV = [
    ("キリカエ", "(リボ切替・二重計上のため除外)", "除外"),
    ("イテラ", "役員報酬/役員貸付の返済(法人→個人)・要確認", "要確認"),
    ("イシダ リナ", "家族間立替の精算・戻し(収支外)", "除外"),
    ("リナ", "家族間立替の精算・戻し(収支外)", "除外"),
    ("カズナリ", "家族間立替の精算・戻し(収支外)", "除外"),
    ("イシダ", "自己資金移動(本人口座間・楽天等への移動・収支外)", "除外"),
    ("ワタナ", "貸付金の回収(本人→ワタナベ30万貸付の返済・収支外)", "除外"),
    ("トウキヨウカイジヨウ", "保険金/返戻(東京海上日動・戻し・収支外)", "除外"),
    ("ＭＡサポート", "03plus遅延費用の補填回収(MAサポート負担・収支外)", "除外"),
    ("MAサポート", "03plus遅延費用の補填回収(MAサポート負担・収支外)", "除外"),
    ("ミツイスミトモ", "カード返金(SMCC・収支外)", "除外"),
    ("利息", "雑収入・受取利息", "個人候補"),
    ("ATM", "現金入金(ATM)・要確認", "要確認"),
]
RULES_BANK_OUT_INDIV = [
    ("セゾン", "カード決済(セゾン・明細取込済)→除外", "除外"),
    ("ミツイスミトモ", "カード決済(SMCC=OLIVE/Amazon・明細取込済)→除外", "除外"),
    ("ミツビシユーエフジェイニコス", "カード決済(JAL/NICOS・明細取込済)→除外", "除外"),
    ("ニコス", "カード決済(JAL/NICOS・明細取込済)→除外", "除外"),
    ("ＤＣカード", "カード決済(DC=JAL/NICOS・明細取込済)→除外", "除外"),
    ("ＤＣ　キリカエ", "(リボ切替・二重計上のため除外)", "除外"),
    ("ＤＣ", "カード決済(DC=JAL/NICOS・明細取込済)→除外", "除外"),
    ("アプラス", "個人カード返済(アプラス・銀行引落ベース計上)", "個人候補"),
    ("住信SBI", "口座間移動(自己資金・本人のSBI口座へ・収支外)", "除外"),
    ("スミシンSBI", "口座間移動(自己資金・本人のSBI口座へ・収支外)", "除外"),
    ("三井住友銀行", "口座間移動(自己資金・本人のSMBC口座へ・収支外)", "除外"),
    ("オリコ", "個人カード返済(オリコ分割/リボ・銀行引落ベース計上)", "個人候補"),
    ("オリエントコーポレ", "個人カード返済(オリコ=オリエントコーポレーション・銀行引落ベース)", "個人候補"),
    ("ペイデイ", "後払い決済(Paidy・明細未取込)・要確認", "個人候補"),
    ("ペイディ", "後払い決済(Paidy・明細未取込)・要確認", "個人候補"),
    ("ヤチンシユウノウ", "個人費用・家賃(個人住居・個人負担179,550)", "個人候補"),
    ("ジエイリース", "個人費用・家賃保証(個人口座払い・個人負担)", "個人候補"),
    ("家賃", "地代家賃・家賃(個人払い)・要確認", "要確認"),
    ("学生支援機構", "個人・奨学金返済", "個人候補"),
    ("ガクセイシエンキコウ", "個人・奨学金返済(日本学生支援機構)", "個人候補"),
    ("シヤキヨ", "緊急小口資金等の返済(社協・借入金返済・収支外)", "除外"),
    ("社協", "緊急小口資金等の返済(社協・借入金返済・収支外)", "除外"),
    ("カズナリ", "家族間立替の精算・戻し(収支外)", "除外"),
    ("パソコン振替", "口座間移動(自己資金・収支外)", "除外"),
    ("住信SBI", "口座間移動(自己資金・本人のSBI口座へ・収支外)", "除外"),
    ("三井住友銀行", "口座間移動(自己資金・本人のSMBC口座へ・収支外)", "除外"),
    ("イテラ", "法人への資金拠出(役員借入の個人側・収支外)", "除外"),
    ("ATM", "現金引出(ATM)・要確認", "要確認"),
    ("カード出金", "現金引出(ATMカード出金)・要確認", "要確認"),
    ("カード", "現金引出(ATMカード・個人)", "個人候補"),
    ("振込手数料", "支払手数料・振込手数料", "個人候補"),
    ("カード手数料", "支払手数料・カード手数料", "個人候補"),
]

def _nrm(s):
    # 半角カナの分離濁点(ﾄ ﾞ→ド)・長音=ハイフン等を吸収。NFKC→空白除去→再NFKC→長音/ハイフン除去。
    s = unicodedata.normalize("NFKC", s or "")  # ﾞ等を分解(濁点が空白+結合文字になる場合あり)
    s = re.sub(r"\s+", "", s)                    # 空白除去で結合文字が基底に隣接
    s = unicodedata.normalize("NFKC", s)         # 基底+結合→濁音1文字
    s = re.sub(r"[ー‐‑‒–—―－\-]", "", s)
    return s

def categorize_bank(name, flow, owner="法人"):
    u = _nrm(name)
    if owner == "個人":
        rules = RULES_BANK_IN_INDIV if flow == "入金" else RULES_BANK_OUT_INDIV
    else:
        rules = RULES_BANK_IN if flow == "入金" else RULES_BANK_OUT
    for kw, cat, seg in rules:
        if _nrm(kw) in u:
            return cat, seg
    return "（未分類・要確認）", "要確認"

def load_saison(fp, owner, source):
    out = []
    with open(fp, encoding="cp932") as f:
        data = list(csv.reader(f))
    pay_date = ""
    for r in data:
        if not r:
            continue
        c0 = r[0].strip()
        if c0 == "お支払日" and len(r) > 1:
            pay_date = r[1].strip(); continue
        if DATE.match(c0):
            name = r[1].strip() if len(r) > 1 else ""
            kubun = r[3].strip() if len(r) > 3 else ""
            amt_raw = r[5].strip() if len(r) > 5 else ""
            note = r[6].strip() if len(r) > 6 else ""
            try:
                amt = int(amt_raw)
            except:
                continue
            acct, seg = categorize(name, owner)
            out.append({
                "source": source, "owner": owner,
                "pay_date": pay_date, "use_date": c0,
                "name": name, "kubun": kubun, "amount": amt, "note": note,
                "account": acct, "segment": seg,
            })
    return out

def load_olive(fp, owner, source):
    """SMCC Olive: ヘッダ無し。0=利用日,1=店名,2=利用金額,5=今回請求額。
    請求月はファイル名(YYYYMM)。日付空行は小計→スキップ。金額は利用金額(col2)優先。"""
    out = []
    fn = os.path.basename(fp)
    m = re.match(r"(\d{4})(\d{2})", fn)
    pay_date = f"{m.group(1)}/{m.group(2)}/01" if m else ""
    with open(fp, encoding="cp932") as f:
        data = list(csv.reader(f))
    for r in data:
        if not r:
            continue
        c0 = r[0].strip()
        if not DATE.match(c0):
            continue
        name = r[1].strip() if len(r) > 1 else ""
        a2 = r[2].strip() if len(r) > 2 else ""
        a5 = r[5].strip() if len(r) > 5 else ""
        kubun = (r[3].strip() if len(r) > 3 else "")
        note = r[6].strip() if len(r) > 6 else ""
        raw = a2 if a2 else a5
        try:
            amt = int(raw.replace(",", ""))
        except:
            continue
        acct, seg = categorize(name, owner)
        out.append({
            "source": source, "owner": owner,
            "pay_date": pay_date, "use_date": c0,
            "name": name, "kubun": kubun, "amount": amt, "note": note,
            "account": acct, "segment": seg,
        })
    return out

JPDATE = re.compile(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日")
def parse_jpdate(s):
    m = JPDATE.search(s or "")
    if not m:
        return ""
    return f"{int(m.group(1)):04d}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"

def load_nicos(fp, owner, source):
    """UFJ NICOS(JALカード): ヘッダ有。0確定情報,1お支払日,2店名,3利用日,4回数,6金額(円)。
    日付=YYYY年M月D日。金額カンマ・△/▲はマイナス。"""
    out = []
    with open(fp, encoding="cp932") as f:
        data = list(csv.reader(f))
    for r in data:
        if not r or len(r) < 7:
            continue
        if r[0].strip() not in ("確定", "未確定", "確定情報") or r[0].strip() == "確定情報":
            # ヘッダ行(確定情報)・名前行はスキップ。確定/未確定のみ採用
            if r[0].strip() not in ("確定", "未確定"):
                continue
        use_date = parse_jpdate(r[3])
        pay_date = parse_jpdate(r[1])
        if not use_date:
            continue
        name = r[2].strip()
        kubun = r[4].strip() if len(r) > 4 else ""
        raw = r[6].strip().replace(",", "").replace("△", "-").replace("▲", "-")
        try:
            amt = int(raw)
        except:
            continue
        acct, seg = categorize(name, owner)
        out.append({
            "source": source, "owner": owner,
            "pay_date": pay_date, "use_date": use_date,
            "name": name, "kubun": kubun, "amount": amt, "note": (r[7].strip() if len(r) > 7 else ""),
            "account": acct, "segment": seg,
        })
    return out

def load_bank_sbi(fp, owner, source):
    """住信SBI(法人): 0日付,1内容,2出金,3入金,4残高,5メモ。出金/入金を別flowで。"""
    out = []
    with open(fp, encoding="cp932") as f:
        data = list(csv.reader(f))
    for r in data:
        if not r or len(r) < 5:
            continue
        d = r[0].strip()
        if not DATE.match(d):
            continue
        name = r[1].strip()
        de = r[2].replace(",", "").strip()  # 出金
        cr = r[3].replace(",", "").strip()  # 入金
        for raw, flow in ((de, "出金"), (cr, "入金")):
            if not raw:
                continue
            try:
                amt = int(raw)
            except:
                continue
            acct, seg = categorize_bank(name, flow, owner)
            out.append({
                "source": source, "owner": owner,
                "pay_date": d, "use_date": d,
                "name": name, "kubun": "", "amount": amt, "note": flow,
                "account": acct, "segment": seg, "type": "bank", "flow": flow,
            })
    return out

def _yen(s):
    s = (s or "").replace("\\", "").replace("￥", "").replace(",", "").strip()
    try:
        return int(s)
    except:
        return None

# SMBC法人の「振込・振替サービスご利用明細」＝Web通帳で相手先空欄の振込の受取人名を補完するためのルックアップ
SMBC_TRANSFER_GLOB = r"G:\マイドライブ\00_myDrive\銀行入出金明細\SMBC（法人）\振込・振替サービスご利用明細*.csv"
def _load_smbc_transfer_lut():
    lut = {}
    for fp in glob.glob(SMBC_TRANSFER_GLOB):
        with open(fp, encoding="utf-8-sig") as f:
            data = list(csv.reader(f))
        for r in data:
            if len(r) < 20 or r[0] == "対象年月":
                continue
            m = re.match(r"(\d{4})(\d{2})(\d{2})", r[13].strip())  # 取扱日年月日
            payee = unicodedata.normalize("NFKC", r[18]).strip()    # 受取人名
            val = _yen(r[19])                                       # 金額
            if m and val is not None and payee:
                lut[(f"{m.group(1)}/{m.group(2)}/{m.group(3)}", val)] = payee
    return lut
SMBC_TRANSFER_LUT = _load_smbc_transfer_lut()

def load_bank_smbc(fp, owner, source):
    """SMBC法人 Web通帳: 多列。10=対象年,16=月,17=日,18=ご入金,19=ご出金,21=摘要。
    「振込サービス」で相手先空欄の出金は、振込明細(別CSV)の受取人名を補完して分類。"""
    out = []
    with open(fp, encoding="utf-8-sig") as f:
        data = list(csv.reader(f))
    for r in data:
        if len(r) < 22 or r[0] == "顧客名１":
            continue
        yr = r[10].strip() or r[13].strip()
        mo = r[16].strip(); da = r[17].strip()
        tekiyo = unicodedata.normalize("NFKC", r[21]).strip()
        if "繰越" in tekiyo:
            continue
        cin = _yen(r[18]); cout = _yen(r[19])
        if not (mo and da) or (cin is None and cout is None):
            continue
        try:
            d = f"{int(yr):04d}/{int(mo):02d}/{int(da):02d}"
        except:
            continue
        for amt, flow in ((cin, "入金"), (cout, "出金")):
            if amt is None:
                continue
            name = tekiyo
            # 振込サービスは受取人名を別明細から補完
            if flow == "出金" and "振込" in tekiyo:
                payee = SMBC_TRANSFER_LUT.get((d, amt))
                if payee:
                    name = f"振込 {payee}"
            acct, seg = categorize_bank(name, flow, owner)
            out.append({
                "source": source, "owner": owner,
                "pay_date": d, "use_date": d,
                "name": name, "kubun": "", "amount": amt, "note": flow,
                "account": acct, "segment": seg, "type": "bank", "flow": flow,
            })
    return out

def load_bank_smbc_indiv(fp, owner, source):
    """SMBC個人(通帳明細): 7列 0年月日,1お引出し,2お預入れ,3お取扱内容,4残高。
    日付=YYYY/M/D(ゼロ埋め無)。半角カナはNFKCで吸収。"""
    out = []
    with open(fp, encoding="cp932") as f:
        data = list(csv.reader(f))
    for r in data:
        if not r or len(r) < 5 or r[0].strip() == "年月日":
            continue
        m = re.match(r"(\d{4})/(\d{1,2})/(\d{1,2})", r[0].strip())
        if not m:
            continue
        d = f"{int(m.group(1)):04d}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"
        name = unicodedata.normalize("NFKC", r[3]).strip()
        de = _yen(r[1]); cr = _yen(r[2])
        for amt, flow in ((de, "出金"), (cr, "入金")):
            if amt is None:
                continue
            acct, seg = categorize_bank(name, flow, owner)
            out.append({
                "source": source, "owner": owner,
                "pay_date": d, "use_date": d,
                "name": name, "kubun": "", "amount": amt, "note": flow,
                "account": acct, "segment": seg, "type": "bank", "flow": flow,
            })
    return out

def load_bank_rakuten(fp, owner, source):
    """楽天銀行: 0取引日(YYYYMMDD),1入出金(円・符号付),2残高,3内容。+入金/-出金。"""
    out = []
    with open(fp, encoding="cp932") as f:
        data = list(csv.reader(f))
    for r in data:
        if not r or len(r) < 4 or r[0].strip() == "取引日":
            continue
        m = re.match(r"(\d{4})(\d{2})(\d{2})", r[0].strip())
        if not m:
            continue
        d = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
        val = _yen(r[1])
        if val is None:
            continue
        flow = "入金" if val >= 0 else "出金"
        name = unicodedata.normalize("NFKC", r[3]).strip()
        acct, seg = categorize_bank(name, flow, owner)
        out.append({
            "source": source, "owner": owner,
            "pay_date": d, "use_date": d,
            "name": name, "kubun": "", "amount": abs(val), "note": flow,
            "account": acct, "segment": seg, "type": "bank", "flow": flow,
        })
    return out

LOADERS = {"saison": load_saison, "olive": load_olive, "nicos": load_nicos,
           "bank_sbi": load_bank_sbi, "bank_smbc": load_bank_smbc,
           "bank_smbc_indiv": load_bank_smbc_indiv, "bank_rakuten": load_bank_rakuten}

# ============================================================
# 確定判定の適用層（本人の判断を反映。自動推定RULESとは分離）
# 追記するたびにここへ。各決定は「いつ・何を・なぜ」を残す。
# ------------------------------------------------------------
# 決定1（2026-06-29 本人）：法人→個人 に「30万程度」動いた振込は役員報酬。
#   実額は毎月 300,000／350,000。バンド[250,000〜360,000]を役員報酬とみなす。
#   法人側(出金・相手=石田/イシダ)=役員報酬(法人経費)、個人側(入金・相手=ITERRA/イテラ)=役員報酬受取(個人収入)。
#   ※同一資金移動の表裏。法人=費用/個人=収入で別エンティティ計上のため二重計上ではない。
YAKUIN_LO, YAKUIN_HI = 250000, 360000
def _d2i(s):
    y, m, dd = s.split("/"); return int(y) * 372 + int(m) * 31 + int(dd)
def _is_atm(nm):
    return any(k in nm for k in ["ATM", "支払機", "預金機", "カード出金", "カ-ド出金", "カ−ド出金"])

def apply_decisions(rows):
    # 決定1：法人→個人 30万程度(25〜36万)＝役員報酬（法人=費用／個人=収入）
    for r in rows:
        if r["type"] != "bank":
            continue
        nm = unicodedata.normalize("NFKC", r["name"]); a = r["amount"]
        if YAKUIN_LO <= a <= YAKUIN_HI:
            if r["owner"] == "法人" and r["flow"] == "出金" and "イシダ" in nm:
                r["account"] = "役員報酬（定期・法人→個人）"; r["segment"] = "役員報酬"
            elif r["owner"] == "個人" and r["flow"] == "入金" and "イテラ" in nm:
                r["account"] = "役員報酬 受取（個人収入）"; r["segment"] = "役員報酬受取"
    # 決定5：ATM/支払機/カード出金は、別口座への同額±5日入金とマッチしなければ単純な支出。
    #        マッチすれば口座間移動（法人→個人=役員貸付／個人→法人=役員借入／同名義=収支外）。
    credits = [r for r in rows if r["type"] == "bank" and r["flow"] == "入金"]
    used = set()
    for de in sorted([r for r in rows if r["type"] == "bank" and r["flow"] == "出金"
                      and _is_atm(unicodedata.normalize("NFKC", r["name"]))], key=lambda r: -r["amount"]):
        a = de["amount"]; matched = None
        for i, cr in enumerate(credits):
            if i in used or cr["source"] == de["source"] or cr["amount"] != a:
                continue
            if abs(_d2i(cr["use_date"]) - _d2i(de["use_date"])) > 5:
                continue
            matched = i; break
        if matched is not None:
            used.add(matched); cr = credits[matched]
            if de["owner"] != cr["owner"]:
                if de["owner"] == "法人":
                    de["segment"] = "役員貸付"; de["account"] = f"現金移動(法人→{cr['owner']}・ATM)＝役員貸付"
                else:
                    de["segment"] = "役員借入"; de["account"] = "現金移動(個人→法人・ATM)＝役員借入"
            else:
                de["segment"] = "除外"; de["account"] = "自己口座間 現金移動(ATM)・収支外"
        else:
            if de["owner"] == "法人":
                de["segment"] = "法人"; de["account"] = "現金支出(ATM引出・使途/雑費として計上)"
            else:
                de["segment"] = "個人候補"; de["account"] = "現金支出(ATM引出・個人)"
    # 決定7：入金側のうち、ATM/カード/預金機での現金入金＝手許現金の預け入れ（収支外）、
    #        パソコン振替＝口座間移動（収支外）。本人申告：C＝手許現金。
    for r in rows:
        if r["type"] != "bank" or r["flow"] != "入金" or r["segment"] != "要確認":
            continue
        nm = unicodedata.normalize("NFKC", r["name"])
        if any(k in nm for k in ["ATM", "支払機", "預金機"]) or re.match(r"^カ.?ド", nm):
            r["segment"] = "除外"; r["account"] = "手許現金の預け入れ(ATM/カード入金・収支外)"
        elif "パソコン振替" in nm or "パソコン振込" in nm:
            r["segment"] = "除外"; r["account"] = "口座間振替(収支外)"
    # 決定8（2026-06-29）：カード支出のグループ別原則。Amazonは明細待ちで保留。
    #   旅行宿泊/飲食/交通系IC=法人、未分類/YouTube=個人費用、（個人候補）生活費物販はそのまま個人。
    for r in rows:
        if r["type"] != "card" or r["segment"] not in ("要確認", "個人候補"):
            continue
        a = r["account"]
        if "Amazon" in a:
            continue  # 明細待ちで保留
        if any(k in a for k in ["宿泊", "旅行", "航空", "空港", "レンタカー", "海外旅行保険", "交通系IC", "PASMO", "Suica"]):
            r["segment"] = "法人"  # 旅費交通費（出張）
        elif "飲食" in a:
            r["segment"] = "法人"  # 会議費/接待交際費
        elif "未分類" in a:
            r["segment"] = "個人候補"  # 原則 生活費（個人費用）
        elif "YouTube" in a:
            r["segment"] = "個人候補"  # 私的サブスク
    # 決定6：法人→個人 で用途不明な振込（役員報酬30万に該当せず残ったもの）は役員貸付。
    #        法人側(出金・相手=石田/イシダ)=役員貸付、個人側(入金・相手=ITERRA/イテラ)=役員貸付受取。
    for r in rows:
        if r["type"] != "bank" or r["segment"] != "要確認":
            continue
        nm = unicodedata.normalize("NFKC", r["name"])
        if r["owner"] == "法人" and r["flow"] == "出金" and "イシダ" in nm:
            r["segment"] = "役員貸付"; r["account"] = "役員貸付（法人→個人・用途不明）"
        elif r["owner"] == "個人" and r["flow"] == "入金" and "イテラ" in nm:
            r["segment"] = "役員貸付受取"; r["account"] = "役員貸付 受取（法人→個人・用途不明）"
    return rows

def main():
    rows = []
    for s in SOURCES:
        new = []
        for fp in sorted(glob.glob(s["glob"])):
            new += LOADERS[s["loader"]](fp, s["owner"], s["name"])
        t = s.get("type", "card")
        for r in new:
            r.setdefault("type", t)
            # カードは金額>0=出金/支出、<0=入金/返金。銀行はloaderでflow設定済み。
            if "flow" not in r:
                r["flow"] = "入金" if r["amount"] < 0 else "出金"
        rows += new
    apply_decisions(rows)
    rows.sort(key=lambda r: (r["use_date"], r["source"]))

    # 明細台帳
    cols = ["source","owner","type","flow","pay_date","use_date","name","kubun","amount","note","account","segment"]
    with open(os.path.join(BASE, "ledger_master.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow(r)

    # 要確認リスト（店名単位で重複排除：要確認＋個人候補）
    from collections import defaultdict
    rev = defaultdict(lambda: [0,0,"","",""])  # total,count,account,segment,type
    for r in rows:
        if r["segment"] in ("要確認","個人候補"):
            a = rev[r["name"]]; a[0]+=r["amount"]; a[1]+=1; a[2]=r["account"]; a[3]=r["segment"]; a[4]=r["type"]
    with open(os.path.join(BASE, "review_needed.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["店名/内容","合計金額","件数","推定科目","仮セグメント","種別","→本人判定(法人/個人/不課税)","正しい科目(任意)"])
        for name,(tot,cnt,acct,seg,tp) in sorted(rev.items(), key=lambda x:-x[1][0]):
            w.writerow([name,tot,cnt,acct,seg,tp,"",""])

    print("取引行:", len(rows), " 要確認店名:", len(rev))
    return rows

if __name__ == "__main__":
    main()
