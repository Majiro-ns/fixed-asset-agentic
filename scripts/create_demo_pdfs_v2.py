#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デモ用PDF 4パターン作成スクリプト v2（フォント埋め込み修正版）

使い方:
    cd C:/Users/owner/Desktop/fixed-asset-ashigaru
    pip install reportlab
    python scripts/create_demo_pdfs_v2.py

出力:
    data/demo_pdf/demo_capital.pdf   -> CAPITAL_LIKE 確定
    data/demo_pdf/demo_capital2.pdf  -> CAPITAL_LIKE 確定
    data/demo_pdf/demo_expense.pdf   -> EXPENSE_LIKE 確定
    data/demo_pdf/demo_guidance.pdf  -> GUIDANCE 確定

修正点:
    - TTCファイルのフォントインデックスを正しく指定
    - フォント埋め込みを確実に行う
"""

import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import mm
except ImportError:
    print("reportlab がインストールされていません。")
    print("pip install reportlab を実行してください。")
    exit(1)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "demo_pdf"


def register_japanese_font():
    """日本語フォントを登録（Windows環境・修正版）"""
    # TTCファイルはsubfontIndexを指定する必要がある
    font_configs = [
        # (パス, フォント名, subfontIndex)
        ("C:/Windows/Fonts/msgothic.ttc", "MSGothic", 0),
        ("C:/Windows/Fonts/meiryo.ttc", "Meiryo", 0),
        ("C:/Windows/Fonts/YuGothM.ttc", "YuGothic", 0),
        # TTFファイル（インデックス不要）
        ("C:/Windows/Fonts/msmincho.ttc", "MSMincho", 0),
    ]

    for path, name, index in font_configs:
        if os.path.exists(path):
            try:
                if path.endswith('.ttc'):
                    # TTCファイルはsubfontIndexを指定
                    pdfmetrics.registerFont(TTFont(name, path, subfontIndex=index))
                else:
                    pdfmetrics.registerFont(TTFont(name, path))
                print(f"Font registered: {name} from {path}")
                return name
            except Exception as e:
                print(f"Failed to register {path}: {e}")
                continue

    # フォールバック: 標準フォント使用（日本語不可）
    print("WARNING: No Japanese font found. Using Helvetica (Japanese will not display)")
    return "Helvetica"


def create_capital_pdf(filename: str, font_name: str):
    """
    CAPITAL_LIKE用: データセンター新設工事の見積書
    キーワード: 新設, 設置, 導入, 構築
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # タイトル
    c.setFont(font_name, 24)
    c.drawCentredString(width / 2, height - 40*mm, "御 見 積 書")

    # 宛先
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 60*mm, "株式会社サンプル商事 御中")

    # 発行情報
    c.setFont(font_name, 10)
    c.drawRightString(width - 25*mm, height - 55*mm, "見積番号: Q-2024-0115")
    c.drawRightString(width - 25*mm, height - 62*mm, "発行日: 2024年1月15日")

    # 発行元
    c.drawRightString(width - 25*mm, height - 75*mm, "架空ITソリューションズ株式会社")
    c.drawRightString(width - 25*mm, height - 82*mm, "東京都港区架空1-2-3")

    # 件名
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 95*mm, "件名: データセンター新設工事")

    # 合計金額
    c.setFont(font_name, 14)
    c.rect(25*mm, height - 115*mm, 160*mm, 12*mm, stroke=1, fill=0)
    c.drawString(30*mm, height - 112*mm, "御見積金額: 1,100,000円（税込）")

    # 明細ヘッダー
    table_top = height - 130*mm
    c.setFont(font_name, 10)
    c.setFillGray(0.9)
    c.rect(25*mm, table_top - 8*mm, 160*mm, 8*mm, stroke=1, fill=1)
    c.setFillGray(0)
    c.drawString(28*mm, table_top - 6*mm, "No")
    c.drawString(40*mm, table_top - 6*mm, "品名・作業内容")
    c.drawString(120*mm, table_top - 6*mm, "数量")
    c.drawString(145*mm, table_top - 6*mm, "金額")

    # 明細行（CAPITAL_LIKEキーワード）
    items = [
        ("1", "サーバー機器新設工事", "1式", "400,000円"),
        ("2", "ネットワーク設備設置工事", "1式", "300,000円"),
        ("3", "セキュリティシステム導入", "1式", "200,000円"),
        ("4", "インフラ基盤構築作業", "1式", "100,000円"),
    ]

    y = table_top - 8*mm
    for item in items:
        y -= 8*mm
        c.rect(25*mm, y, 160*mm, 8*mm, stroke=1, fill=0)
        c.drawString(28*mm, y + 2*mm, item[0])
        c.drawString(40*mm, y + 2*mm, item[1])
        c.drawString(122*mm, y + 2*mm, item[2])
        c.drawRightString(182*mm, y + 2*mm, item[3])

    # 小計・税・合計
    y -= 8*mm
    c.rect(25*mm, y, 160*mm, 8*mm, stroke=1, fill=0)
    c.drawString(120*mm, y + 2*mm, "小計")
    c.drawRightString(182*mm, y + 2*mm, "1,000,000円")

    y -= 8*mm
    c.rect(25*mm, y, 160*mm, 8*mm, stroke=1, fill=0)
    c.drawString(120*mm, y + 2*mm, "消費税 10%")
    c.drawRightString(182*mm, y + 2*mm, "100,000円")

    y -= 8*mm
    c.rect(25*mm, y, 160*mm, 8*mm, stroke=1, fill=0)
    c.drawString(120*mm, y + 2*mm, "合計")
    c.drawRightString(182*mm, y + 2*mm, "1,100,000円")

    # 備考
    y -= 20*mm
    c.setFont(font_name, 9)
    c.drawString(25*mm, y, "【備考】")
    c.drawString(25*mm, y - 8*mm, "・納期: ご発注後30営業日")
    c.drawString(25*mm, y - 16*mm, "・支払条件: 納品月末締め翌月末払い")

    c.save()
    print(f"Created: {filepath}")


def create_expense_pdf(filename: str, font_name: str):
    """
    EXPENSE_LIKE用: 年間保守契約の見積書
    キーワード: 保守, 点検, 修理, 調整, 清掃
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # タイトル
    c.setFont(font_name, 22)
    c.drawCentredString(width / 2, height - 40*mm, "年間保守契約 御見積書")

    # 宛先
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 60*mm, "株式会社サンプル製作所 御中")

    # 発行情報
    c.setFont(font_name, 10)
    c.drawRightString(width - 25*mm, height - 55*mm, "見積番号: M-2024-0088")
    c.drawRightString(width - 25*mm, height - 62*mm, "発行日: 2024年2月1日")

    # 発行元
    c.drawRightString(width - 25*mm, height - 75*mm, "架空メンテナンス株式会社")
    c.drawRightString(width - 25*mm, height - 82*mm, "保守サービス事業部")

    # 契約概要
    y = height - 100*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【契約概要】")
    c.setFont(font_name, 10)
    c.drawString(30*mm, y - 10*mm, "契約期間: 2024年4月1日〜2025年3月31日（12ヶ月）")
    c.drawString(30*mm, y - 18*mm, "対象設備: 空調設備、電気設備、防災設備")

    # サービス内容（EXPENSE_LIKEキーワード）
    y -= 35*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【サービス内容】")
    c.setFont(font_name, 10)
    y -= 10*mm
    c.drawString(30*mm, y, "1. 定期点検サービス（年4回）")
    c.drawString(35*mm, y - 8*mm, "- 空調機器点検・調整作業")
    c.drawString(35*mm, y - 16*mm, "- 電気設備点検作業")

    y -= 28*mm
    c.drawString(30*mm, y, "2. 保守サービス")
    c.drawString(35*mm, y - 8*mm, "- 設備保守・メンテナンス作業")
    c.drawString(35*mm, y - 16*mm, "- フィルター清掃作業")

    y -= 28*mm
    c.drawString(30*mm, y, "3. 修理対応")
    c.drawString(35*mm, y - 8*mm, "- 軽微な修理作業（部品代別途）")

    # 費用
    y -= 25*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【年間費用】")
    c.setFont(font_name, 10)
    y -= 12*mm
    c.drawString(30*mm, y, "定期点検費用 ..................... 40,000円")
    y -= 8*mm
    c.drawString(30*mm, y, "保守基本料金 ..................... 50,000円")
    y -= 8*mm
    c.drawString(30*mm, y, "緊急対応費用（基本枠）............. 10,000円")

    y -= 12*mm
    c.line(30*mm, y + 4*mm, 140*mm, y + 4*mm)
    c.drawString(30*mm, y, "小計 ............................. 100,000円")
    y -= 8*mm
    c.drawString(30*mm, y, "消費税（10%）..................... 10,000円")
    y -= 10*mm
    c.setFont(font_name, 11)
    c.drawString(30*mm, y, "年間合計 ......................... 110,000円")

    c.save()
    print(f"Created: {filepath}")


def create_guidance_pdf(filename: str, font_name: str):
    """
    GUIDANCE用: 撤去・移設混在の作業報告書
    キーワード: 既設, 撤去, 移設（判断が割れる）
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # タイトル
    c.setFont(font_name, 22)
    c.drawCentredString(width / 2, height - 40*mm, "作 業 完 了 報 告 書")

    # 基本情報
    c.setFont(font_name, 11)
    y = height - 60*mm
    c.drawString(25*mm, y, "報告日: 2024年1月20日")
    c.drawString(25*mm, y - 8*mm, "作業場所: 本社サーバールーム")
    c.drawString(25*mm, y - 16*mm, "担当: 架空エンジニアリング株式会社")

    # 宛先
    y -= 30*mm
    c.setFont(font_name, 12)
    c.drawString(25*mm, y, "株式会社テスト工業 情報システム部 御中")

    # 作業内容（GUIDANCEキーワード: 既設, 撤去, 移設）
    y -= 20*mm
    c.setFont(font_name, 12)
    c.drawString(25*mm, y, "【作業内容】")

    c.setFont(font_name, 11)
    y -= 15*mm
    c.drawString(30*mm, y, "1. 既設サーバー撤去作業")
    c.drawString(35*mm, y - 10*mm, "- 既設ラック内機器の取り外し")
    c.drawString(35*mm, y - 20*mm, "- ケーブル撤去及び廃棄処理")

    y -= 35*mm
    c.drawString(30*mm, y, "2. 機器移設工事")
    c.drawString(35*mm, y - 10*mm, "- 移設先ラックへの機器設置")
    c.drawString(35*mm, y - 20*mm, "- 既設配線の再接続作業")

    # 費用明細
    y -= 40*mm
    c.setFont(font_name, 12)
    c.drawString(25*mm, y, "【費用明細】")

    c.setFont(font_name, 11)
    y -= 15*mm
    c.drawString(30*mm, y, "既設サーバー撤去作業 ............. 150,000円")
    y -= 10*mm
    c.drawString(30*mm, y, "機器移設工事 ..................... 100,000円")

    y -= 15*mm
    c.line(30*mm, y + 5*mm, 150*mm, y + 5*mm)
    c.drawString(30*mm, y, "小計 ............................. 250,000円")
    y -= 10*mm
    c.drawString(30*mm, y, "消費税（10%）..................... 25,000円")
    y -= 12*mm
    c.setFont(font_name, 12)
    c.drawString(30*mm, y, "合計 ............................. 275,000円")

    # 特記事項
    y -= 25*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【特記事項】")
    c.setFont(font_name, 10)
    c.drawString(30*mm, y - 10*mm, "・既設機器の一部は再利用のため保管")
    c.drawString(30*mm, y - 20*mm, "・移設作業は夜間帯に実施")

    c.save()
    print(f"Created: {filepath}")


def create_capital2_pdf(filename: str, font_name: str):
    """
    CAPITAL_LIKE用（別様式）: 発注書形式
    キーワード: 購入, 整備
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # タイトル
    c.setFont(font_name, 24)
    c.drawCentredString(width / 2, height - 40*mm, "発 注 書")

    # 発注情報
    c.setFont(font_name, 10)
    c.drawRightString(width - 25*mm, height - 55*mm, "発注番号: PO-2024-0312")
    c.drawRightString(width - 25*mm, height - 63*mm, "発注日: 2024年3月12日")

    # 発注先
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 60*mm, "株式会社オフィス機器販売 御中")

    # 発注元
    c.setFont(font_name, 10)
    c.drawString(25*mm, height - 80*mm, "発注元: 架空産業株式会社 総務部")
    c.drawString(25*mm, height - 88*mm, "担当者: 山田太郎")

    # 件名
    c.setFont(font_name, 11)
    c.drawString(25*mm, height - 105*mm, "件名: オフィス機器購入及び環境整備")

    # 明細ヘッダー
    table_top = height - 120*mm
    c.setFont(font_name, 10)
    c.setFillGray(0.85)
    c.rect(25*mm, table_top - 8*mm, 160*mm, 8*mm, stroke=1, fill=1)
    c.setFillGray(0)
    c.drawString(28*mm, table_top - 6*mm, "品目")
    c.drawString(100*mm, table_top - 6*mm, "数量")
    c.drawString(130*mm, table_top - 6*mm, "単価")
    c.drawString(160*mm, table_top - 6*mm, "金額")

    # 明細行（CAPITAL_LIKEキーワード: 購入, 整備）
    items = [
        ("業務用PC購入", "10台", "150,000", "1,500,000"),
        ("モニター購入", "10台", "50,000", "500,000"),
        ("デスク・チェア購入", "10セット", "80,000", "800,000"),
        ("OAフロア整備工事", "1式", "300,000", "300,000"),
        ("電源環境整備", "1式", "200,000", "200,000"),
    ]

    y = table_top - 8*mm
    for item in items:
        y -= 8*mm
        c.rect(25*mm, y, 160*mm, 8*mm, stroke=1, fill=0)
        c.drawString(28*mm, y + 2*mm, item[0])
        c.drawString(102*mm, y + 2*mm, item[1])
        c.drawRightString(150*mm, y + 2*mm, item[2])
        c.drawRightString(182*mm, y + 2*mm, item[3])

    # 合計
    y -= 15*mm
    c.setFont(font_name, 11)
    c.drawString(120*mm, y, "小計: 3,300,000円")
    c.drawString(120*mm, y - 10*mm, "消費税: 330,000円")
    c.setFont(font_name, 12)
    c.drawString(120*mm, y - 22*mm, "合計: 3,630,000円")

    c.save()
    print(f"Created: {filepath}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    font = register_japanese_font()
    print(f"Using font: {font}")
    print()

    # 4パターン作成
    create_capital_pdf("demo_capital.pdf", font)
    create_expense_pdf("demo_expense.pdf", font)
    create_guidance_pdf("demo_guidance.pdf", font)
    create_capital2_pdf("demo_capital2.pdf", font)

    print()
    print("=" * 50)
    print("デモ用PDF作成完了（4パターン）")
    print(f"出力先: {OUTPUT_DIR}")
    print()
    print("期待される判定結果:")
    print("  demo_capital.pdf  -> CAPITAL_LIKE（資産寄り）")
    print("  demo_expense.pdf  -> EXPENSE_LIKE（費用寄り）")
    print("  demo_guidance.pdf -> GUIDANCE（要確認）")
    print("  demo_capital2.pdf -> CAPITAL_LIKE（資産寄り）")
    print("=" * 50)


if __name__ == "__main__":
    main()
