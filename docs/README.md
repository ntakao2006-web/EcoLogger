# 資料の案内（docs/ と直下の資料）

資料1本ごとの説明。`CLAUDE.md`の「ファイル構成」にあった文面を2026-11-13にここへ移した（文面はそのまま）。
**資料を足した・最新が変わった・送った・回答が来たときは、ここを直す。** 道具の説明は`tools/README.md`。

- 置き場所の決まりは`ARCHITECTURE.md` 8章「ファイル構成方針」。
- 古い資料に出てくる直下のファイル名の読み替えは`ARCHITECTURE.md` 4章の頭「いまの姿」の表。

## 直下に置いてある資料

- `ARCHITECTURE.md`：プロジェクト全体のマスターファイル
- `SPEC.md`：**Ver.2の仕様書（2026-11-13、下書き）**。誰に・どの場面で・何をできるようにするか（要求）、守る決まり（3章）、入口を場所ごとに1つにする方針（7章）、今の道具の仕分け案（8章）、ユーザーに決めてほしいこと（9章）。**道具や画面を足す・直す・やめるときは、まずここの要求に当てはめる**。現在地とロードマップは`ARCHITECTURE.md`のまま
- `task_spec_rebuild_breakdown.md`：`SPEC.md`に合わせて道具・入口を作り直す作業の分解（SP-x、2026-11-13）。PCのアプリを1つにする・車とコースを選ぶ・走行を見る・スマホの入口・車載画面の印。**本体に入れる分は展示用のファームから戻したあと、自宅のサーバーに入れる分はユーザーの了承のあと**
- `v2_hardware_overview.html`：**Ver.2のハードウェア構成図**（チームに見せる用。2026-11-10、SUGOを走った形）。電源の流れ・基板の積み重ね（下からUNO Q→UPS→シールド）・センサー・ドック/モニター/カメラ、LTE→SORACOM→自宅5B→ピット画面の道、部品の一覧・部品代、**外から本体へつなぐ3つの道（USBのadb・テザリング・LTE）でできること・できないことの○△×の表**。後半は**ソフトウェアの構成**（本体のSTM32ファーム・Arduino Router・EcoCapture・DASH・焼き込み録画・見守り役、5B・PC・スマホのソフト、置き場所の一覧）。Artifactのページにも載せてある（同じファイルを出し直すと更新）。構成やソフトの役割を変えたらここも直す。公開リポジトリなので5BのURLは書かない
- `v2_firmware_backup_20261110.md`：**Ver.2のファームの控えと戻し方**（2026-11-10、展示会で書き換える前にSUGOを走った形で取った）。STM32のフラッシュ全体・今のロガーの像・Linux側（ホーム・`/opt`・systemd・Docker像）の置き場（PCの`Documents\UNOQ_fw_backup\2026-11-10\`とNAS）、確かめたこと、展示用のファームを入れるときの注意（監視役を止める）、ロガーだけ／土台から／Linux側の戻し方。**展示のあとで元へ戻すときはまずこれを開く**
- `HANDOFF.md`：RCP JSONプロトコルの実測仕様の詳細
- `sensorhub_generic_spec.md`：**汎用センサーハブ**（アナログ8ch・デジタル4ch・出力2ch、PIC＋外部CAN数珠繋ぎ）のLintarohさん向け要求仕様。Defi傍受基板とは別物で併用する。**外部CANバス全体のID割り当て表（5章）と、設定をロガー側に置く運用ルール（6章）もここが正**
- `unoq_video_check_procedure.md`：UNO Qの映像確認（V-1〜V-5）の手順と実測結果。5-6章に走行映像へのプロット焼き込みの模擬試験（試験プログラムは`tools/unoq_overlay_enc/`）。5-14章が焼き込む計器の設定ファイル（ユーザーが書き換える`tools/video_hud/hud.ini`、PCで見る`Preview-HUD.cmd`、本体へ送る`Apply-HUD.cmd`）。5-16章がRaceChronoのような配置（針のメーター・コース図・ベストとの差。差は本体の`tools/unoq_overlay_enc/lap_ref.h`で計算。**2026-11-04に本体へ導入済み**、前の版は`*.pre-v2-20261104`）。5-17章が動画の「走行＋章」の名前と回収アプリ、5-18章が**ドラレコ式の消し方**（動画と走行記録をまとめて回収済み→ほかの古い順、下限1GiB。決まりは録画の`video_store.h`とEcoCaptureの`EcoCapture-Web/video_store.py`で同じ、場面の試験は`tools/unoq_overlay_enc/testdata/video_store/`）とSDカードの画面。5-19章が**レンズの歪みの補正・ズーム**と、本体のモニターで画角を決めるプレビュー（`tools/lens_view/`：PCで見る`Lens-View.cmd`、モニターで決める`Lens-Preview.cmd`、値を送る`Apply-Lens.cmd`。値は本体の`/home/arduino/ecologger-video/lens.json`、無ければ補正しない）。5-20章が**録画の音**（カメラ内蔵のマイクをMP2で`.ts`へ。本体に`libtwolame0`が要り、無ければ音なし。試験は`tools/unoq_overlay_enc/audio_mux_test.c`）とGボールの横の向き。5-21章が**露出を録画プログラムで決める仕組み**（明るい日の白飛び対策。`tools/unoq_overlay_enc/auto_exposure.h`、設定は本体の`/home/arduino/ecologger-video/exposure.ini`、`mode = camera`でカメラ任せに戻る。PCから見る・切り替えるのは`tools/video_exposure/Exposure.cmd`）。5-22章が焼き込みの回転計の色を車の画面（DASH）と同じ決まりにした分（DASHの帯そのものは画角に写るので焼き込まない）。5-23章が**録画の音の割れ**の対策（カメラのマイクの音量を−15dBへ下げる`mic-volume.sh`、100Hzより下を削る・リミッター。調整は本体の`/home/arduino/ecologger-video/audio.ini`、`mic_volume`はdBで書く）。5-24章が**針の補間**（値を約25Hzで読み、カメラがその絵を撮った時刻の値を`mcu_ms`の時刻で前後の間から補間して描く。`tools/unoq_overlay_enc/tele_smooth.h`、調整は本体の`~/ecologger-video/smooth_ms`（待つ上限）・`telemetry_hz`、`smooth_ms`に0で前の描き方）。5-25章が**1周だけの切り出しと、人に見せる音の風切り対策**（`tools/lap_video/`）
- `unoq_video_to_shield_sd_study.md`：焼き込み映像をシールド側SDへ保存できるか（E-6）の調査。Linux→STM32の内部SPI、ビットレートと画質の実測、SD側のボトルネック
- `server_deploy_grafana_x86.md`：自宅ROCK 5Bのピット用Grafana（EcoRun Live）・「周回・時間」のページ・地図を、別のLinuxサーバー（主サーバーにする先輩のラックサーバー）で**5Bと同じに立てる**ための引き継ぎ資料（2026-10-25 10時の5Bの実物と照合した版）。画面の構成・ブリッジがしていること・10/18以降のUI変更・5Bの設定との対応表・手順。実際のファイルは`tools/home_telemetry/deploy/`（VictoriaMetrics・Grafana・ブリッジのDocker Compose）。チームの`latest`がJSON Linesを書くのでサーバー本体の変更は不要。先輩へ送る文面は`docs/share/maruo_share_20261025_dashboard.md`
- `task_sugo_20261108_breakdown.md`：**SUGO 120分耐久（2026-11-08、ロードスターNCEC）**向けのロガー・車載ダッシュ・インジケーター・油温油圧の基板の分解と日程（SG-x）。大会そのものの準備は`ncec-roadster`リポジトリ側
- `task_kart_20261129_breakdown.md`：カート用ロガー試作0号を**2026-11-29に富士スピードウェイ カートコース**で使うための分解と日程（KT-x）。**2026-11-16にやめた（ユーザー決定。シンプルなロガーは市販品のほうが安く安定している）**。調査資料・部品リスト・GNSSの載せ台基板の案は`archive/kart/`へ移した（MyLapsのラインとラップの取り方・CIKの規則・ステアリング角の付け方は参考に残る）
- `ncec_next_session_checklist.md`：**NCECに実車接続する前に必ず開く**。実車が無いと解けない宿題の一覧
- `task_phaseX_breakdown.md`：各フェーズのサブタスク分解（1チャット=1タスク粒度）

## `docs/share/` — 人に渡したメモと、その回答

- **人に渡したメモとその回答は`docs/share/`に置く**（2026-11-13に直下から移した。新しいメモ・回答もここへ。ソフトのコメントから名指しされている`hardware_share_20261004_podium.md`と`lintaroh_answer_20261101_defi_volt.md`の2本だけは直下のまま）
- `docs/share/hardware_meeting_agenda.md`：友人とのミーティングをどの順番で進めるかの道しるべ（`docs/design/hardware_interface_spec.md`各章への案内役）
- `docs/share/hardware_share_YYYYMMDD.md`：回路担当へ渡すための日付つきメモ。**最新は`docs/share/hardware_share_20260921.md`**で、これは差分メモではなく「いま未回答の依頼・質問を全部1枚に集約したもの」（それ以前の資料はどれも未送だったため）。**2026-09-21に送付済み・回答受領済み**で、各「回答欄」に結論を転記してある。`docs/share/hardware_share_20260915.md`はバス負荷・CAN周期・4輪特定・基板まわりの訂正をまとめたもので、20260921版の5-2章から判断材料として参照している。`docs/share/hardware_share_20261004.md`はLTEアンテナ（市販貼り付け品FXUB63＋SMA接続）の発注依頼だけをまとめた単発メモ。`hardware_share_20261004_podium.md`はV2のPodium送信を実装する回路担当向けの**次世代Podiumの確定版プロトコル**（2026-10-04実測。認証形式が旧資料から変わっている）
- `docs/share/hardware_ans_YYYYMMDD.md`：**回路担当からの回答の一次資料**。最新は`docs/share/hardware_ans_20260921.md`。回答原文をそのまま残し、確定したこと／確定しなかったこと・**こちら側の記述が訂正された箇所**・**この回答で新たに発生したこちらの宿題**を整理してある。ハード側の話が出たら`docs/share/hardware_share_*`とセットで読む
- `docs/share/lintaroh_share_YYYYMMDD.md`：Lintarohさんへの共有メモ。**Lintarohさんは回路担当と同一人物**で、回路・基板・電源を担当している。**UNO QのLinux側のソフト・EcoCapture・STM32のファームは基本こちら（ユーザーとClaude）で作る**ので、ソフトを変えても報告用のメモは作らず、記録は分解ファイルとARCHITECTURE.mdだけにする（2026-11-09。それより前のファームやUNO Qのソフトには、Lintarohさんが書いたものも含まれる）（`docs/share/hardware_share_*`・`docs/share/hardware_ans_*`の「回路担当」も同じ人）。最新は`docs/share/lintaroh_share_20261009_2.md`（稼働中ソースの確定、CAN2のACKとループ監視の導入、**内部リセット後にLinuxとの通信路が戻らない件の相談**、Linux側の監視役`mcu-supervisor.py`、RAMの実際の限界）。その前が`docs/share/lintaroh_share_20261009.md`（ファーム書き込みでLinux側UARTが固まる件、UNO Q上でしたこと、ソースの食い違い、E-6の結果と相談）と`docs/share/lintaroh_share_20261009_power.md`（カメラ・モニターの機材構成案、UPSモジュールとの組み合わせで確認したいこと）、`docs/share/lintaroh_share_20261010_sensorhub.md`（汎用センサーハブの仕様の要点と判断してほしい8項目。本体は`sensorhub_generic_spec.md`）、`docs/share/lintaroh_share_20261013_oiltemp.md`（エコラン大会向けにユニバーサル基板版ハブで油温を読むための確認事項）、`docs/share/lintaroh_share_20261015_audio.md`（ドライバーの音声を音声基板からUSBオーディオへ変える相談、未送）、`docs/share/lintaroh_share_20261018_unoq_damage.md`（今のUNO Qの裏面のチップ部品が脱落している件と、内蔵Bluetoothが固まった件、買い替えの相談。未送・写真を貼る欄あり）、`docs/share/lintaroh_share_20261025_sugo.md`（SUGO 120分耐久でロードスターの油温・油圧を読む基板を11/3までに用意できるかの相談。未送）、`docs/share/lintaroh_share_20261105_dock_power.md`（電源が一瞬切れるとUPSの外のUSB-Cドックだけが落ち、モニターとカメラがLinuxの再起動まで戻らない件。ドックをUPSの内側に入れる案・入力断の知らせと正しい停止の相談。10/9の電源メモ3章の聞き直しを兼ねる。未送）
- `docs/share/lintaroh_share_20261113_12v_ups.md`：車の電源へ直接つなぐにあたり、ヒューズ電源と車用充電器の間（12V側）に数秒だけ保つ小さなUPSを作ってもらえるかの相談。今のUPSモジュールを残すか・止まるまでが長い件もあわせて聞く。調べた市販品の一覧つき。期限は12/5の3〜4日前、Lintarohさんは11/20以降に動ける（11/13）。20日までにこちらで消費電力とヒューズの容量を測って書き足す
- `docs/share/lintaroh_share_20261113_repo.md`：リポジトリ名を`EcoLogger`へ変えたこと・資料をフォルダーへ移したこと・Codex向けの入口`AGENTS.md`・「RaceCaptureから離れる」方針の連絡と、返事がほしい3点（未送、2026-11-13）
- `docs/share/lintaroh_answer_YYYYMMDD.md`：**Lintarohさんからの回答の一次資料**（本人がリポジトリへ直接push）。最新は`lintaroh_answer_20261101_defi_volt.md`（SUGO向けのPICファームv8：Defiの油圧・温度2chの電圧をCAN2 0x580で送るパケットの確定仕様と、UNO Q側の更新手順の引継ぎ。ユーザー経由で受け取った写し。PICへの書き込みは未）。その前が`docs/share/lintaroh_answer_20261009.md`（ファーム更新手順を共通の`EcoCapture-Web/flash-mcu.sh`へ統一、稼働中ファームの正しいソースは未確定、**STM32のRAMは現状でも映像用リングを足す余地が無い**、E-6の段階的な統合手順と本番採用の判定条件）
- `docs/share/maruo_share_YYYYMMDD_*.md`：Maruo.Sさん（チームの通話サーバー`ecorun-logger-server`の作者）への相談。`docs/share/maruo_share_20261015_discord.md`はピットの通話をDiscordに戻す相談（未送）、`docs/share/maruo_share_20261025_dashboard.md`はピット用ダッシュボードを主サーバーでも5Bと完全に同じに立てるための連絡（未送。10/24版`docs/share/maruo_share_20261024_grafana.md`の差し替え）、`docs/share/maruo_share_20261025_cluster.md`は先輩のサーバー→5Bの複製が約21時間止まっていた件と、5Bの再起動後に複製の接続・Ver.2の接続が先輩側から切られた件の報告と質問（未送）、`docs/share/maruo_share_20261025_podium_rows.md`は先輩のサーバーの「skipping Podium sample…」の警告の原因（ロガーはPodium本来の詰めた形で送り、サーバーのデコードが固定長を前提にしている）と5B側ログの照合結果（未送）、`docs/share/maruo_share_20261030_server_pause.md`は先輩のサーバーを当面止めてもらい自宅の5Bをメインにする連絡（未送）、`docs/share/maruo_share_20261017_rock5b.md`は大会用の予備サーバーのお願いと、先輩がPR#1へ入れた実装（`4482ede`）にロガーから合わせるための相談（地図に位置を出す方法・ロガー向け音声。2026-10-18送付済み）
- `docs/share/maruo_answer_YYYYMMDD.md`：**Maruo.Sさんからの回答の一次資料**。最新は`docs/share/maruo_answer_20261025.md`（ダッシュボード引き継ぎの確認事項への回答：入口は先輩が手で用意済み、ポートも先輩が直した、画面の更新はまだ。外から見た先輩のサーバーの状態と5Bとの違い）。その前が`docs/share/maruo_answer_20261018.md`（予備は先輩宅のラックサーバー、分散構成・Grafana不採用の方向、GitHub上の`4482ede`ではロガーの位置・音声がまだ出ないことの確認、こちらの宿題）
- `docs/share/ogata_share_YYYYMMDD_*.md`：緒方さん（GitHub `ktrogt`、走行戦略ツールを作っているチームメンバー）への返信。`docs/share/ogata_share_20261024_issues_reply.md`は緒方さんがChatGPTで出した「既存の不具合と注意点」（`existing-issues.md`）への確認結果と、ブリッジのWebSocketの読み口（`kind=clock`）の説明
- `docs/share/HANDOFF_2026*.md`・`docs/share/HANDOFF_*_20260915.md`：2026-09のVer.1（ESP32-S3）・EcoCaptureの作業の引継ぎ（09-02の統合、09-04のUX250h試験版、09-15のNCECへの反映・OBD限定送信・ファンの観測と暫定採用・状態表示）。当時の到達点の記録で、いまの正は`ARCHITECTURE.md`
- `docs/share/ROADSTER_INVESTIGATION_20260915.md`：NCECの実車調査（2026-09-15）のまとめ。CANの解釈のいまの正は`docs/design/ncec_can_spec.md`
- `docs/share/UNOQ_Defi電圧入力対応_引継ぎ.md`：Lintarohさんが書いた、UNO QをPIC v8のDefi電圧入力（PRESS・TEMP1・TEMP2）に対応させる引継ぎ（2026-11-01）。こちらの受け取り側はSG-4-3

## `docs/design/` — 仕様・設計

- `docs/design/lineage_racecapture.md`：**RaceCaptureからの系譜**（何を使って始め、いつ何を自前に置き換えたか）と、Ver.2のソフトに公式ファーム・公式アプリ・Ver.1のコードの写しが無いかを突き合わせた結果、ライセンスの扱いの案（SP-9-1〜9-3、2026-11-13。決めるのはユーザー）
- `docs/design/pc_app_requirements.md`：PCの道具が前提にしているもの（Pythonの版・外のパッケージ・adb・ssh・ffmpeg）の一覧と、ほかの人のPCへの入れ方の案（SP-3-10、2026-11-13。pip用の一覧は`tools/requirements.txt`）
- `docs/design/ecologger_phone_mock.html`：**スマホで開くピット用の入口（自宅のサーバーのページ）の案の見本**（SP-6-1、2026-11-13。動かない。数字は例）。場面（準備中・ピット・走行中・油温の警告・値が届かない）と見ている人（見るだけ・係）を切り替えて確かめる。Claudeのページにも載せてある
- `docs/design/ecologger_app_mock.html`：**PCのEcoLoggerアプリを1つにまとめる案の見本**（SP-3-1、2026-11-13。動かない。数字と走行は例）。上にいつも「つながり」の帯、その下に「いまの様子・回収・走行を見る・設定（開発者）」の4段。場面を切り替えて、つながり方ごとの見え方を確かめる。Claudeのページにも載せてある（同じファイルを出し直すと更新）
- `docs/design/hardware_interface_spec.md`：電気・回路系担当の友人と認識合わせをするための入出力インターフェース仕様書
- `docs/design/ncec_can_spec.md`：NCEC（本番車両）のCAN通信仕様（ID・バイトマップ・デコード式・OBD2）。実装・共有用の独立ファイル
- `docs/design/sensorhub_defi_tap_design.md`：既設Defiの油温・油圧センサーを読むセンサーハブ基板の設計（v2：油温はサーミスタを直接測りデジタルポテンショメータでDefiへ再現、ピン単位の接続表・LCSC品番つき部品表・換算式・校正手順）。使用サーミスタの特性は`datasheet/defi_temp_sensor_rt.csv`
- `docs/design/analysis_map_features.md`：**解析アプリの地図の上での解析・比べの仕様**（SP-10-12〜10-17、2026-11-15）。線を値・タイムの差で塗る、コーナーごとの区間の表と理論ベスト、測位から計算する旋回半径と摩擦円、物差しと線の横のずれ、車を追う再生、別の日の線のずれ。SUGO 11/8 の3周での下見の数と、ほかの解析ソフト（AiM・MoTeC・Circuit Tools など、Garmin Catalyst は米国特許まで、RaceChrono・Harry's LapTimer は作者のフォーラムまで）の地図まわりの比べつき
- `docs/design/brake_pressure_sensor_ncec.md`：NCECの**ブレーキ圧センサー**の候補（AiM M10、0-100/0-160 bar）とロガー側のつなぎ方。**電源が8〜16Vで、センサーハブの5Vでは動かない**点に注意。付ける場所・継手は車両リポジトリ（ncec-roadster）の`maintenance/reliability-plan.md` 2-2が正
- `docs/design/ecorun_team_systems.md`：エコランチーム（GitHub組織`TMCIT-Ecorun`）の既存システム（フロントパネル・通話試作・ダッシュボード）とEcoLoggerの関係、通話・中継サーバーの構成方針。**チーム側リポジトリは読むだけで変更しない**（例外：`ecorun-logger-server`はMaruo.Sさんの依頼でブランチ＋PRで変更する。2026-10-14〜）
- `docs/design/enclosure_ecorun_20261024.md`：エコラン大会用の3Dプリント筐体の設計材料（Ver.2・Ver.1の基板寸法と縁の部品位置、STEPの場所、要件、未確定事項）。耐衝撃の考え方は`docs/design/case_shock_design.md`
- `docs/design/er12_mpp_soc_harness_bom.md`：EV二輪のMPP充電器からSOCを読む測定用ハーネスの部品表（秋月版・千石版）と結線表（ER-12）
- `docs/design/unoq_software_inventory.md`：本体のソフト（`RaceCapture-UNOQ/`・`EcoCapture-Web/`）を「いま動いているもの／公式アプリ用／通話／試験／古い候補」に分けた一覧（2026-11-13、SP-2-4）。公式アプリを外すとき（SP-7-3）の材料。本体で有効かどうかは「要確認」のまま
- `docs/design/logger_v2_channel_and_sensor_spec.md`：Ver.2への入力・出力チャンネルの仕様（回路担当の宿題6・7・8。外部CANのチャンネルごとの用途、油温・油圧センサーの選定、追加で記録したい車体の信号）。外部CANのID割り当て表の正は`sensorhub_generic_spec.md`
- `docs/design/logger_v2_gnss_i2c_design.md`：Ver.2のGNSSをI²C（DDC）にしてIMUとバスを分け合う設計メモ（回路担当の宿題1・2）

## `docs/manual/` — 手順書

- `docs/manual/day_manual_template.html`：**当日用A4手順書のひな形**（SP-8-1、2026-11-13）。新しい大会の手順書は、これを写して【 】の所を書き換える
- `docs/manual/pit_cover_phone.md`：ピットの表紙をスマホで使う手順（開く・ホーム画面に置く・合言葉をQRで入れる・操作を送る。SP-6-4、2026-11-13。アドレスは書いていない）
- `docs/manual/ecorun_day_manual_20261024.html`：エコラン大会の当日用A4手順書（取付・記録の確認・コースウォーク・停止・回収・困ったとき）。ブラウザでA4縦に印刷する。回収は`tools/collect_logs/Collect-Logs.cmd`
- `docs/manual/sugo_day_manual_20261108.html`：SUGOの当日用A4手順書（SG-5-1、**10/30の下書き**。11/5に警告の数値などを入れて仕上げる）。Ver.2をSUGO用の設定へ切り替える道具とラップのリセットは`tools/sugo_setup/`（`sugo_setup.py`・`Reset-Laps.cmd`）。PIC v8の電圧（`PressVolt`・`Temp1Volt`・`Temp2Volt`、0x580）を信号に登録する道具も同じ場所の`defi_volt_setup.py`（既定は確かめるだけ、`--apply`で登録）。その電圧からDefiの油温・水温を℃にする（`OilTemp`をTEMP2へ差し替え、`WaterTempDefi`を足す）のは`defi_temp_setup.py`（`--pullup`でDefi内部の抵抗を変える）。セクターのタイム（2026-11-07）を本体（`lap.py`・DASH）と5B（タイム表）へ入れるのは`install_sectors.py`（既定は確かめるだけ、`--apply`で本体、`--server`で5B）
- `docs/manual/android_circuit_handoff_20261104.md`：予備の車載画面（EcoLoggerアプリの「サーキット」、SG-2-8）を、DASHの油圧の警告・同時表示・1分の点滅・約10秒の警報音に合わせた分の引継ぎ。**PCでやること**（Gradleでのビルドと試験86件、エミュレーターで`circuit_mock.py`の`press=70`などを見る、スマホへの導入、本体への`field.py`）と、DASHと違うところ
- `docs/manual/rename_local_folder.md`：このPCの作業フォルダー名を`RaceCapture`から`EcoLogger`へ変える手順（SP-9-9。古い名前を通り道として残す、Claudeの記憶を写す、ショートカットを作り直す、戻し方）。**まだ実行していない**
- `docs/manual/ecologger_system_overview.html`：EcoLoggerの全体像（エコラン大会、2026-10時点）。チーム向けの1枚
- `docs/manual/ecologger_troubleshooting.html`：困ったときの手順集（ロガー担当向け、エコラン大会の頃の構成）
- `docs/manual/ecorun_flow_20261024.html`：エコラン全国大会の出発前〜帰宅後の流れ
- `docs/manual/ncec_field_procedure.md`・`docs/manual/mazda2_field_procedure.md`・`docs/manual/lexus_ux_field_procedure.md`：Ver.1の頃の自作CAN解析基板（XIAO ESP32C3＋MCP2562FD）での実車CAN・OBD2の現地手順書（NCEC・MAZDA2・レクサスUX）。**NCECの前は`ncec_next_session_checklist.md`を先に開く**
- `docs/manual/podium_auto_link_test_plan.md`：Podium送信のWi-Fi⇔LTE自動切替の実機試験計画（ER-1-6、2026-10-15）

## `docs/research/` — 調査

- `docs/research/analysis_export_formats_20261113.md`：解析ソフトへ走行記録を書き出す形式の調査（MoTeC i2の`.ld`、RaceLogicの`.vbo`ほか。SP-5-5、2026-11-13。まだ何も作っていない。形式を決めるのはユーザー）
- `docs/research/analysis_software_survey_20261114.md`：自作ロガーのデータを使用許諾の問題なく開ける既存の解析ソフトの比べ（2026-11-14。TrackDataAnalysis・Circuit Tools・WinDarab Free・RaceChrono Proほか、動画の同期の道具）。どのソフトもこちらのデータで開く確かめはしていない。この報告のあと解析は自前のアプリ（SP-10）にした。元のメモは`docs/research/analysis_software_survey_20261114_notes/`
- `docs/research/digspice_analysis_study_20261115.md`：デジスパイスの解析ソフトの調べ（SP-10、2026-11-15）。地図の上の機能（減速は点線・物差し・4台のアニメーション・セクター）、GPSから計算するGと旋回半径・摩擦円、コーナーごとの仮想区間という見方、解析アプリとの比べと、地図の上での解析を強くする案6つ。今の版（Ver4.8.0）の説明書で確かめ直した表つき。ドリフト角（iPhoneの姿勢センサーと測位から出す。普通のログには入らない）と採点は7.1。仕様にしたものは`docs/design/analysis_map_features.md`
- `docs/research/phone_lap_accuracy_20261115.md`：スマホ（測位1Hz）の周のタイムがどれだけ正しいか（SP-7-7、2026-11-15）。数え方は変えない（誤差はスマホの位置のゆっくりしたずれで、エコランの速さで約0.2〜0.3秒）
- `docs/research/defi_sensor_curves_research.md`：Defiの油圧・温度センサーの電圧特性の調べもの（Defiは公式に非公開。海外フォーラムの実測表・個人サイトのメーター換算・公式のコネクター色を集め、2026-11-03〜04の実測と照合）。油圧は P[kPa]≒250×(V−V0)、温度はβが高温ほど大きい
- `docs/research/LOGGER_V2_UNOQ_REPORT.md`：Ver.2（UNO Q）のGNSS選定とセンサーフュージョンの構想（回路担当への共有用）。7章の`E-x`はVer.2の判断の記録（`ARCHITECTURE.md` 5章冒頭の表）
- `docs/research/LOGGER_V2_LTE_MODEM_REPORT.md`・`docs/research/LOGGER_V2_LTE_MODEM_QUESTIONS.md`：LTEモデム（SIM7070G）の評価と、回路担当への相談メモ（2026-09）
- `docs/research/logger_v2_lte_sim_survey.md`：日本とドイツの両方で使えるLTE-MのSIMの調べ（回路担当の宿題9）
- `docs/research/OBD2_SURVEY.md`：ELM327での実車のOBD2プロトコル・PIDの調査記録（Phase 2-0の一次資料、「NCEC 追補」に実測）
- `docs/research/vehicle_can_survey_summary.md`：実車のCAN・OBD2で測った事実だけの1枚（回路担当への共有用）
- `docs/research/lap_detection_survey_20261014.md`：ラップ判定の比べ（RaceCapture・RaceChrono・Ver.2の`lap.py`、ER-2-4）。RaceCaptureのファームはGPLv3なので考え方だけ取り込んだ
- `docs/research/podium_connect_notes.md`：Podium・Podium Connectで分かっていること・未確認のこと（Ver.2で使う検討用）
- `docs/research/ecorun_final_plan_20261023.md`：エコラン大会の出発前〜当日のロガーの計画（優先順位：記録＞ピット＞ラップ＞音声＞油温）
- `docs/research/test_drive_20261024_night.md`：10/24夜の試験走行（ピット画面の修正ER-8-10の確かめ。ER-11-21でアプリを変えたときも同じ手順）
- `docs/research/ecorun_race_20261025_supercub_timeout.md`：大会2日目のスーパーカブの規定時間オーバーの振り返りと対策案（ER-13、読み取りだけで調べた）
