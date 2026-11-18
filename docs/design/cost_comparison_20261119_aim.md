# 自作ロガーと同じ機能をAiMで組むといくらか（NCロードスター 2005 MT・日本・税込）

調べた日：2026-11-19（以下の「確認日」はすべてこの日）

## 0. 結論（先に）

| 構成 | 中身 | 合計（税込） | 5機能のうち |
|---|---|---|---|
| **A. 全機能にいちばん近い** | MXS 1.3（5"ダッシュロガー・GPS・IMU・アナログ8ch）＋油圧・油温センサー＋SmartyCam 4 Corsa | **AiMだけで約91.8万円**（取付部材を足して約93.5万円）。LTEテレメトリーを他社品で足すと**約100万円〜** | 1〜4は可。5はAiMに製品なし |
| **B. 1〜3の最低限** | MXq（モノクロLCDダッシュロガー・GPS・IMU内蔵）＋ACC3（アナログ増設）＋油圧・油温センサー＋SmartyCam 4 Corsa | **約62.5万円**（取付部材込みで約64万円） | 1〜4は可（表示は白黒LCD）。5は不可 |
| 参考：油温・油圧をあきらめる | Solo 2 DL＋SmartyCam 4 Corsa | 約48.5万円 | 1は油温・油圧なし、3は小さな表示だけ |
| 参考：映像なし | Bから SmartyCam を抜く | 約31.0万円 | 2が無い |

- **「AiMで今の構成にすると50万円は軽くかかる」は正しい。** 油温・油圧まで入れて1〜3をそろえる最低限（B）で約63万円、
  5インチカラー画面にするAなら約92万円。50万円を切るのは、油温・油圧と大きな画面をあきらめた参考構成だけ。
- 費用のおよそ半分は **映像（SmartyCam 4 Corsa 315,700円）**。日本の正規販売店では旧型の SmartyCam 3 Sport（以前は160,600円）が一覧から消え、今は SmartyCam 4 Corsa だけになっている。
- **5. ピットへのLTEテレメトリーは、AiMの製品にはない**（AiM本社の2026年11月版の価格表全91ページに、テレメトリー・LTE・クラウドの製品が1つも載っていない）。
  やるなら他社品（Autosport Labs の PodiumConnect/Micro 等）をAiMのCANにつなぐ。
- 4. 解析ソフト Race Studio 3 は無料（価格表の各製品に「freely downloadable」と書いてある）。

## 1. 価格の出どころと換算

- **日本円の価格**：Aimダイレクト（有限会社ベア、bear-racing.co.jp の運営。AiM製品の国内販売サイト）https://store.aimsports.jp/ の商品ページ。各ページに「税込」と表示されている。
  - 「正規輸入代理店」とはサイトに書かれていない（確かめられなかった）。ただ、国内でAiMの製品をほぼ全部扱い、価格がAiM本社の欧州定価と一定の比率で並んでいるので、実質的な国内定価とみなした。
- **AiM本社の価格表**：AiM car/bike price list Ver. 26t（2026年11月版、ユーロ・付加価値税抜）https://www.aim-sportline.com/download/price_lists/aim_price_list_car-bike.pdf
- **国内価格と欧州定価の関係**（確かめた分）：国内税込 ≒ 欧州税抜定価 × 約205円 × 1.1。
  例：MXS 1.3 は €2,450 → 551,100円（÷1.1÷2,450 = 204.5）。SmartyCam 4 Corsa は €1,400 → 315,700円（205.0）。Solo 2 DL は €750 → 169,400円（205.3）。
  → 国内サイトに出ていない品は、この比率で **推定** し「推定」と書いた。
- **米ドル品の換算**：1ドル＝155円と **仮定**（今日の為替は確かめていない）。個人輸入だと別に消費税と送料がかかる。

## 2. 構成A：全機能にいちばん近い（MXS 1.3 ダッシュロガー）

| 品目 | 受け持つ機能 | 価格（税込） | 出どころ | 確度 |
|---|---|---|---|---|
| MXS 1.3（カラーダッシュロガー、5" TFT 800×480、GPS付属（1.3m/4m）、慣性センサー（加速度3軸＋ジャイロ3軸）、アナログ/デジタル入力8ch（各最大500Hz）、CAN 3系統・2,000種以上のECUに対応、Wi-Fi） | 1（車両CAN・GNSS・IMU・記録）、3（画面：ラップ・差・温度・回転・警告） | 551,100円 | https://store.aimsports.jp/products/detail/29 ／ 仕様と同梱品は本社価格表 p.3（同梱：GPS・37ピン標準ハーネス・USB） | 高（価格）／中（国内でもハーネスが付くか：国内ページには「37pinタイプは本体セットに付属」とだけある） |
| 油圧センサー（日本製）0-10bar、R1/8、エコノシールコネクター | 1（油圧） | 16,500〜31,680円（変換ケーブル有無。合計には上限の31,680円を使用） | https://store.aimsports.jp/products/detail/86 | 高（価格）／中（出力の仕様がページにない） |
| 温度センサー Pt100（抵抗内蔵型、M10 / NPT1/8 / M5） | 1（油温） | 19,140円 | https://store.aimsports.jp/products/detail/18 | 高（価格）／中（油温に使えるかは取付ネジ次第。ページは「水温/液温」として売っている） |
| SmartyCam 4 Corsa（85°、1080p60、AiMのロガーやECUからCANでデータを受けて映像に焼き込む、CANケーブル2m/4m付） | 2（計器の焼き込み録画） | 315,700円 | https://store.aimsports.jp/products/detail/1087 ／ 本社価格表 p.32（€1,400） | 高 |
| Race Studio 3 | 4（PC解析、映像との同期） | 0円 | 本社価格表（各製品「RaceStudio 3 software freely downloadable」） | 高 |
| **AiMの分の小計** | | **917,620円** | | |
| 油温・油圧の取り出し（オイルブロック等、AiM以外） | 1 | 1〜2万円（推定） | 調べていない | 低 |
| OBD2プラグへの配線（MXS 1.3の37ピンハーネスのCAN線をOBD2の6・14番へ。AiMにはMXS 1.3用のOBDハーネスが価格表にない） | 1 | 数千円（推定・自作） | 本社価格表 p.3 ／ NCの接続資料（下記） | 中 |
| **AiM以外の部材を足した計** | | **約93.5万円** | | |
| （5. テレメトリー）PodiumConnect/Micro（Autosport Labs製。AiMのCAN拡張ハブに5ピンBinderでつなぐ。通信は手元のスマホ等のWi-Fiホットスポット経由） | 5（ピットへのライブ） | $349.95 ≒ 5.4万円（換算）＋AiM接続ケーブル（別売・価格未確認）＋消費税・送料 → **7〜8万円程度（推定）** | https://www.autosportlabs.com/product/podiumconnect-micro-live-motorsports-telemetry-stream-data-from-your-racecar-with-aim-motec-ecumaster-vbox-lowrance/ | 中（本体価格）／低（日本での入手・総額） |
| （5.）Podium の利用料 | 5 | 無料で始められる。有料プランの値段はページに出ていない | https://podium.live/ | 低 |
| **テレメトリーまで含めた概算** | | **約100万円〜** | | |

### Aの別案：Strada（表示専用）＋Stradaロガーでも安くならない

| 品目 | 価格（税込） | 出どころ |
|---|---|---|
| MXS 1.3 Strada（表示専用。CANハーネスかOBDハーネス（CAN＋K）付きを選べる） | 270,600円（品切れ中） | https://store.aimsports.jp/products/detail/39 ／ 本社価格表 p.9（€1,200） |
| Stradaロガー（Strada に記録の機能を足す。SDに記録。取り寄せで1〜2か月） | 194,700円 | https://store.aimsports.jp/products/detail/45 ／ 本社価格表 p.86（€863） |
| GPSモジュール（GPS09c、25Hz） | 72,050円 | https://store.aimsports.jp/products/detail/51 ／ 本社価格表 p.71（€320） |
| 23ピンハーネス（アナログ入力用。23ピンコネクターキットだけなら10,120円） | 42,790円 | https://store.aimsports.jp/products/detail/44 |
| 計 | **580,140円**（MXS 1.3 の 551,100円より高い） | |

- Strada にIMUが入るかは確かめられなかった（AiMの説明では慣性センサーは「ダッシュロガー版だけ」）。**Strada の組み合わせは選ぶ理由がない。**
- 別の店（Yahoo!ショッピングのHSモータースポーツ）では MXS 1.3 Strada を 257,000円（税込か不明。以前の検索結果には229,900円という表示もあった）で出している。店によって1〜2割の差はありうる。https://store.shopping.yahoo.co.jp/hs-motorsport/mxsst.html （確度：低）

## 3. 構成B：1〜3の最低限（MXq＋ACC3）

| 品目 | 受け持つ機能 | 価格（税込） | 出どころ | 確度 |
|---|---|---|---|---|
| MXq（白黒LCDダッシュロガー。GPS内蔵、慣性センサー内蔵、ECU接続はCAN・K-Line・RS232、アナログ入力1ch（0-5Vか熱電対）、Wi-Fi、4GB。OBD2用のCAN/K-Line電源ケーブル付きのキットあり） | 1、3（白黒の表示） | 191,400円（品切れ中） | https://store.aimsports.jp/products/detail/1083 ／ 本社価格表 p.1（€850） | 高（価格）／中（内蔵GPSの更新レート、画面に何を出せるかは未確認） |
| ACC3（アナログ→CAN変換、4ch・各1kHz、0-5V／測温抵抗／熱電対） | 1（油温・油圧を入れる入力を増やす） | 67,540円 | https://store.aimsports.jp/products/list ／ 本社価格表 p.57（€300） | 高（価格）／中（MXqにつなげるか：国内ページで関連商品に並ぶだけ） |
| 油圧センサー（日本製）0-10bar | 1 | 31,680円（上限） | https://store.aimsports.jp/products/detail/86 | 高 |
| 温度センサー Pt100 | 1 | 19,140円 | https://store.aimsports.jp/products/detail/18 | 高 |
| SmartyCam 4 Corsa | 2 | 315,700円 | https://store.aimsports.jp/products/detail/1087 | 高 |
| Race Studio 3 | 4 | 0円 | 本社価格表 | 高 |
| **計** | | **625,460円**（取付部材を足して約64万円） | | |

- 参考：ケータハムカップ・ジャパンの部品パック（2026-10発表）に「MXq＋SmartyCam 4 Corsa 85° 4m＋カメラ接続ケーブル＋OBD接続電源ケーブル」が **514,250円（税込）** で入っている。上の積み上げ（191,400＋315,700＝507,100円＋ケーブル類）と合う。https://www.autoprestige.co.jp/170partspack （確度：高）
- 別案 MXm（白黒LCD、GPS内蔵、アナログ4ch）は 275,000円。ACC3が要らないぶん同じくらいの値段（約64万円）になるが、価格表の仕様に慣性センサーが無い。https://store.aimsports.jp/products/list?pageno=2 ／ 本社価格表 p.2（€1,220）
- さらに安い参考：**Solo 2 DL（169,400円）＋SmartyCam 4 Corsa ＝ 485,100円**。Solo 2 DL はGPS・慣性センサー・ECU接続（CAN/K-Line）付きだが、価格表にアナログ入力が無く、油温・油圧が入らない（確度：中）。画面も小さい白黒。欧州ではこの2つの組み合わせが「Track-Day Kit」€2,275 として売られている（本社価格表 p.33）。https://store.aimsports.jp/products/list
- 映像を抜くと B は約31万円。費用の半分は映像。

## 4. NCロードスターの車両CANへのつなぎ方（AiMの対応）

- AiMは **「Mazda MX5-NC（2005年以降）」のプロトコルを持っている**。OBD2の6番＝CAN High、14番＝CAN Low。Race Studio で ECU を「Mazda」「MX5」に設定する。
  出どころ：AiM「Mazda MX5-NC Release 1.04」https://www.aim-sportline.com/download/ecu/stock/mazda/MazdaMX5-NC_104_eng.pdf （確度：高）
- 取れるチャンネル（資料のとおり）：回転数、4輪の車輪速、車速、ブレーキ圧、ブレーキスイッチ、ABS警告、アクセルペダル位置（2本）、クラッチスイッチ、水温、吸気温、操舵角、エンジン負荷、空燃比、点火時期、触媒温度、燃料残量、油量スイッチ。
  - **スロットル開度（TPS）は一覧に無い**（ペダル位置はある）。油温・油圧も無いので、センサーは別に要る。
  - 資料には「すべてのチャンネルが全年式で確かめられているわけではない」とある。ECUを純正から替えた車では、流れているCANが資料と違うことがある。

## 5. AiMでは賄えない・確かめきれなかったこと

1. **5. LTEテレメトリー**：AiMの製品は無い（2026年11月版の本社価格表に無い。国内サイトにも無い）。
   - ドイツのAiM販売店（memotec）のサイトに「xTCU Team Telemetry Module」（4G/LTE・クラウド表示、税込€422.45）が載っているが、作っている会社の名前が無く、AiM本社の価格表にも無い。日本では手に入らない。https://www.aim-store.com/en/Others/xTCU/xTCU-Team-Telemetry-Module （確度：低）
   - 他社品の PodiumConnect/Micro（$349.95）を使えばAiMのCANから Podium へ送れる。ピットでの地図・数値・ラップ表は Podium 側の機能になる。
2. **GNSS 10〜25Hz**：外付けの GPS09c は25Hz（本社価格表 p.72）。MXS 1.3 に付く GPS と MXq・Solo 2 DL の内蔵 GPS の更新レートは確かめていない。
3. **約100Hz の記録**：アナログは各最大500Hz（MX 1.3）、ACC3は1kHz、慣性センサーは100Hz（MX シリーズの説明）。ECUのチャンネルはECUが流す周期による。
4. **取付の工賃**は含めていない（店に頼めば別途）。

## 6. 主な不確かさ

- 国内価格はAimダイレクトの表示だけ。他店では値引きがあるかもしれない（MXS 1.3 Strada で1〜2割の差の例）。品切れ・取り寄せの品が多い（MXq・MXS Strada は品切れ、Stradaロガーは1〜2か月）。
- MXS 1.3 の国内価格にハーネスが含まれるか（本社では37ピン標準ハーネスが同梱）。含まれなければ 85,470〜101,200円 が足される（https://store.aimsports.jp/products/detail/32 ）。→ Aは最大で約100万円（テレメトリー抜き）。
- MXq に ACC3 をつなげるか、MXq の白黒画面に油温・油圧やラップの差を並べられるか。
- 油圧・油温センサーをNCのどこから取るか（オイルブロック等の値段）。
- テレメトリーの総額（AiM接続ケーブル・Podium の有料プラン・SIMの料金）。為替は1ドル155円と仮定。
- 旧型 SmartyCam 3 Sport は国内の一覧から消えた（以前は160,600円。在庫品や海外品を探せば A・B とも約15万円下がる）。
