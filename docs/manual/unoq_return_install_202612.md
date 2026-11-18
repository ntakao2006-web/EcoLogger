# 本体（UNO Q）が戻ったら：確かめる・控える・まとめて入れる・戻す（2026-12、TS-2）

> 2026-11-19作成（作手の走行会 12/5 向け、`task_tsukude_20261205_breakdown.md` TS-2-1・TS-2-2）。
> 本体は11月いっぱい貸し出し中。戻ったら（12/1ごろ）この順に進める。**12/2の夜が切り時**（終わらなければ「6. 戻す」で展示の前の形へ戻し、作手はその版で走る）。
> 入れてよい了承は2026-11-16にもらってある（「まとめて入れて」）。入れる前に改めて聞かず、入れることだけ一言伝える。**走行中・走行の直前は入れない。**

## 0. 入れるもの・入れないもの

| 順 | もの | どこ | 中身 | 了承 |
|---|---|---|---|---|
| A | EcoCapture | Linux（`~/EcoCapture-Web`、`deploy.sh`） | SP-4-8（LTEでコースを選ぶ・線を入れる）、SP-9-4（Podiumへ直接送る道を外す）、SP-7-2（スマホへ送信の印）、11/14の線を変えたら走っている周を捨てる直し、11/16の設定の保存が422になる直し、SDの種類5〜8を読み解く`sd_decode.py` | 済み |
| B | 車載画面DASH | Linux（`/opt/logger-v2-racecapture`） | SP-7-1（「送信」の印） | 済み |
| C | 焼き込み録画 | Linux（`/opt/ecologger-video`） | 針の補間の直し（1660783） | 済み |
| D | STM32のファーム | STM32 | **SP-7-8**（測位の補強の出どころをSDへ、静的集計 129,293 B） | 済み |
| E | コースの設定 | Linux（`<データ>/setups/courses/`と線） | SP-4-3（`setups_apply.py`）。作手の線は12/4に | 済み |
| ― | SP-11（ECUへのOBDの問い合わせ） | STM32 | **入れない**（作手の前に入れるかはユーザーが決める。TS「判断」2） | 未 |
| ― | 自宅のサーバー（5B） | 5B | 入れない（入れる前に聞く） | 未 |

- **いまのmasterのファームにはSP-11が入っている**（11/17のbd01a87。切り替えのスイッチは無い）。SP-7-8だけを入れるときは、**SP-11の1つ前のコミット`9b5ec57`のファームのソースで組む**（`firmware/ecologger_v2/`の`.h`・`.ino`は`e392d79`と同じ。間のコミットは試験台と資料だけ）
  - 組み方：`git archive 9b5ec57 firmware/ecologger_v2 | tar -x -C <作業の置き場>` で取り出し、そこで組む。WSLの中でgitを動かさない
- Aはmasterのままでよい。SP-11の分はOBDの状態の表示と読み解きだけで、SP-7-8のファームでは「（受信専用）」と出る。ただし**設定の保存の知らせ（`server.py`）と設定の画面のNCECの説明（`web/index.html`）は「OBDの問い合わせを送る」と書いてある**。SP-11を入れないなら、Aを入れる前にこの2か所の文を前の文（bd01a87^の版）に戻す

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
| B | DASHの試験を本体の`/tmp`で流し、通ったら`dash_model.py`・`ecocapture_dash.py`を入れて`systemctl restart ecocapture-dash`（画面が約5秒消える） | `/opt/logger-v2-racecapture/*.pre-<日時>` |
| C | `tools/unoq_overlay_enc/`の一式を送り、PCとSHA-256を照らして、rootで`install-video.sh <置き場>`（録画が一度切れる）。詳しくは`unoq_video_check_procedure.md` 5-24の2026-11-16追記 | `/opt/ecologger-video/overlay_rec`・`run-video.sh`を`*.pre-drift-<日付>` |
| D | 本体の`~/ecologger_v2/`を写して残し、`9b5ec57`のソースを`/tmp`で組む → `image-audit.json`の静的集計がPCの`sh firmware/ecologger_v2/build_pc.sh`（129,293 B）と同じか見る（**違えば書かずに調べる**）→ `flash-mcu.sh`で書く（11/11のSDの目次の直しと同じ手順。`ARCHITECTURE.md` 4章の2026-10-09・2026-11-11の追記。決まった順番で書かないとLinux側のUARTが固まる） | 今の像`~/ecologger_v2_sdfix_20261111.bin`（7066c1b7…） |
| E | `python tools/setups/setups_apply.py --vehicle ncec --course sugo`で確かめるだけ → 違いを見てから`--apply`（車の信号が違えば記録を止めて入れ直すので、走行記録のファイルが分かれる）。作手の線は12/4に`--course tsukude --apply` | 本体の`lap.json.bak-<日時>`・`config.json.bak-<日時>-before-setup`、PCの`%USERPROFILE%\.ecologger\config-backups\` |

## 4. 1つ入れるたびに見ること

- `/api/status`：`connected: true`、受信約100Hz、`mcu_resets`が増えない、記録の行が増える、SDが「記録中」
- A：LTEの送り先が中継（自宅の5B）のままで、5Bに値が届く（送信のON/OFFは変えていない）
- B：モニターに画面が出て、下の段に「送信」の印がある
- C：1分後のjournalの`smooth:`で`mcu_clock_slow`が約+2600、`wait`が150 msに張りつかない。空ぶかしで針が動くか（音が出るので先に予告する）
- D：SDの記録を`sd_decode.py`に通し、`.gnss.jsonl`に種類5・6が出る。しばらく動かしてから`/api/status`の`hardware.sd_queue_max`を読む
- 全部入れたら：机の上で30分つけっぱなしにし、記録・画面・録画・LTEが止まらないか

## 5. 入れたら記録する

- 入れた日時・版・確かめた数字を、`task_spec_rebuild_breakdown.md`の各項目（SP-4-3・4-8・7-1・7-2・7-8・9-4）、`unoq_video_check_procedure.md` 5-24、`firmware/ecologger_v2/README.md`、`ARCHITECTURE.md` 4章、`task_tsukude_20261205_breakdown.md` TS-2-2に書いてコミット・push

## 6. 戻す（切り時を越えたとき、入れたあとに不具合が出たとき）

- 1つだけ戻すなら、3の表の右の控えから戻す（A：控えのファイルを戻して`deploy.sh`、B：`*.pre-<日時>`を戻して再起動、C：`*.pre-drift-<日付>`を戻してサービスを再起動、D：`~/ecologger_v2_sdfix_20261111.bin`を`flash-mcu.sh`で書く、E：`lap.json.bak`・`config.json.bak`）
- **展示の前の形へ丸ごと戻すなら**、`v2_firmware_backup_20261110.md` 4章。ただしファームは**11/10の控え（e3501ec7）ではなく11/11の`ecologger_v2_sdfix_20261111.bin`（7066c1b7）**へ戻す（11/10の版にはSDの目次の不具合がある）
- 戻したら1-2・1-3と同じ確かめをする
