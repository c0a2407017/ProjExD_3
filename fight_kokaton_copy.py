import os
import random
import sys
import time
import math
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # デフォルトの向き（右向き）

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/6.png"), 0, 0.9)
        screen.blit(self.img, self.rct)
        pg.display.update()
        time.sleep(0.5)  # 0.5秒間表示
        self.img = __class__.imgs[self.dire]  # 元の画像に戻す

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)  # 向きを更新
            self.img = __class__.imgs[self.dire]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load("beam.png")  # ビーム画像をロード
        angle = math.degrees(math.atan2(-bird.dire[1], bird.dire[0]))  # 角度を計算
        self.img = pg.transform.rotozoom(self.img, angle, 1.0)  # 角度に応じて回転
        self.rct = self.img.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width // 2 * bird.dire[0] // 5
        self.rct.centery = bird.rct.centery + bird.rct.height // 2 * bird.dire[1] // 5
        self.vx, self.vy = bird.dire[0] * 5, bird.dire[1] * 5  # ビームの速度

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rct.move_ip(self.vx, self.vy)  # ビームを移動
        if check_bound(self.rct) != (True, True):  # 画面外に出たら無効化
            return False
        screen.blit(self.img, self.rct)  # ビームを画面に描画
        return True


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """
    スコアを管理・表示するクラス
    """
    def __init__(self):
        """
        スコアの初期化
        """
        self.fonto = pg.font.SysFont("hgp創英角ポップ体", 30)  # フォント設定
        self.color = (0, 0, 255)  # 青色
        self.score = 0  # 初期スコア
        self.img = self.fonto.render(f"スコア: {self.score}", 0, self.color)  # スコア表示用Surface
        self.rct = self.img.get_rect()
        self.rct.bottomleft = (100, HEIGHT - 50)  # 画面左下に表示

    def update(self, screen: pg.Surface):
        """
        スコアを更新して画面に描画する
        引数 screen：画面Surface
        """
        self.img = self.fonto.render(f"スコア: {self.score}", 0, self.color)  # スコアを更新
        screen.blit(self.img, self.rct)  # スコアを画面に描画


class Explosion:
    """
    爆発エフェクトを管理するクラス
    """
    def __init__(self, center: tuple[int, int]):
        """
        爆発エフェクトを初期化する
        引数 center：爆発の中心座標
        """
        # explosion.gifをロードし、上下反転した2つのSurfaceをリストに格納
        img = pg.image.load("explosion.gif")
        self.images = [
            img,
            pg.transform.flip(img, True, True)
        ]
        self.index = 0  # 現在の画像インデックス
        self.img = self.images[self.index]
        self.rct = self.img.get_rect()
        self.rct.center = center
        self.life = 20  # 爆発の表示時間

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを更新して描画する
        引数 screen：画面Surface
        """
        self.life -= 1
        if self.life > 0:
            self.index = (self.index + 1) % 2  # 画像を交互に切り替える
            self.img = self.images[self.index]
            screen.blit(self.img, self.rct)  # 爆発を描画


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  # 複数の爆弾を生成
    beams = []  # ビームのリスト
    explosions = []  # 爆発エフェクトのリスト
    score = Score()  # スコアインスタンスを生成
    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でビームを発射
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        # こうかとんと爆弾の衝突判定
        for bomb in bombs[:]:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        # ビームの更新と描画
        for beam in beams[:]:
            if not beam.update(screen):  # ビームが画面外に出たら削除
                beams.remove(beam)

        # 爆弾とビームの衝突判定
        for beam in beams[:]:
            for bomb in bombs[:]:
                if beam.rct.colliderect(bomb.rct):
                    beams.remove(beam)  # ビームを削除
                    bombs.remove(bomb)  # 爆弾を削除
                    bird.change_img(5, screen)  # 喜ぶエフェクト
                    score.score += 1  # スコアを1点加算
                    explosions.append(Explosion(bomb.rct.center))  # 爆発エフェクトを追加
                    break

        # 爆弾の更新
        for bomb in bombs:
            bomb.update(screen)

        # 爆発エフェクトの更新と描画
        for explosion in explosions[:]:
            explosion.update(screen)
            if explosion.life <= 0:  # 爆発が終了したら削除
                explosions.remove(explosion)

        # スコアの更新と描画
        score.update(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
