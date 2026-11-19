// GNSSアンテナ（JCA002）ロールバー用マウント
// ------------------------------------------------------------
// 座標：X = ロールバーと直角（車幅方向など）、Y = ロールバーの軸方向（+Y側へケーブルが出る）、
//       Z = 上。ロールバーの頂上が Z=0、中心が Z=-R。
// 固定：結束バンド3本（アンテナの下を通す2本＋ケーブルを押さえる1本）。
//       上からもう1本かけたいときは、側壁の溝（top_tie_notch）でアンテナの上を回す。
//       鞍の面に両面テープ（車載用のフォーム、10mm角）を貼るくぼみがあり、仮止めと回り止めに使う。
// 角R：平面で見た角は、ポケットの内側と本体の外側を同じ中心の円弧にしている（外R＝内R＋壁厚）。
// 印刷：-Y の端面（ケーブルが出ない側）を下にして立てて印刷する。サポートは基本不要。
// 寸法の出典：JCA002データシート（45.2×35.8×15.2mm、RG174、SMA-P）。
//            ケーブル口（ブッシュ）の寸法は図に無いので「要実測」の初期値。
// ------------------------------------------------------------

/* [ロールバー] */
bar_d    = 40;   // ロールバーの外径[mm]。ここを変えれば全体が追随する
pad_t    = 0;    // 間に挟むゴムシートの厚さ[mm]（挟まないなら0）
bar_clr  = 0.3;  // 半径方向のすきま[mm]
wrap_deg = 40;   // 頂上から片側へ抱え込む角度[°]（大きいほどしっかり、ただし厚くなる。90未満）

/* [アンテナ JCA002] */
ant_l = 45.2;      // ケーブル方向の長さ（データシート 45.2±0.3）
ant_w = 35.8;      // 幅（データシート 35.8±0.3）
ant_h = 15.2;      // 高さ（データシート 15.2±0.3）※プレビュー用
ant_clr = 0.4;     // ポケットのすきま（片側）
ant_corner_r = 4;  // ポケットの角R（アンテナの角Rより小さくしておけば当たらない）。外側はこれ＋壁厚
pocket_depth = 3.5;// ポケットの深さ（アンテナを横から囲う高さ）
grommet_w = 7.0;   // ケーブル口（ブッシュ）の幅  ※要実測
grommet_l = 3.0;   // ブッシュが本体端面から出っ張る長さ ※要実測
cable_d = 2.8;     // RG174の外径（公称2.8）
cable_z = 3.5;     // ポケット底からケーブル中心までの高さ ※要実測（両面テープ厚込み）

/* [結束バンド] */
tie_w   = 4.8;   // バンド幅（4.8mm幅の一般品。2.5mm幅なら2.5）
tie_t   = 1.4;   // バンド厚
tie_clr = 0.4;   // 溝のすきま
tie_inset = 10;  // アンテナ下の2本の位置（ポケット端からの距離）
top_tie_notch = true; // アンテナの上を回す1本用の溝を側壁に付ける

/* [両面テープ（鞍の面）] */
tape_pads  = true; // 鞍の面にテープのくぼみを付ける（本体の中央と舌の2か所）
tape_size  = 10;   // テープの大きさ（正方形の1辺）
tape_t     = 1.1;  // テープの厚さ（車載用アクリルフォームは1.1mm前後が多い）
tape_crush = 0.2;  // 圧着代：くぼみから出っ張らせる量＝締めたときに潰れる量
tape_clr   = 0.5;  // くぼみの周りのすきま（片側）

/* [本体] */
wall    = 2.0;   // ポケットの壁厚
floor_t = 1.2;   // バンド溝の上に残す床の厚さ
tail_len = 22;   // ケーブル側へ伸ばす舌の長さ
tail_w   = 14;   // 舌の幅
tail_corner_r = 3; // 舌の先の角R
drain    = true; // ポケットの水抜き（-Y側の壁の下に切り欠き）

/* [表示] */
show_preview = false; // trueでアンテナとロールバーを重ねて表示（STL出力時はfalse）

$fn = 128;
eps = 0.01;

// ---- 導出値 ----
R      = bar_d/2 + pad_t + bar_clr;          // 鞍の内半径
Rt     = R + tie_t + tie_clr;                // バンド溝の外半径
flank_t = tie_t + tie_clr + 2.0;             // 抱え込み部の厚さ（溝の外に2mm残す）
sag    = R * (1 - cos(wrap_deg));            // 抱え込み部の下端（頂上から下へ）
z_pf   = tie_t + tie_clr + floor_t;          // ポケット底の高さ
z_top  = z_pf + pocket_depth;                // 壁の上端
pk_l   = ant_l + 2*ant_clr;                  // ポケット内寸
pk_w   = ant_w + 2*ant_clr;
Lb     = pk_l + 2*wall;                      // 本体の外寸
Wb     = pk_w + 2*wall;
r_out  = ant_corner_r + wall;                // 外側の角R（内側と同じ中心）
z_tt   = z_pf + cable_z;                     // 舌の上面（ケーブルの中心の高さ）
y_tail_end = Lb/2 + tail_len;
tw     = tie_w + tie_clr;                    // バンド溝の幅
y_tie3 = y_tail_end - 4 - tw/2;              // 舌のバンドの位置
tape_s = tape_size + 2*tape_clr;             // テープのくぼみの大きさ
tape_depth = tape_t - tape_crush;            // テープのくぼみの深さ
tape_ys = [0, (Lb/2 + y_tie3 - tw/2)/2];     // 本体の中央（2本のバンドの間）と、舌の中ほど

echo(str("鞍の内半径 R=", R, "  本体 ", Wb, " x ", Lb + tail_len, " x 高さ ", sag + z_top,
         " mm  ポケット底 z=", z_pf, "  テープのくぼみ深さ ", tape_depth));

// XZ断面（2D：xがX、yがZ）
module section(ztop, half_w) {
    difference() {
        intersection() {
            hull() {
                translate([-half_w, 0]) square([2*half_w, ztop]);
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

// 平面で見た外形（上から見た形）を縦に押し出したもの
module plan_clip(l, w, r, y0 = 0) {
    translate([0, y0, -500]) linear_extrude(height = 1000) rr2d(l, w, r);
}

module mount() {
    difference() {
        union() {
            // 本体：断面の押し出しを、角Rの外形で切り抜く
            intersection() {
                extrude_y(-Lb/2, Lb/2) section(z_top, Wb/2);
                plan_clip(Lb, Wb, r_out);
            }
            // ケーブル側の舌：先端の角だけR（根元は本体に埋める）
            intersection() {
                extrude_y(Lb/2 - r_out, y_tail_end) section(z_tt, tail_w/2);
                plan_clip(tail_len + r_out + tail_corner_r, tail_w, tail_corner_r,
                          (Lb/2 - r_out + y_tail_end + tail_corner_r)/2);
            }
        }
        // アンテナのポケット
        translate([0, 0, z_pf]) linear_extrude(height = pocket_depth + 1) rr2d(pk_l, pk_w, ant_corner_r);
        // ケーブル口：+Y側の壁をブッシュ幅で切り欠く（上から差し込めるように上まで開ける）
        translate([-grommet_w/2, pk_l/2 - eps, z_pf])
            cube([grommet_w, wall + grommet_l + eps, max(pocket_depth, cable_z + cable_d) + 1]);
        // 舌の上のケーブル溝
        translate([0, Lb/2 - 1, z_tt]) rotate([-90, 0, 0])
            cylinder(d = cable_d + 0.6, h = tail_len + 2);
        // アンテナの下を通す結束バンドの溝（ロールバーに沿った円弧）
        for (y = [-(pk_l/2 - tie_inset), pk_l/2 - tie_inset])
            translate([0, y, -R]) rotate([90, 0, 0])
                cylinder(r = Rt, h = tw, center = true);
        // 舌：ケーブルの上からかけるバンドの位置決め（両側面の深さ0.8の溝）
        for (s = [-1, 1])
            translate([s * tail_w/2 - 0.8, y_tie3 - tw/2, -R])
                cube([1.6, tw, R + z_tt + 1]);
        // アンテナの上を回すバンド用：側壁の外面の溝と、上端の切り欠き（深さ1）
        if (top_tie_notch) {
            for (s = [-1, 1])
                translate([s * Wb/2 - 0.8, -tw/2, -R])
                    cube([1.6, tw, R + z_top + 1]);
            translate([-Wb/2 - 1, -tw/2, z_top - 1])
                cube([Wb + 2, tw, 2]);
        }
        // 両面テープのくぼみ：鞍の面から tape_depth だけ掘る（底はロールバーと同じ中心の円弧）
        if (tape_pads)
            for (y = tape_ys)
                intersection() {
                    translate([0, y, -R]) rotate([90, 0, 0])
                        cylinder(r = R + tape_depth, h = tape_s, center = true);
                    translate([-tape_s/2, y - tape_s/2, -R]) cube([tape_s, tape_s, R + tape_depth + 1]);
                }
        // 水抜き
        if (drain)
            translate([-2, -Lb/2 - 1, z_pf - 0.5]) cube([4, wall + 2, pocket_depth + 1]);
    }
}

// ---- プレビュー用の部品 ----
module antenna_dummy() {
    color("#222") translate([0, 0, z_pf + 0.3]) {
        hull() {
            linear_extrude(height = 4) rr2d(ant_l, ant_w, 5);
            translate([0, 0, ant_h - 1]) linear_extrude(height = 1) rr2d(ant_l - 10, ant_w - 10, 4);
        }
        translate([0, ant_l/2, cable_z - 0.3]) rotate([-90, 0, 0]) cylinder(d = 6, h = grommet_l);
        translate([0, ant_l/2, cable_z - 0.3]) rotate([-90, 0, 0]) cylinder(d = cable_d, h = 60);
    }
}
module bar_dummy() {
    color("silver", 0.6) translate([0, 0, -R]) rotate([90, 0, 0])
        cylinder(d = bar_d, h = 160, center = true);
}

if (show_preview) {
    color("orange") mount();
    antenna_dummy();
    bar_dummy();
} else {
    mount();
}
