// GNSSアンテナ（JCA002）ロールバー用マウント
// ------------------------------------------------------------
// 座標：X = ロールバーと直角（車幅方向など）、Y = ロールバーの軸方向（+Y側へケーブルが出る）、
//       Z = 上。ロールバーの頂上が Z=0、中心が Z=-R。
// 考え方：アンテナの底に最初から付いている両面テープ（フォーム、約1mm）を、
//       ロールバーの頂上に直接（線で）当てる。ポケットの底はロールバーの頂上より
//       ant_tape_crush だけ低い平面で、真ん中に窓があってロールバーの頂上が出ている。
//       アンテナを押し込むと、テープはポケットの底の左右に貼り付き、真ん中の線で
//       ロールバーに ant_tape_crush だけ押し付けられる（これが位置決めと回り止め）。
// 固定：結束バンド2本（-Y側のタブ、+Y側の舌でケーブルごと）。アンテナの下にはバンドを通さない。
//       側壁の中央の溝を使って、アンテナの上からもう1本回すとテープがしっかり押し付けられる。
// 角R：平面で見た角は、ポケットの内側と本体の外側を同じ中心の円弧にしている（外R＝内R＋壁厚）。
// 印刷：-Y の端面（タブの先）を下にして立てて印刷する。サポートは基本不要。
// 寸法の出典：JCA002データシート（45.2×35.8×15.2mm、RG174、SMA-P）。
//            ケーブル口（ブッシュ）の寸法・底のテープの厚さは図に無いので「要実測」の初期値。
// ------------------------------------------------------------

/* [ロールバー] */
bar_d    = 40;   // ロールバーの外径[mm]。ここを変えれば全体が追随する
bar_clr  = 0.3;  // 半径方向のすきま[mm]
wrap_deg = 40;   // 頂上から片側へ抱え込む角度[°]（大きいほどしっかり、ただし厚くなる。90未満）

/* [アンテナ JCA002] */
ant_l = 45.2;      // ケーブル方向の長さ（データシート 45.2±0.3）
ant_w = 35.8;      // 幅（データシート 35.8±0.3）
ant_h = 15.2;      // 高さ（データシート 15.2±0.3）※プレビュー用
ant_clr = 0.4;     // ポケットのすきま（片側）
ant_corner_r = 4;  // ポケットの角R（アンテナの角Rより小さくしておけば当たらない）。外側はこれ＋壁厚
pocket_depth = 3.5;// ポケットの深さ（ポケットの底から壁の上端まで）
ant_tape_t = 1.0;  // アンテナの底に最初から付いている両面テープの厚さ ※要実測（1mm前後の記憶）
ant_tape_crush = 0.2; // 圧着代：ロールバーの頂上がポケットの底より出る量＝テープが線で潰れる量
grommet_w = 7.0;   // ケーブル口（ブッシュ）の幅  ※要実測
grommet_l = 3.0;   // ブッシュが本体端面から出っ張る長さ ※要実測
cable_d = 2.8;     // RG174の外径（公称2.8）
cable_h = 2.5;     // アンテナの底面からケーブル中心までの高さ ※要実測

/* [結束バンド] */
tie_w   = 4.8;   // バンド幅（4.8mm幅の一般品。2.5mm幅なら2.5）
tie_clr = 0.4;   // 溝のすきま
top_tie_notch = true; // アンテナの上を回す1本用の溝を側壁に付ける

/* [本体] */
wall     = 2.0;  // ポケットの壁厚
floor_min = 1.2; // ポケットの底の最小の厚さ（これより薄くなる真ん中は窓にする）
tab_len  = 10;   // -Y側のタブの長さ
tab_top  = 2.0;  // タブの上面の高さ（ロールバーの頂上から）
tail_len = 22;   // +Y側（ケーブル側）の舌の長さ
tail_w   = 14;   // タブ・舌の幅
tail_corner_r = 3; // タブ・舌の先の角R

/* [表示] */
show_preview = false; // trueでアンテナとロールバーを重ねて表示（STL出力時はfalse）

$fn = 128;
eps = 0.01;

// ---- 導出値 ----
R      = bar_d/2 + bar_clr;                  // 鞍の内半径
flank_t = 3.0;                               // 抱え込み部の厚さ
sag    = R * (1 - cos(wrap_deg));            // 抱え込み部の下端（頂上から下へ）
z_pf   = -ant_tape_crush;                    // ポケットの底（ロールバーの頂上より少し低い）
z_top  = z_pf + pocket_depth;                // 壁の上端
pk_l   = ant_l + 2*ant_clr;                  // ポケット内寸
pk_w   = ant_w + 2*ant_clr;
Lb     = pk_l + 2*wall;                      // 本体の外寸
Wb     = pk_w + 2*wall;
r_out  = ant_corner_r + wall;                // 外側の角R（内側と同じ中心）
win_hw = sqrt(R*R - pow(R + z_pf - floor_min, 2)); // 窓の半幅（底が floor_min より薄い所）
cable_z = ant_tape_t + cable_h;              // ポケットの底からケーブル中心までの高さ
z_tt   = z_pf + cable_z;                     // 舌の上面（ケーブルの中心の高さ）
y_tail_end = Lb/2 + tail_len;
y_tab_end  = -Lb/2 - tab_len;
tw     = tie_w + tie_clr;                    // バンド溝の幅
y_tie_tail = y_tail_end - 4 - tw/2;          // 舌のバンドの位置
y_tie_tab  = (y_tab_end - Lb/2)/2;           // タブのバンドの位置（タブの中央）

echo(str("鞍の内半径 R=", R, "  本体 ", Wb, " x ", Lb + tail_len + tab_len, " x 高さ ", sag + z_top,
         " mm  ポケット底 z=", z_pf, "  窓の幅 ", 2*win_hw, "  アンテナ底面 z=", z_pf + ant_tape_t));

// XZ断面（2D：xがX、yがZ）
module section(ztop, half_w) {
    difference() {
        intersection() {
            hull() {
                translate([-half_w, 0]) square([2*half_w, max(ztop, eps)]);
                intersection() {
                    translate([0, -R]) circle(r = R + flank_t);
                    translate([-500, -sag]) square([1000, 1000]);
                }
            }
            translate([-half_w, -500]) square([2*half_w, 500 + ztop]);
        }
        translate([0, -R]) circle(r = R);
    }
}

// 断面をY方向に押し出す（y0〜y1）
module extrude_y(y0, y1) {
    translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(height = y1 - y0) children();
}

module rr2d(l, w, r) {   // 角Rの長方形（X=w, Y=l、中心基準）
    offset(r = r) square([w - 2*r, l - 2*r], center = true);
}

// 平面で見た外形を縦に押し出したもの（中心 y0）
module plan_clip(l, w, r, y0 = 0) {
    translate([0, y0, -500]) linear_extrude(height = 1000) rr2d(l, w, r);
}

// タブ・舌：y_root（本体側）から y_end（先端）まで。先端の角だけR
module arm(y_root, y_end, ztop) {
    y0 = min(y_root, y_end); y1 = max(y_root, y_end);
    len = y1 - y0 + tail_corner_r;
    yc = (y_end > y_root) ? (y0 + y1 + tail_corner_r)/2 : (y0 + y1 - tail_corner_r)/2;
    intersection() {
        extrude_y(y0, y1) section(ztop, tail_w/2);
        plan_clip(len, tail_w, tail_corner_r, yc);
    }
}

// バンドの位置決め：タブ・舌の両側面の深さ0.8の溝
module side_notches(y, ztop) {
    for (s = [-1, 1])
        translate([s * tail_w/2 - 0.8, y - tw/2, -R]) cube([1.6, tw, R + ztop + 1]);
}

module mount() {
    difference() {
        union() {
            intersection() {                                   // 本体
                extrude_y(-Lb/2, Lb/2) section(z_top, Wb/2);
                plan_clip(Lb, Wb, r_out);
            }
            arm(Lb/2 - r_out, y_tail_end, z_tt);               // +Y：ケーブル側の舌
            arm(-Lb/2 + r_out, y_tab_end, tab_top);            // -Y：タブ
        }
        // アンテナのポケット
        translate([0, 0, z_pf]) linear_extrude(height = 50) rr2d(pk_l, pk_w, ant_corner_r);
        // 窓：ロールバーの頂上を出して、アンテナのテープを直接当てる（ポケットの長さいっぱい）
        translate([-win_hw, -pk_l/2 + ant_corner_r, -R]) cube([2*win_hw, pk_l - 2*ant_corner_r, R + z_pf + eps]);
        // ケーブル口：+Y側の壁をブッシュ幅で切り欠く（上から差し込めるように上まで開ける）
        translate([-grommet_w/2, pk_l/2 - eps, z_pf]) cube([grommet_w, wall + grommet_l + eps, 50]);
        // 舌の上のケーブル溝
        translate([0, Lb/2 - 1, z_tt]) rotate([-90, 0, 0]) cylinder(d = cable_d + 0.6, h = tail_len + 2);
        // バンドの位置決め
        side_notches(y_tie_tail, z_tt);
        side_notches(y_tie_tab, tab_top);
        // アンテナの上を回すバンド用：側壁の外面の溝と、上端の切り欠き（深さ1）
        if (top_tie_notch) {
            for (s = [-1, 1])
                translate([s * Wb/2 - 0.8, -tw/2, -R]) cube([1.6, tw, R + z_top + 1]);
            translate([-Wb/2 - 1, -tw/2, z_top - 1]) cube([Wb + 2, tw, 2]);
        }
    }
}

// ---- プレビュー用の部品 ----
module antenna_dummy() {
    translate([0, 0, z_pf]) {
        color("white") linear_extrude(height = ant_tape_t) rr2d(ant_l - 2, ant_w - 2, 4);   // 底のテープ
        color("#222") translate([0, 0, ant_tape_t]) {
            hull() {
                linear_extrude(height = 4) rr2d(ant_l, ant_w, 5);
                translate([0, 0, ant_h - 1]) linear_extrude(height = 1) rr2d(ant_l - 10, ant_w - 10, 4);
            }
            translate([0, ant_l/2, cable_h]) rotate([-90, 0, 0]) cylinder(d = 6, h = grommet_l);
            translate([0, ant_l/2, cable_h]) rotate([-90, 0, 0]) cylinder(d = cable_d, h = 60);
        }
    }
}
module bar_dummy() {
    color("silver", 0.6) translate([0, 0, -bar_d/2]) rotate([90, 0, 0])
        cylinder(d = bar_d, h = 160, center = true);
}

if (show_preview) {
    color("orange") mount();
    antenna_dummy();
    bar_dummy();
} else {
    mount();
}
