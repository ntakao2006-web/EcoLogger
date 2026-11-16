# 無料ソフト2本に任せて、足りない3つだけ自作する

> 2026-11-16 リポジトリへ収めた（書いたのは2026-11-14。直下の`reports/`に置いたまま未収録だった）。調べものの元のメモ（英語・出典つき）は`docs/research/analysis_software_survey_20261114_notes/`。**この報告のあと、解析は自前の専用アプリ（SP-10、別リポジトリ`ecologger-analysis`）で作ると決めた**（`task_spec_rebuild_breakdown.md`のSP-5-5・SP-10）。Circuit Tools 3 の止まり方は、同じ日の夜の追試で「2周目以降の動画を開くときだけ」「衛星数32の行を使わない」と分かった（同ファイルのSP-5-5）

2026-11-14 調査。自作ロガー（GNSS 10 Hz＋車両CAN＋IMU、走行後はCSV、計器を焼き込んだH.264動画をGNSSの時刻つきで録画、走行中はLTEで自宅のサーバーへ送ってピットのページとGrafanaで見ている）のデータを、使用許諾の問題なく解析できる既存のソフトを比べた。**どのソフトも、こちらのデータで実際に開く確かめはまだしていない**（READMEや公式ページ、ソースを読んだだけ）。

**結論から言うと、使用許諾の心配がなく、チーム全員にただで配れて、i2に近い解析ができるのは、有志の無料ソフト TrackDataAnalysis（MITライセンス）がいちばん近く、次が Racelogic の無料ソフト Circuit Tools と Bosch の WinDarab Free だった。** TrackDataAnalysis は周の重ね合わせ・タイムの差（タイムスリップ）・GPSのコース図・動画の再生をひと通り持ち、しかも RaceCapture のログ（`.log`）をそのまま読む。こちらのロガーはもともと RaceCapture 互換なので、書き出しの手間がいちばん小さい。WinDarab は**メーカー自身が「Bosch製でないデータもASCIIかMDFで取り込める」と公式に答えている唯一の本格ソフト**で、Free版は登録すればずっと使える。スマホで走行後に見るなら RaceChrono Pro に `.vbo` を取り込むのが現実的だった。一方で、動画の同期はどのソフトも手で合わせるか、仕組みがはっきりしない。こちらは動画にGNSSの時刻が入っているので、**「カーソルに連動する動画とコース図」「2周を距離でそろえた重ね合わせとタイムの差」は自分たちのアプリで作ったほうが確実**で、それに使う部品（グラフ・地図・計算の手本）はMITやBSDのものだけで揃う。書き出す形式は、(1) RaceCapture形式の `.log`、(2) `.vbo`、の2つで足り、WinDarab向けのASCIIは本格ソフトが要るときだけでよい。MoTeC の `.ld` は候補から外す。

## MoTeC i2 は、自作のデータで使うと使用許諾に反する

背景として、比べる基準にしている MoTeC i2 Pro は対象から外した。MoTeC の担当者がフォーラムで、MoTeC製でないデータからi2用の `.ld` を作ることは、i2を入れるときに同意する使用許諾に反すると答えている（[MoTeCフォーラム](https://forum.motec.com.au/viewtopic.php?p=2241)）。正規の道は、i2 API のPCごとのライセンス（[i2 API User Guide](https://www.motec.com.au/hessian/uploads/i2_API_User_Guide_330ed28c83.pdf)）、CSV取り込み機能のライセンス、MoTeCに他社ソフトとして認めてもらう、のどれかで、どれも有料になる。11/13の先行調査（`docs/research/analysis_export_formats_20261113.md`）では i2 の使用条件を「未確認」としていたが、この件で決着した。したがって、その資料が2番目に勧めていた `.ld`＋`.ldx` の書き出しは作らない。TrackDataAnalysis も `.ld` を読めるが、`.ld` は形式が非公開で、よく知られた読み書きの実装（ldparser）はGPL-3.0なので、わざわざ作る理由がない（[ldparser](https://github.com/gotzl/ldparser)）。

i2 と比べて今のアプリに足りないのは、**2周を距離でそろえた重ね合わせとタイムの差、カーソルに連動する動画、カーソルに連動するコース図**の3つだった。以下はこの3つを埋められるかを中心に見ている。

## 許諾と費用で絞ると、残るのは無料の3本と有料の数本

いちばん効いたのは「他社・自作のデータを使ってよいか」という基準だった。メーカーが公式に他社データの取り込みを認めているのは Bosch の WinDarab だけで、公式ページのよくある質問に、Bosch製でないデータも**ASCIIかMDFで取り込んで解析できる**とある（[Bosch WinDarab](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)）。使用許諾の説明には「同時に別のPCで動かしてはいけない」「複製・配布はBoschの書面の同意が要る」とあるが、データの出どころを縛る文は見つからなかった（[WinDarab Wiki の法的事項](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/239848075.html)）。TrackDataAnalysis はMITライセンスのオープンソースなので、使い方の制限はもともと無い（[GitHub](https://github.com/racer-coder/TrackDataAnalysis)）。Circuit Tools は無料で、Racelogic が `.vbo` の形式を開発者向けに公開しており、RaceChrono など他社のアプリが `.vbo` を書き出して Circuit Tools で開くことがフォーラムで普通に話されている（[VBOの構造](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html)、[RaceChronoフォーラム](https://racechrono.com/forum/discussion/comment/8449/)）。ただし Circuit Tools の使用許諾の本文は読めておらず、「他社のデータでも使ってよい」とはっきり書いた文も見つかっていない（**未確認**。公式ページが自動の読み取りを受け付けなかった）。

逆に、AiM の Race Studio 3 と Race Technology の解析ソフトは無料だが、他社のデータを取り込む口が見つからなかった（[RS3の更新履歴](https://docs.aim-sportline.com/racestudio3/html/release/software-release.html)、[Race Technology](https://race-technology.com/gb/racing/software/analysis-software)）。使うには自社の非公開の形式（`.xrk`・`.run`）をまねて書くことになり、MoTeCの `.ld` と同じ種類の危うさがあるので外した。GEMS の GDA はCSVを取り込めるが有料のProfessional版だけ（[GEMS GDA](https://gems.co.uk/products/software/gda/)、[GEMSフォーラム](https://www.gems.co.uk/gemsforum/viewtopic.php?p=1519)）、Cosworth の Pi Toolbox は無料のLite版が iRacing のデータ向けとしか書かれていない（[Cosworth Pi Toolbox](https://www.cosworth.com/motorsport/products/pi-toolbox)）。どちらも値段は公開されていない。

下の表が全体の比べ。「重ね合わせ等」は周の重ね合わせ・タイムの差・コース図をまとめた欄。

| ソフト | 重ね合わせ等 | 動画との同期 | 他社・自作データの許諾 | 費用・配りやすさ | 読ませる形式（仕様） | Windows / Android | 保守 |
|---|---|---|---|---|---|---|---|
| **TrackDataAnalysis** | ○ 距離・時間の重ね合わせ、タイムの差、GPSのコース図、計算チャンネル | ○ ただし1ログに動画1本、位置合わせは手で | ○ MIT（制限なし） | 無料。各自がGitHubから入れる | RaceCapture `.log`、`.vbo`、`.ld`、AiM `.xrk` ほか。汎用CSVは不可。`.log` の読み方はソースで読める | Windows・Linux・Mac / × | 作者1人。配布版は 0.4.1（2024年2月）のまま、本体のコードは2026年9月まで更新 |
| **Circuit Tools 3** | ○（計算・レポートのメニューあり。細部は**未確認**） | △ `.vbo` の同期用の列で合わせる。他社の動画の扱いにくせあり | △ 形式は公開、許諾の本文は**未確認** | 無料（検索の要約のみ） | `.vbo`（**公式に公開**） | Windows・Mac / × | 版と日付は**未確認** |
| **WinDarab Free** | ○ 重ね合わせ、GPSからのコース図、区間、計算チャンネル | △ 「計測の動画」機能あり、合わせ方は**未確認** | **◎ メーカーが公式に可と回答** | 無料（20日以内に登録、開けるファイルは4つまで、1台ずつ） | ASCII・MDF（ASCIIの細かい書式は**未確認**） | Windows / × | V7.10（2025年） |
| **RaceChrono Pro** | ○ グラフ・地図・動画の連動、タイムの差 | △ GoPro・Garmin以外は手で | ○ 取り込みもDIY機器も機能として用意 | 有料アプリ（値段は**未確認**）。各自が買う | `.vbo` 推奨、NMEA | ○ / ○ | v10.3.3（2026年11月13日） |
| GEMS GDA Pro | ○ | ○ 動画の読み込みと同期 | ○ CSV取り込みはPro版の機能 | 有料（値段非公開） | CSV | Windows / × | **未確認** |
| Cosworth Pi Toolbox | ○ | **未確認** | Lite は iRacing のみ。上位版は**未確認** | Lite無料、上位は営業経由 | **未確認** | Windows / × | v14 |
| AiM Race Studio 3 | ○（AiMのデータのみ） | AiMのカメラのみ | × 取り込む口が無い | 無料 | 自社形式のみ | Windows / × | 3.85.12（2026年11月12日） |
| Race Technology Analysis | ○ | ○（GoPro） | × 取り込む口が見つからない | 無料 | 自社形式のみ | Windows / × | 10.0.0438（2026年1月） |
| Telemetry Overlay | × 解析より動画づくり | ○ `utc (ms)` の列で自動の見込み | ○ 自前CSVの書式を公開 | 買い切り199ドル（更新1年） | 独自CSV（**公開**） | Windows・Mac・Linux / × | 販売中 |
| RaceRender | × 動画づくり | △ 合わせる道具あり、自動かは**未確認** | ○ CSVの書式を公開 | 無料版は3分まで・ロゴ入り、有料39.95〜59.95ドル | CSV（**公開**）、`.vbo` | Windows・Mac / × | 3.7.3、ページは2022年。動きは遅い |
| Track Attack | ○ | ○ 「どの動画でも自動」とされるが仕組みは**未確認** | ○（利用者の話で RaceCapture のログも可） | Pro 月5.99ドル・年49.99ドル | 公式の一覧なし（**未確認**） | 主にスマホ / ○ | **未確認** |
| PlotJuggler | × 周・距離の考えが無い | MP4の再生はある | ○ MPL-2.0 | 無料、管理者権限なしで入る | 任意のCSV、MQTT・UDP・WebSocketのライブ | Windows・Linux / × | 4.1.0（2026年11月5日） |
| （参考）MoTeC i2 Pro | ◎ | ○ | **× 他社データは使用許諾違反** | 正規の道は有料 | `.ld`（非公開） | Windows / × | 対象外 |

出どころ：TrackDataAnalysis（[GitHub](https://github.com/racer-coder/TrackDataAnalysis)、[配布版](https://github.com/racer-coder/TrackDataAnalysis/releases)）、Circuit Tools（[公式](https://vboxmotorsport.co.uk/us/circuit-tools)、[CT3のメニュー](https://support-centre.racelogic.co.uk/motorsport/software/ct3/ug/toolbar/)）、WinDarab（[公式](https://www.bosch-motorsport.com/products-and-services/software-highlights/windarab/)、[7.10](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/392199435.html)）、RaceChrono（[公式](https://racechrono.com/)、[取り込みの話](https://racechrono.com/forum/discussion/1654/can-we-still-import-nmea-files)）、Telemetry Overlay（[公式](https://goprotelemetryextractor.com/)、[自前CSV](https://goprotelemetryextractor.com/tools-for-custom-csv)）、RaceRender（[機能](https://racerender.com/RR3/Features.html)、[データ形式](https://racerender.com/Developer/DataFormat.html)）、Track Attack（[App Store](https://apps.apple.com/app/id1557802135)、[HP Academy](https://www.hpacademy.com/forum/data-analysis-fundamentals/show/racecapture/)）、PlotJuggler（[GitHub](https://github.com/PlotJuggler/PlotJuggler)、[4.1.0](https://github.com/PlotJuggler/PlotJuggler/releases/tag/4.1.0)）。

チームへの配り方は、どれも**ソフトそのものは各自がメーカーやGitHubから入れ、チームはデータと画面の設定だけを配る**形がいちばん安全だった。WinDarab の入れ物を勝手に配るには Bosch の同意が要る（[WinDarab Wiki](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/239848075.html)）。TrackDataAnalysis の Windows の入れ物には動画再生の部品 `libmpv-2.dll` が同梱されていて、これは作り方しだいでGPLにもLGPLにもなる（[setup.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/setup.py)、[ui/mpv.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/ui/mpv.py)）。どちらで作られたものかは**未確認**なので、こちらで入れ物を作り直して配るのは避け、各自に公式の配布版を入れてもらう。日本語の画面を持つソフトは1本も確かめられなかったので、どれを選んでも短い日本語の手順書が要る。

## TrackDataAnalysis が i2 にいちばん近いが、作者1人で配布版が古い

TrackDataAnalysis は、作者が「MoTeC では 1080p・60コマの動画がカクついた」ことをきっかけに作った解析ソフトで、距離・時間のグラフに複数の周を重ね、周ごとにずらし、タイムの差を出し、衛星写真つきのGPSのコース図で走行ラインを比べ、計算チャンネルを使える。動画は**距離で重ねたときも、比べる側の周の再生を速めたり遅めたりして同期を保つ**（[GitHub](https://github.com/racer-coder/TrackDataAnalysis)）。i2 で足りない3つのうち、重ね合わせとタイムの差とコース図はこれで埋まる。衛星写真の背景には無料の MapTiler のキーが要り、無ければ線だけになる（同上）。

弱みは3つある。1つ目は**動画が1ログに1本だけで、位置合わせを手でやる**こと（周の頭にカーソルを置き、右クリックで「Set video alignment」、下のスライダーを動かして合わせる）。合わせた値が保存されるかは**未確認**（[GitHub](https://github.com/racer-coder/TrackDataAnalysis)）。2つ目は**配布版が 0.4.1（2024年2月）で止まっている**こと。区間ごとのタイムの表、コースの編集、ヒストグラムなどは開発中の版（main）にしか無く、使うには Python と libmpv を手で入れる必要があって、ソフトが専門でないメンバーには現実的でない（[ui/](https://github.com/racer-coder/TrackDataAnalysis/tree/main/ui)、[配布版](https://github.com/racer-coder/TrackDataAnalysis/releases)）。3つ目は**作者1人の小さな計画**（スター66）で、いつ止まってもおかしくないこと。ただ、2025年11月以降の直近100件のうち40件がコードの更新で、動き自体は続いている（[コミット](https://github.com/racer-coder/TrackDataAnalysis/commits/main)）。

読ませる形式では、**RaceCapture（Autosport Labs）の `.log` をそのまま読む**のが大きい。中身はカンマ区切りのCSVで、見出しは `"名前"|"単位"|...` の形、1列目がミリ秒の時刻、周の区切りに `LapCount` の列が要り、`Utc` から日時を取り、`Speed`・`Latitude`・`Longitude`・`Altitude` を決まった名前で読む。空のマスは飛ばすので、間隔の違う列が混ざってもよい（[data/autosport_labs.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/data/autosport_labs.py)）。この形式の公式の説明書は見つからなかったが、読む側のソースがMITで公開されているので、それが事実上の仕様になる。`.vbo` も読めるはずだが、2026年1月に「VBOXの形式が合わない？」という未解決の報告が出ている（[issues](https://github.com/racer-coder/TrackDataAnalysis/issues)）。TrackDataAnalysis へは `.log` で入れるのが安全だった。

## 動画とリアルタイムは、既製品より自前のほうが筋がよい

動画の同期で、こちらと同じ「データ側も動画側もGPSの時刻を持っている」前提で自動に合わせてくれるソフトは、はっきりとは見つからなかった。RaceChrono が自動で合わせるのは GoPro と Garmin VIRB だけで、ほかは手で直し、自動でも2秒ずれたという報告がある（[RaceChrono 解説](https://racechrono.com/article/480)、[フォーラム](https://racechrono.com/forum/discussion/comment/8874/)）。Circuit Tools は `.vbo` の `[avi]` 欄と `avifileindex`・`avisynctime` の列で動画とつなぐが、`avisynctime` の単位は公式ページに書かれていない（[VBOの構造](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html)）。しかも、見出しの名前の食い違いで落ちる、データが動画より先に始まると同期が崩れる、MP4と宣言しないとAVIとみなす、といったくせが報告されている（[RaceChronoフォーラム 1395](https://racechrono.com/forum/discussion/1395/vbo-video-sync-messed-up-when-exporting-whole-session)、[2358](https://www.racechrono.com/forum/discussion/2358/vbo-video-export-crashes-circuit-tools-with-index-exception)）。Telemetry Overlay は `utc (ms)` の列で自動に合わせられるという他社の話があるが、GoPro以外の動画のどこから時刻を読むかは書かれていない（[自前CSV](https://goprotelemetryextractor.com/tools-for-custom-csv)、[rkd-telemetry-extractor](https://github.com/sam-dumont/rkd-telemetry-extractor)）。

動画の入れ物にも注意が要る。こちらの録画は MPEG-TS（音声はMP2）だが、**MPEG-TSを読めると書いたソフトは1本も無かった**。Circuit Tools はAVIとMP4（[CT3の更新記録](https://vboxmotorsport.co.uk/en/fw-sw/release-notes-circuit-tools-3)）、RaceChrono は他社カメラの音声の形式で書き出しに失敗した報告がある（[フォーラム](https://racechrono.com/forum/discussion/comment/8980/)）。既製品に渡すなら、回収のときに**映像はそのまま写してMP4へ詰め替え、音声はAACへ変えるか捨てる**のが無難（こちらの判断。どのソフトでも試していない）。TrackDataAnalysis は libmpv で再生するので「ほぼ何でも」読めるとされ、TSのままでも開く見込みがいちばん高い（[GitHub](https://github.com/racer-coder/TrackDataAnalysis)）。

こう並べると、**各フレームのGNSSの時刻をすでに持っているこちらのアプリで、カーソルの時刻から動画の位置を引くほうが、他社のくせと戦うより確実**になる。計器は焼き込み済みなので、Telemetry Overlay や RaceRender で計器を重ねる用事はほとんど無く、使うとしても人に見せる動画を作るときだけでよい。

リアルタイムについては、今の「LTEで自宅のサーバーへ送り、ピットのページとGrafanaで見る」形が、学生チームのよくある形そのものだった。CANをLTEでMQTTへ送ってダッシュボードで見る例は他チームにもあり（[CSS Electronics の事例](https://www.csselectronics.com/pages/real-time-dashboard-telematics-solar-car)、[SingleStore の記事](https://www.singlestore.com/blog/building-a-real-time-analytics-pipeline-for-race-cars/)）、周回の計時まで含んだ「そのまま使える」オープンソースの一式は見つからなかった。足すとすれば、エンジニアがPCでライブの値を細かく見る用に PlotJuggler（MQTT・WebSocket・UDPを受けられ、Windowsでは管理者権限なしで入る）がある（[GitHub](https://github.com/PlotJuggler/PlotJuggler)）。車内のスマホへライブで流す道としては、RaceChrono が公開している自作機器向けの2つの方式（NMEAに独自の行を足した RC2/RC3 をWi-FiのTCPかBluetoothで送る方式と、BLEでGPSとCANの生の値を送る方式）がいちばん資料が揃っていた（[RaceChrono DIY](https://racechrono.com/article/2572)、[BLEの仕様](https://github.com/aollin/racechrono-ble-diy-device)）。ただしBLEの方式は「まだ変わるかもしれない」と注意書きがあり、自作機器の入力はPro版の機能になる（[RaceChrono](https://racechrono.com/)）。Harry's LapTimer GrandPrix は RaceCapture を対応機器に挙げているので、こちらの RaceCapture 互換の送信がそのまま通る可能性がある（[Harry's 対応機器](https://gps-laptimer.de/compatibility/android)。**未確認**、試していない）。どの方式も、実装するのに料金や許諾が要るとは書かれていないが、はっきり許すとも書かれていないので、ロガーを売る前にはメーカーへ聞いたほうがよい。

## 作るのは3つの画面、任せるのは深掘りとスマホ

以上から、自分たちのアプリと既存ソフトの分担は次のようにするのがよい。軸は、**毎回の走行後にチーム全員がすぐ見る物は自前（日本語・自動の動画同期・エコラン固有の数字）、たまに深く掘る物は既存ソフト**、という分け方。

| 用事 | 担当 | 理由 |
|---|---|---|
| 2周を距離でそろえた重ね合わせとタイムの差 | **自前で作る** | i2との差の本丸。距離の計算とそろえ直しは TrackDataAnalysis（MIT）の `data/distance.py` や FastF1（MIT）のやり方を手本にできる |
| カーソルに連動するコース図 | **自前で作る** | 地図は Leaflet（BSD-2）で描ける |
| カーソルに連動する動画 | **自前で作る** | GNSSの時刻で自動に合わせられるのはこちらだけの強み。既製品はどれも手合わせか仕組みが不明 |
| 周の表・レポート・周の動画の切り出し | 自前（済み） | すでにある |
| ピットのページ・ライブの値 | 自前とGrafana（済み） | すでによくある形になっている |
| 計算チャンネル・ヒストグラム・区間の表などの深掘り | **TrackDataAnalysis に任せる**（本格的に要るなら WinDarab Free） | 作ると重い。たまにしか使わない |
| スマホで走行後に見る | **RaceChrono Pro に任せる**（`.vbo` を取り込む） | Androidで他社のログを取り込めると書いてあるのはこれだけ |
| 人に見せる動画（計器を足す） | 必要なときだけ Telemetry Overlay・RaceRender | 計器は焼き込み済みで用事が少ない |
| エンジニアのライブのデバッグ | 必要なら PlotJuggler | サーバーから値をMQTTかWebSocketで流し直すだけで足せる |

アプリに部品を埋め込むときは、公開リポジトリで将来売るかもしれないことを考えて、**MIT・BSD・Apache-2.0 の物だけをアプリの中に入れ、GPL・AGPL の物は別のプログラムとして横に置く**。グラフは uPlot（MIT）か Apache ECharts（Apache-2.0、NOTICEファイルを残す決まりあり）、地図は Leaflet（BSD-2）、計算の手本は TrackDataAnalysis と FastF1（どちらもMIT、著作権表示を残す）、CANの定義は cantools（MIT）がよい。RaceCapture の公式アプリ（GPL-3.0）と ldparser（GPL-3.0）はコードを貼ると、アプリ全体をGPLにしなければならなくなるので使わない。Grafana（AGPL-3.0）は今のように手を加えず別のサービスとして動かす分には問題ないが、手を加えてネット越しに提供すると、ソースを出す義務がかかる。asammdf と python-can（どちらもLGPL-3.0）は、手を加えずに呼ぶだけならよい（[ライセンスの一覧](https://github.com/racer-coder/TrackDataAnalysis)、[uPlot](https://github.com/leeoniya/uPlot)、[ECharts](https://github.com/apache/echarts)、[Leaflet](https://github.com/Leaflet/Leaflet)、[FastF1](https://github.com/theOehrly/Fast-F1)、[cantools](https://github.com/cantools/cantools)、[Gitee上のRaceCaptureアプリの写し](https://gitee.com/mirrors_Knio/RaceCapture_App)、[Grafana](https://github.com/grafana/grafana)、[asammdf](https://github.com/danielhrisca/asammdf/blob/master/LICENSE)）。

書き出す形式は、11/13の先行調査の順（`.vbo` → `.ld`）を改め、次の順にする。

| 順 | 形式 | 開くソフト | 仕様 | 理由・注意 |
|---|---|---|---|---|
| 1 | **RaceCapture形式の `.log`** | TrackDataAnalysis（ほかに RaceCapture アプリ、Track Attack も読むという話あり） | 公式の説明書は見つからない。読む側のソースがMITで公開 | ロガーがもともと RaceCapture 互換なので手間が最小。必要な列は時刻（ミリ秒）・`Utc`・`LapCount`・`Speed`・`Latitude`・`Longitude`・`Altitude`。速度の単位の扱いは**未確認**なので、試しのファイルで確かめる |
| 2 | **`.vbo`** | Circuit Tools、RaceChrono Pro（スマホ）、RaceRender、Telemetry Overlay、Track Attack | **公式に公開** | 1つで開けるソフトがいちばん多い。経度は「分×-100000」で東経が負になる、見出しと列の名前をそろえる、`avisynctime` の単位は**未確認**、TrackDataAnalysis では合わない報告あり |
| 3 | WinDarab向けASCII（またはMDF4） | WinDarab Free | ASCIIの細かい書式は操作説明書にあるはずだが**未確認** | 本格ソフトが要ると決まったときだけ。メーカー公認なので許諾の心配はいちばん小さい |
| 4 | Telemetry Overlay向けCSV（`utc (ms)` つき） | Telemetry Overlay | **公開** | 人に見せる動画を作る用事が出たときだけ |
| 作らない | `.ld`＋`.ldx`、MoTeCのCSV、AiM `.xrk`、Race Technology `.run` | — | 非公開・有料 | 使用許諾か形式の面で問題がある |

出どころ：[autosport_labs.py](https://github.com/racer-coder/TrackDataAnalysis/blob/main/data/autosport_labs.py)、[VBOの構造](https://developers.racelogic.co.uk/Portal/Tutorials/tutorialVBOfilestructure.html)、[RaceChronoの `.vbo` 推奨](https://racechrono.com/forum/discussion/comment/12422/)、[WinDarab V7 操作説明書](https://www.bosch-motorsport.com/content/downloads/Raceparts/Resources/pdf/Operation%20Manual_70959883_Analysis_Tool_WinDarab_V7.pdf)、[Telemetry Overlay の自前CSV](https://goprotelemetryextractor.com/tools-for-custom-csv)。

## 結論

今回の調べでいちばん考えが変わったのは、「i2 と同じ物を外から借りる」より「i2 との差を3つの画面に絞って自分で作る」ほうが近道だという点だった。既製品の解析ソフトは、データの重ね合わせまではよくできているが、**他社の動画をGPSの時刻で自動に合わせる所はどれも弱い**。ここはGNSSの時刻つき録画を持つこちらが、既製品より上を取れる唯一の所でもある。重ね合わせとタイムの差の計算はMITの手本があるので、作る量は思ったより小さく、ロガーを売る日が来てもライセンスで困らない。

一方で、TrackDataAnalysis は作者1人で配布版が2年近く止まっているので、チームの標準を全面的に預けるのは危ない。`.log` と `.vbo` の2つを書き出しておけば、TrackDataAnalysis が止まっても Circuit Tools や RaceChrono へ逃げられ、WinDarab へも道を残せる。次の一歩は、走行1回分の `.log` と `.vbo` を試しに作り、TrackDataAnalysis 0.4.1・Circuit Tools・RaceChrono Pro で実際に開くかを見ることで、その時に Circuit Tools の使用許諾の本文と、`avisynctime` の単位を確かめる。
