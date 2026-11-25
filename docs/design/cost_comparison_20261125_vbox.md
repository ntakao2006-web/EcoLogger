# 自作ロガーと同じ機能をVBOXで組むといくらか・構成はどう違うか（2026-11-25）

> 2026-11-19のAiMとの比べ（`docs/design/cost_comparison_20261119.md`）に、Racelogic社のVBOX（モータースポーツ向けの「VBOX Motorsport」）を足したもの（ユーザー依頼）。
> 自作の値段・部品は`docs/design/cost_comparison_20261119_ecologger.md`、AiMは`docs/design/cost_comparison_20261119_aim.md`が正。ここはVBOXの見積もりと、3つの構成の違いだけを書く。
> 調べた日：2026-11-25。VBOXの値段は英国の公式ストアの定価で、**日本の値段は見つからなかった**（代理店は見積もり制）。日本円はすべて**推定**。

## 1. 結論

| | 1台分（税込） | 5つの機能のうち |
|---|---:|---|
| **自作 Ver.2（SUGOの形）** | **約8.8万円**（幅7.6万〜10.5万円） | 1〜5すべて |
| VBOX B：1〜3の最低限（Video HD1＋OLED表示器＋入力モジュール＋油温・油圧センサー） | **約45万円**（推定） | 1〜4。ただしIMUが無く、画面に回転・温度・警告が出ない。5は無い |
| VBOX A：いちばん近い構成（Video HD2 Track Package＋CAN Gateway＋入力モジュール＋センサー＋HDMIの小型モニター） | **約77万円**（推定） | 1〜4（IMUは無い）。5は無い |
| VBOX A＋他社のLTE（PodiumConnect/Micro） | 約85万円〜 | 1〜5（IMUは無い） |
| （再掲）AiM B：MXq＋ACC3＋センサー＋SmartyCam 4 Corsa | 約63万円 | 1〜4（画面は白黒）。5は無い |
| （再掲）AiM A：MXS 1.3＋センサー＋SmartyCam 4 Corsa | 約93万円 | 1〜4。5は無い |

- **VBOXは同じくらいの構成でAiMより2割ほど安い**（B：約45万円 対 約63万円、A：約77万円 対 約93万円）。それでも**自作の約5〜9倍**で、方針書の「既製品と桁が違うほど安い」は、VBOXと比べても保たれている
- VBOXは**焼き込み映像が本体の中心**（カメラ一体のロガー）。AiMのように「ロガー＋別売のカメラ（31.6万円）」に分かれていないぶん安い
- そのかわり、**現行のVBOXにはIMU（ジャイロ）が無い**。Gは測位の速度から計算した値だけ。**車載画面（OLED）はラップ・ベストとの差・速度・Gだけ**で、回転・油温・油圧・警告を出せない
- **ピットへのLTEのライブ表示は、VBOXにも無い**（AiMと同じ）。あるのは焼き込み映像をそのまま配信する機器（LiveU Solo、£990）で、映像なので通信量が桁違いに多い
- 解析ソフト（Circuit Tools 3）は無料。NCロードスターの車両CANの読み方も、Racelogicの車種別データベースにある（スロットル開度・油温・油圧は無い）

## 2. 構成の違い（自作・VBOX・AiM）

| | 自作 Ver.2 | VBOX（HD1／HD2） | AiM（MXq・MXS 1.3＋SmartyCam） |
|---|---|---|---|
| 形 | 本体（UNO Q＋シールド）1つに、記録・焼き込み録画・画面・LTEをまとめ、油温・油圧はPICのハブから外部CANで受ける | **カメラ付きの映像ロガー**が中心。表示器・入力モジュールをCANで足す | **ダッシュロガー**（画面と記録が一体）が中心。カメラ（SmartyCam）は別の箱で、CANで値をもらって焼き込む |
| GNSS | 10Hz（u-blox MAX-M10M） | 25Hz（どの機種も） | 外付けGPS09cは25Hz。内蔵の更新レートは未確認 |
| IMU | あり（BNO055：前後左右のG・角速度・姿勢） | **無し**（Gは測位から計算、最大4g） | あり（加速度3軸＋ジャイロ3軸、MXシリーズ） |
| 車両CAN | 500kbps、NCEC用に自分で読み解いた（スロットル開度も取れる） | 車種別データベースにMX-5 NCあり。CANはHD1が2系統、HD2が1端子（足すにはCAN Gateway £495） | 車種別プロトコルにMX5-NCあり（スロットル開度は無い）。CAN 3系統（MXS 1.3） |
| 記録の速さ | 100Hz、本体のeMMCとmicroSDの2か所 | 未確認（SDに記録） | アナログ各最大500Hz・慣性100Hz |
| 油温・油圧 | もとから車にあるDefiのセンサーから分けて取る | 入力モジュール（アナログ4ch、£190〜210）＋センサー | 本体のアナログ入力（MXS 1.3）かACC3＋センサー |
| 焼き込み映像 | カメラ1台、1080p30、計器・コース図・Gを焼き込み、10分ごとに区切る | HD1は一体カメラ1台、HD2は外付け2台まで。1080p30。値が上下限を外れると表示を切り替える警告も焼き込める | SmartyCam 4 Corsa、1080p60 |
| 車載画面 | 7インチのHDMIモニター（HD7H）にDASH：ベスト比・回転・油温・油圧の警告 | OLED表示器：ラップ・ベストとの差・速度・G。回転・温度・警告は出ない（HDMI出力をモニターに映す手はあるが未確認） | MXS 1.3は5インチのカラー、MXqは白黒。回転・温度・警告を出せる |
| 解析 | 自前の解析アプリ（SP-10、作りかけ）。`.vbo`への書き出しでCircuit Tools 3でも比べられる（衛星数を31までに抑える） | Circuit Tools 3（無料、Windowsだけ）。周の重ね合わせ・タイム差・動画2本並べ | Race Studio 3（無料） |
| ピットへのライブ | LTE（SIM7070G）で自宅のサーバー・Podiumへ値を送る | 無し。他社のPodiumConnect/Microを足す | 無し。同上 |
| 完成品としての確かさ | 自分で作って確かめている途中 | 取付が簡単、完成品 | 取付が簡単、完成品 |

- **VBOXの強み**：焼き込み映像の作りが本体の中心で、映像まわりの機能（2台のカメラ、警告の焼き込み、動画2本の比べ）がいちばん充実している。測位は25Hzで自作の10Hzより細かい
- **VBOXの弱み（自作と比べて）**：IMUが無い、運転席の画面に回転・温度・警告を出せない、ライブ表示が無い
- 自作の測位10Hzは、VBOX・AiMの25Hzより粗い。ここは自作が劣る所として残る（周の比べの細かさに効く。いまの使い方で困っているという記録は無い）

## 3. 値段の出し方

- **英国の定価**：公式ストア https://www.vboxmotorsport.store/ の値段（2026-11-25に確認）。ストアの説明に「Prices stated include VAT at the applicable UK rate」とあり、**英国のVAT 20%込み**（https://www.vboxmotorsport.store/index.php?route=information/information&information_id=9 ）。ストアは米ドルでも表示でき、ポンドの約1.5倍の値（HD1 $2,055＝£1,370、HD2 Track Package $3,895＝£2,595）
- **日本円の推定**：£（VAT込み）÷1.2×200円（**1ポンド＝200円と仮定**、今日の為替は確かめていない）×1.1。£1あたり約183円。送料・通関・代理店の上乗せは入れていない
  - AiMは「国内税込 ≒ 欧州の税抜定価×約205円×1.1」だった。VBOXの国内価格が同じ関係なら、この推定に近い（確度：中）
- **日本の代理店**：VBOX JAPAN 株式会社（https://vboxjapan.co.jp/ 、Racelogicの代理店一覧 https://vboxmotorsport.co.uk/en/distributors-worldwide でも日本はここ）。サイトに値段は無く、見積もり制。HD1はまだ載っていない

## 4. 構成B：1〜3の最低限（Video HD1）

| 品目 | 受け持つ機能 | 英国定価（VAT込み） | 推定（税込） | 出どころ | 確度 |
|---|---|---:|---:|---|---|
| VBOX Video HD1＋OLED表示器（RLVBHD1/D。25Hz GNSS、一体カメラ1台・1080p、CAN 2系統（CAN FD対応）、HDMI出力。電源・CANの線、GNSSアンテナ、32GBのSD、取付具つき） | 1（GNSS・CAN）、2、3 | £1,830 | 335,500円 | https://www.vboxmotorsport.store/index.php?route=product/product&product_id=203 ／ データシート https://www.vboxmotorsport.co.uk/downloads/datasheets/RLVBHD1_Data.pdf | 高（英国の値段）／低（日本の値段） |
| Micro Input Module（HD1用。アナログ4ch＋回転1ch、ケーブルRLCAB227込み） | 1（油温・油圧） | £190 | 34,800円 | https://www.vboxmotorsport.store/index.php?route=product/product&product_id=191 | 高 |
| HD1用 OBD CANケーブル（RLCAB160、2m） | 1 | £55 | 10,100円 | https://www.vboxmotorsport.store/index.php?route=product/product&product_id=73 | 高 |
| Circuit Tools 3 | 4 | 0 | 0円 | https://vboxmotorsport.co.uk/en/vbox-video-hd1 | 高 |
| **VBOXの分の小計** | | **£2,075** | **約38.0万円** | | |
| 油温・油圧センサー（VBOX純正は無い。AiMの見積もりと同程度と仮置き）＋取り出し（オイルブロック等） | 1 | | 約6〜7万円 | — | 低 |
| **計** | | | **約44〜45万円** | | |

- HD1はCANが2系統あるので、車両CANと入力モジュールを分け、OLEDをRS232でつなげばCAN Gatewayは要らないと見ている。3つを同時につなぐ配線はメーカーの資料で確かめていない（確度：中）
- HD1は2026年の新製品（データシートは2026-07付）

## 5. 構成A：全機能にいちばん近い（Video HD2）

| 品目 | 受け持つ機能 | 英国定価（VAT込み） | 推定（税込） | 出どころ | 確度 |
|---|---|---:|---:|---|---|
| VBOX Video HD2 Track Package＋OLED表示器（外付けカメラ2台、マイク、取付具2つ、電源線、GNSSアンテナ、32GBのSD、HDMIケーブル） | 1（GNSS・CAN）、2、3 | £2,980 | 546,300円 | https://www.vboxmotorsport.store/index.php?route=product/product&product_id=153 ／ データシート https://www.racelogic.co.uk/_downloads/vbox/Datasheets/Data_Loggers/VBOX_HD2_HDMI_25Hz_Data.pdf | 高（英国の値段）／低（日本の値段） |
| CAN Gateway（HD2の1つしかないCAN端子へ、車両CAN・入力モジュール・OLEDを同時につなぐ） | 1 | £495 | 90,800円 | https://www.vboxmotorsport.store/index.php?route=product/product&product_id=150 | 高（値段）／中（この組み合わせで要るか。車両CAN＋OLEDだけならCAN Splitter £160） |
| Micro IN Module（HD2用、アナログ4ch、センサー用5V出力あり） | 1（油温・油圧） | £210 | 38,500円 | https://www.vboxmotorsport.store/index.php?route=product/product&product_id=79 | 高 |
| OBDII CAN Cable（RLCAB069L、1.5m） | 1 | £90 | 16,500円 | https://www.vboxmotorsport.store/index.php?route=product/product&product_id=83 | 高（値段）／中（Gatewayにそのまま挿せるか） |
| Circuit Tools 3 | 4 | 0 | 0円 | 同上 | 高 |
| **VBOXの分の小計** | | **£3,775** | **約69.2万円** | | |
| 油温・油圧センサー（仮置き）＋取り出し | 1 | | 約6〜7万円 | — | 低 |
| HDMIの小型モニター（HD2のHDMI出力で、焼き込み入りの映像を運転席に映し、回転・温度・警告を補う。他社品） | 3 | | 1〜2万円 | https://vboxmotorsport.co.uk/en/vbox-video | 低（運転中の画面として使えるか未確認） |
| **1〜4の計** | | | **約77万円** | | |
| （5）PodiumConnect/Micro（Autosport Labs製。CANを読んで手元のWi-Fiホットスポット経由でPodiumへ。「VBOX対応」とあるが機種名は無い） | 5 | $349.95 | 7〜8万円（推定、1ドル155円と仮定、税・送料込みの見込み） | https://autosportlabs.com/product/podiumconnect-micro-live-motorsports-telemetry-stream-data-from-your-racecar-with-aim-motec-ecumaster-vbox-lowrance | 中（本体価格）／低（総額・VBOXとのつなぎ方） |
| **5まで含めた計** | | | **約85万円** | | |

- 回転・温度を画面に出す別の道：VBOX Touch Motorsport（4.3インチのカラー、CAN 2系統、Pythonで自分のアプリを書ける、£1,750≒32万円）。足すと高くなるうえ、自作のアプリが要る見込み（未確認）

## 6. 参考：安い構成

| 構成 | 英国定価（VAT込み） | 推定（税込） | 無いもの |
|---|---:|---:|---|
| HD1＋OBDケーブルだけ | £1,425 | 約26万円 | 油温・油圧、IMU、車載画面、ライブ |
| VBOX LapTimer（25Hz、OLED、ベストとの差） | £735 | 約13.5万円 | 車両CAN、映像、油温・油圧、IMU、ライブ |
| Performance Box Touch（25Hz、4.3インチのタッチ画面） | £575 | 約10.5万円 | 同上（CANの記載なし） |

- ラップ・GPS・速度だけなら、LapTimerやPerformance Box Touchで約10〜14万円。方針書1章の「シンプルなロガーは市販品（Dragy等）」の、もう一段上の選択肢になる

## 7. 現行品と廃番

- 現行（製品一覧 https://vboxmotorsport.co.uk/en/products ）：Video HD1、Video HD2、VBOX Touch Motorsport、Performance Box Touch、LapTimer（S／R）、Mini LapTimer（10Hz）
- 廃番（https://en.racelogic.support/motorsport/discontinued-legacy/ ）：VBOX Sport、PB Sport、旧型のVBOX HD、HD2の旧版、VBOX Touch v1、Performance Box Touch V1。Video VBOX Pro／Liteも現行の一覧に無い（廃番と見ているが推測）
- VBOX JAPANのHD2のページには、オプションとしてIMUセンサー（RLVBIMU05／04）が並んでいる。自動車試験用の製品で、英国のストアに無く、値段もHD2での使い方も未確認

## 8. 確かめきれなかったこと

- **日本の値段の全部**（VBOX JAPANは見積もり制）。代理店の上乗せ・送料・通関は入れていない。為替は1ポンド200円・1ドル155円と仮定
- HD1で、車両CAN・入力モジュール・OLEDを同時につなぐ配線。HD2で、OBDケーブルをCAN Gatewayにそのまま挿せるか
- 記録の速さ（何Hzで残るか）
- IMUセンサー（RLVBIMU05）の値段と、HD1／HD2で使えるか
- HDMIモニターを運転中の画面に使えるか（遅れ・見やすさ）
- PodiumConnectとVBOXのつなぎ方、日本での入手と総額、Podiumの利用料
- 英国の公式サイト（vboxmotorsport.co.uk）の一部のページは、自動の読み取りを断られた。HD1の仕様はストアの商品ページとデータシートで確かめた
