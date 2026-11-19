# 本体（UNO Q）が戻ったら：確かめる・控える・まとめて入れる・戻す（2026-12、TS-2）

> 2026-11-19作成（作手の走行会 12/5 向け、`task_tsukude_20261205_breakdown.md` TS-2-1・TS-2-2）。
> 本体は11月いっぱい貸し出し中。戻ったら（12/1ごろ）この順に進める。**12/2の夜が切り時**（終わらなければ「6. 戻す」で展示の前の形へ戻し、作手はその版で走る）。
> 入れてよい了承は2026-11-16（「まとめて入れて」）と、SP-11は2026-11-19（「作手の前に入れる」）にもらってある。入れる前に改めて聞かず、入れることだけ一言伝える。**走行中・走行の直前は入れない。**

## 0. 入れるもの・入れないもの

| 順 | もの | どこ | 中身 | 了承 |
|---|---|---|---|---|
| A | EcoCapture | Linux（`~/EcoCapture-Web`、`deploy.sh`） | SP-4-8（LTEでコースを選ぶ・線を入れる）、SP-9-4（Podiumへ直接送る道を外す）、SP-7-2（スマホへ送信の印）、11/14の線を変えたら走っている周を捨てる直し、11/16の設定の保存が422になる直し、SDの種類5〜8を読み解く`sd_decode.py` | 済み |
| B | 車載画面DASH | Linux（`/opt/logger-v2-racecapture`） | SP-7-1（「送信」の印）。**見た目の作り直し（SP-12、2026-11-19）は含まない**：了承が出るまでは、DASHの2ファイルは`7647120`の版を入れる | 済み（SP-12は未） |
| C | 焼き込み録画 | Linux（`/opt/ecologger-video`） | 針の補間の直し（1660783） | 済み |
| D | STM32のファーム | STM32 | masterの版：**SP-7-8**（測位の補強の出どころをSDへ）＋**SP-11**（ECUへのOBDの読むだけの問い合わせ、`SPEC.md` G-5）。静的集計 130,265 B | 済み（SP-11は11/19「作手の前に入れる」） |
| E | コースの設定 | Linux（`<データ>/setups/courses/`と線） | SP-4-3（`setups_apply.py`）。作手の線は12/4に。**車の設定（`--vehicle ncec`）には了承がまだの2つが入っている**：DASHの目盛り40（SP-12）と、信号`Pedal`・`Brake`（SP-13、焼き込みの足の動き）。了承が出るまでは`--vehicle`を付けず、コース（`--course`）だけ入れる | 済み（車の設定のSP-12・SP-13の分は未） |
| ― | 自宅のサーバー（5B） | 5B | 入れない（入れる前に聞く） | 未 |

- Dは**2つの像を本体で組んでおく**：①masterのソース（SP-7-8＋SP-11、130,265 B）＝入れる像、②SP-11の1つ前のコミット`9b5ec57`のソース（SP-7-8だけ、129,293 B）＝**SP-11だけを外す戻し先**。
  車でOBDの問い合わせに何か出たら、②を書けば測位の補強の記録は残したまま、CAN1は前と同じ受信だけに戻る
  - 2026-11-19にPCで両方を組んで確かめた：①静的集計 130,265 B・像 59,952 B、②129,293 B・58,248 B（どちらも記録どおり）。①は起動を確かめた130,365 Bまで100 Bしかない
  - ②の取り出し方：`git archive 9b5ec57 firmware/ecologger_v2 | tar -x -C <作業の置き場>`（`.h`・`.ino`はSP-7-8の`e392d79`と同じ。間のコミットは試験台と資料だけ）。WSLの中でgitを動かさない
- Aはmasterのまま（SP-11のOBDの状態の表示と`<CSV>.obd.jsonl`への読み解きが入っている）

## 1. つなぐ・今の形を確かめる（TS-2-1。何も変えない）

1. USBのadb（シリアル`2954148814`）か、Pixelのテザリングで`ssh unoq`。ドックは起動の前につなぐ
2. STM32を止めずに読み出し、アプリの領域のハッシュを比べる（`v2_firmware_backup_20261110.md` 5章のコマンド）
   - `7066c1b7…`（11/11のSDの目次を直した版）なら、展示の前の形のまま
   - `e3501ec7…`（11/10の控え、SUGOを走った版）なら、11/11の書き込みが無かったことになっている。理由を調べてから進む
   - **どちらでもない・土台（先頭0x3A000バイト）まで変わっている**なら、展示用に書き換えられている。**そこで止めてユーザーに聞く**（`v2_firmware_backup_20261110.md` 4-2）
3. Linux側：`/api/status`で`connected: true`・受信約100Hz・`mcu_resets`が増えない・記録の行が増える。サービスの有効/無効が控えの`inventory.txt`と同じか
4. 本体の`~/EcoCapture-Web`・DASH・録画のファイルが、リポジトリのどれかの版と同じか（本体で直された版を上書きしないため。`tools/sugo_setup/install_sectors.py`の確かめと同じ考え方）

## 2. 控えを取る（入れる前に必ず）

- 11/10と同じ取り方で丸ごと控える（`v2_firmware_backup_20261110.md` 1〜2章）。置き場は`Documents\UNOQ_fw_backup\<日付>\`とNAS。`SHA256SUMS.txt`を作ってNASと照らす
- 控えは**リポジトリに入れない**（合言葉・SIMの設定・sshの鍵が入る）

## 3. 入れる（1つずつ。1つ入れたら4の確かめをしてから次へ）

| 順 | 入れ方 | 戻す用の控え |
|---|---|---|
| A | リポジトリの`EcoCapture-Web/`を本体へ送り、`deploy.sh`（本体で試験を全部流し、落ちたら作り直さないので前のまま動き続ける）。記録は止めなくてよい（途切れは作り直しの十数秒） | `~/EcoCapture-Web/.bak-<日時>/`、イメージ`ecocapture-web:pre-<日時>` |
| B | **masterのDASHは見た目を作り直した版（SP-12、了承がまだ）なので、`git show 7647120:RaceCapture-UNOQ/ecocapture_dash.py`・`dash_model.py`・`test_dash_model.py`で前の版を書き出して使う**（SP-12の了承が出ていればmasterの版。そのときは`task_spec_rebuild_breakdown.md` SP-12-3の「入れる前に見る」も）。DASHの試験を本体の`/tmp`で流し、通ったら`dash_model.py`・`ecocapture_dash.py`を入れて`systemctl restart ecocapture-dash`（画面が約5秒消える） | `/opt/logger-v2-racecapture/*.pre-<日時>` |
| C | `tools/unoq_overlay_enc/`の一式を送り、PCとSHA-256を照らして、rootで`install-video.sh <置き場>`（録画が一度切れる）。詳しくは`unoq_video_check_procedure.md` 5-24の2026-11-16追記 | `/opt/ecologger-video/overlay_rec`・`run-video.sh`を`*.pre-drift-<日付>` |
| D | 本体の`~/ecologger_v2/`を写して残し、0の①②を`/tmp`で組む → `image-audit.json`の静的集計が、同じソースをPCの`sh firmware/ecologger_v2/build_pc.sh`で組んだ値（①130,265 B・②129,293 B）と同じか見る（**違えば書かずに調べる**。起動を確かめた上限は130,365 B）→ ①を `flash-mcu.sh`で書く（11/11のSDの目次の直しと同じ手順。`ARCHITECTURE.md` 4章の2026-10-09・2026-11-11の追記。決まった順番で書かないとLinux側のUARTが固まる） | 今の像`~/ecologger_v2_sdfix_20261111.bin`（7066c1b7…） |
| E | **SP-12・SP-13の了承が出ていなければ、`--vehicle ncec`を外してコースだけにする**（車の設定に、DASHの目盛り40と信号`Pedal`・`Brake`が入っているため。了承が出ていれば、そのまま入れてから`tools/video_hud/Apply-HUD.cmd`で焼き込みの設定も送る）。`python tools/setups/setups_apply.py --vehicle ncec --course sugo`で確かめるだけ → 違いを見てから`--apply`（車の信号が違えば記録を止めて入れ直すので、走行記録のファイルが分かれる）。作手の線は12/4に`--course tsukude --apply` | 本体の`lap.json.bak-<日時>`・`config.json.bak-<日時>-before-setup`、PCの`%USERPROFILE%\.ecologger\config-backups\` |

## 4. 1つ入れるたびに見ること

- `/api/status`：`connected: true`、受信約100Hz、`mcu_resets`が増えない、記録の行が増える、SDが「記録中」
- A：LTEの送り先が中継（自宅の5B）のままで、5Bに値が届く（送信のON/OFFは変えていない）
- B：モニターに画面が出て、下の段に「送信」の印がある
- C：1分後のjournalの`smooth:`で`mcu_clock_slow`が約+2600、`wait`が150 msに張りつかない。空ぶかしで針が動くか（音が出るので先に予告する）
- D（机の上、CAN1に何もつながない）：SDの記録を`sd_decode.py`に通し、`.gnss.jsonl`に種類5・6が出る。しばらく動かしてから`/api/status`の`hardware.sd_queue_max`を読む。
  **SP-11は送らないこと**：`logger.status`の`obd`が状態0（リッスンオンリーで待ち）・送った数0のまま、画面のCAN1が「（受信専用・OBD待ち）」
- D（車、SP-11-7。**最初は停車・アイドルで、走る前に**。12/3）：
  - `obd`が状態1（問い合わせ中）になり、送った数・一括の回数が増え、拒否した数が0
  - 受信は約100Hzのまま、CAN1のフレームの数が前と同じくらい、バスエラー0、SDの`sd_queue_dropped`が0
  - **車の警告灯・メーター・エンジンのかかり方に変化が無い**（キーを回し直しても同じ）
  - 状態2（送信エラーで受信だけに戻した）になった、または警告灯・メーターに何か出たら、**そこで止めて②（SP-11を外した像）を書く**。作手はその版で走る
  - 帰ってから`sd_decode.py`で`<CSV>.obd.jsonl`を作り、モード01の値・対応表・03/07の故障コード・09のCALIDが読めるか見る（VINは読まない）
- 全部入れたら：机の上で30分つけっぱなしにし、記録・画面・録画・LTEが止まらないか

## 5. 入れたら記録する

- 入れた日時・版・確かめた数字を、`task_spec_rebuild_breakdown.md`の各項目（SP-4-3・4-8・7-1・7-2・7-8・9-4・11-7）、`unoq_video_check_procedure.md` 5-24、`firmware/ecologger_v2/README.md`、`ARCHITECTURE.md` 4章、`task_tsukude_20261205_breakdown.md` TS-2-2に書いてコミット・push

## 6. 戻す（切り時を越えたとき、入れたあとに不具合が出たとき）

- 1つだけ戻すなら、3の表の右の控えから戻す（A：控えのファイルを戻して`deploy.sh`、B：`*.pre-<日時>`を戻して再起動、C：`*.pre-drift-<日付>`を戻してサービスを再起動、D：SP-11だけ外すなら②、ファームを丸ごと前へ戻すなら`~/ecologger_v2_sdfix_20261111.bin`を`flash-mcu.sh`で書く、E：`lap.json.bak`・`config.json.bak`）
- **展示の前の形へ丸ごと戻すなら**、`v2_firmware_backup_20261110.md` 4章。ただしファームは**11/10の控え（e3501ec7）ではなく11/11の`ecologger_v2_sdfix_20261111.bin`（7066c1b7）**へ戻す（11/10の版にはSDの目次の不具合がある）
- 戻したら1-2・1-3と同じ確かめをする
