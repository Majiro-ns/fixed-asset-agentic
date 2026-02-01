#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デモ用PDF 4パターン作成スクリプト（異なる様式）

使い方:
    cd C:/Users/owner/Desktop/fixed-asset-ashigaru
    pip install reportlab
    python scripts/create_demo_pdfs.py

出力:
    data/demo_pdf/demo_capital.pdf   -> CAPITAL_LIKE 確定（正式見積書形式）
    data/demo_pdf/demo_capital2.pdf  -> CAPITAL_LIKE 確定（発注書形式）
    data/demo_pdf/demo_expense.pdf   -> EXPENSE_LIKE 確定（保守契約書形式）
    data/demo_pdf/demo_guidance.pdf  -> GUIDANCE 確定（作業報告書形式）
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
    """日本語フォントを登録（Windows環境）"""
    font_paths = [
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("JapaneseFont", path))
                return "JapaneseFont"
            except Exception:
                continue
    return "Helvetica"


def format_yen(amount: int) -> str:
    """金額を日本円形式でフォーマット（¥なし、カンマ区切り + 円）"""
    return f"{amount:,}円"


def create_formal_estimate_pdf(filename: str, font_name: str):
    """
    パターンA: 正式な見積書形式（CAPITAL_LIKE用）
    - 罫線付きテーブル
    - 会社印欄あり
    - 正式なビジネス文書スタイル
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # ヘッダー: 御見積書（大きく中央）
    c.setFont(font_name, 28)
    c.drawCentredString(width / 2, height - 40*mm, "御 見 積 書")

    # 宛先（左上）
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 65*mm, "株式会社サンプル商事 御中")
    c.line(25*mm, height - 68*mm, 90*mm, height - 68*mm)

    # 発行情報（右上）
    c.setFont(font_name, 10)
    c.drawRightString(width - 25*mm, height - 55*mm, "見積番号: Q-2024-0115")
    c.drawRightString(width - 25*mm, height - 62*mm, "発行日: 2024年1月15日")
    c.drawRightString(width - 25*mm, height - 69*mm, "有効期限: 2024年2月14日")

    # 発行元
    c.drawRightString(width - 25*mm, height - 82*mm, "架空ITソリューションズ株式会社")
    c.drawRightString(width - 25*mm, height - 89*mm, "東京都港区架空1-2-3")
    c.drawRightString(width - 25*mm, height - 96*mm, "TEL: 03-1234-5678")

    # 件名
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 110*mm, "件名: データセンター新設工事")

    # 合計金額（目立つ枠）
    c.setFont(font_name, 14)
    c.rect(25*mm, height - 130*mm, 160*mm, 12*mm, stroke=1, fill=0)
    c.drawString(30*mm, height - 127*mm, "御見積金額:")
    c.setFont(font_name, 16)
    c.drawRightString(180*mm, height - 127*mm, "1,100,000円（税込）")

    # 明細テーブル
    table_top = height - 145*mm
    c.setFont(font_name, 9)

    # テーブルヘッダー
    c.setFillGray(0.9)
    c.rect(25*mm, table_top - 8*mm, 160*mm, 8*mm, stroke=1, fill=1)
    c.setFillGray(0)
    c.drawString(28*mm, table_top - 6*mm, "No")
    c.drawString(38*mm, table_top - 6*mm, "品名・作業内容")
    c.drawString(105*mm, table_top - 6*mm, "数量")
    c.drawString(120*mm, table_top - 6*mm, "単価")
    c.drawString(150*mm, table_top - 6*mm, "金額")

    # 明細行（CAPITAL_LIKEキーワード: 新設, 設置, 導入, 構築）
    items = [
        ("1", "サーバー機器新設工事", "1式", "400,000", "400,000"),
        ("2", "ネットワーク設備設置工事", "1式", "300,000", "300,000"),
        ("3", "セキュリティシステム導入", "1式", "200,000", "200,000"),
        ("4", "インフラ基盤構築作業", "1式", "100,000", "100,000"),
    ]

    y = table_top - 8*mm
    for item in items:
        y -= 7*mm
        c.rect(25*mm, y, 160*mm, 7*mm, stroke=1, fill=0)
        c.drawString(28*mm, y + 2*mm, item[0])
        c.drawString(38*mm, y + 2*mm, item[1])
        c.drawString(108*mm, y + 2*mm, item[2])
        c.drawRightString(140*mm, y + 2*mm, item[3])
        c.drawRightString(180*mm, y + 2*mm, item[4])

    # 小計・税・合計
    y -= 7*mm
    c.rect(25*mm, y, 160*mm, 7*mm, stroke=1, fill=0)
    c.drawString(120*mm, y + 2*mm, "小計")
    c.drawRightString(180*mm, y + 2*mm, "1,000,000")

    y -= 7*mm
    c.rect(25*mm, y, 160*mm, 7*mm, stroke=1, fill=0)
    c.drawString(120*mm, y + 2*mm, "消費税 10%")
    c.drawRightString(180*mm, y + 2*mm, "100,000")

    y -= 7*mm
    c.setFont(font_name, 10)
    c.rect(25*mm, y, 160*mm, 7*mm, stroke=1, fill=0)
    c.drawString(120*mm, y + 2*mm, "合計")
    c.drawRightString(180*mm, y + 2*mm, "1,100,000")

    # 備考
    y -= 20*mm
    c.setFont(font_name, 9)
    c.drawString(25*mm, y, "【備考】")
    c.drawString(25*mm, y - 7*mm, "・納期: ご発注後30営業日")
    c.drawString(25*mm, y - 14*mm, "・支払条件: 納品月末締め翌月末払い")
    c.drawString(25*mm, y - 21*mm, "・本見積書はデモ用の架空データです")

    c.save()
    print(f"Created: {filepath}")


def create_simple_delivery_pdf(filename: str, font_name: str):
    """
    パターンB: シンプルな納品書/作業報告書形式（GUIDANCE用）
    - 罫線なしのシンプルなリスト
    - 作業報告書スタイル
    - 異なるレイアウトで「様々なフォーマット対応」をアピール
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # ヘッダー: 作業完了報告書
    c.setFont(font_name, 22)
    c.drawCentredString(width / 2, height - 35*mm, "作 業 完 了 報 告 書")

    # 基本情報（左寄せ、シンプル）
    c.setFont(font_name, 11)
    y = height - 60*mm
    c.drawString(25*mm, y, "報告日: 2024年1月20日")
    y -= 8*mm
    c.drawString(25*mm, y, "作業場所: 本社サーバールーム")
    y -= 8*mm
    c.drawString(25*mm, y, "担当: 架空エンジニアリング(株)")

    # 宛先
    y -= 15*mm
    c.drawString(25*mm, y, "株式会社テスト工業 情報システム部 御中")

    # 作業内容（GUIDANCEキーワード: 既設, 撤去, 移設, 一式）
    y -= 20*mm
    c.setFont(font_name, 12)
    c.drawString(25*mm, y, "【作業内容】")

    c.setFont(font_name, 11)
    y -= 12*mm
    c.drawString(30*mm, y, "1. 既設サーバー撤去作業一式")
    y -= 8*mm
    c.drawString(35*mm, y, "- 既設ラック内機器の取り外し")
    y -= 8*mm
    c.drawString(35*mm, y, "- ケーブル撤去及び廃棄処理")

    y -= 12*mm
    c.drawString(30*mm, y, "2. 機器移設工事一式")
    y -= 8*mm
    c.drawString(35*mm, y, "- 移設先ラックへの機器設置")
    y -= 8*mm
    c.drawString(35*mm, y, "- 既設配線の再接続作業")

    # 金額（シンプルなリスト形式）
    y -= 20*mm
    c.setFont(font_name, 12)
    c.drawString(25*mm, y, "【費用明細】")

    c.setFont(font_name, 11)
    y -= 12*mm
    c.drawString(30*mm, y, "既設サーバー撤去作業一式 ............ 150,000円")
    y -= 8*mm
    c.drawString(30*mm, y, "機器移設工事一式 .................... 100,000円")

    y -= 12*mm
    c.line(30*mm, y + 5*mm, 150*mm, y + 5*mm)
    c.drawString(30*mm, y, "小計 ............................... 250,000円")
    y -= 8*mm
    c.drawString(30*mm, y, "消費税（10%） ....................... 25,000円")
    y -= 10*mm
    c.setFont(font_name, 12)
    c.drawString(30*mm, y, "合計 ............................... 275,000円")

    # 特記事項
    y -= 25*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【特記事項】")
    y -= 10*mm
    c.setFont(font_name, 10)
    c.drawString(30*mm, y, "・既設機器の一部は再利用のため保管")
    y -= 7*mm
    c.drawString(30*mm, y, "・移設作業は夜間帯に実施")
    y -= 7*mm
    c.drawString(30*mm, y, "・本報告書はデモ用の架空データです")

    # 署名欄
    y -= 25*mm
    c.setFont(font_name, 10)
    c.drawString(120*mm, y, "作業責任者: _______________")
    y -= 10*mm
    c.drawString(120*mm, y, "確認者: _______________")

    c.save()
    print(f"Created: {filepath}")


def create_purchase_order_pdf(filename: str, font_name: str):
    """
    パターンC: 発注書形式（CAPITAL_LIKE用・別様式）
    - 横長テーブル
    - 発注書スタイル
    - キーワード: 購入, 整備
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # ヘッダー
    c.setFont(font_name, 24)
    c.drawCentredString(width / 2, height - 35*mm, "発 注 書")

    # 発注番号・日付（右上）
    c.setFont(font_name, 10)
    c.drawRightString(width - 25*mm, height - 50*mm, "発注番号: PO-2024-0312")
    c.drawRightString(width - 25*mm, height - 57*mm, "発注日: 2024年3月12日")
    c.drawRightString(width - 25*mm, height - 64*mm, "納期: 2024年4月30日")

    # 発注先（左上）
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 55*mm, "株式会社オフィス機器販売 御中")
    c.line(25*mm, height - 58*mm, 100*mm, height - 58*mm)

    # 発注元
    c.setFont(font_name, 10)
    y = height - 75*mm
    c.drawString(25*mm, y, "発注元: 架空産業株式会社 総務部")
    y -= 7*mm
    c.drawString(25*mm, y, "担当者: 山田太郎")
    y -= 7*mm
    c.drawString(25*mm, y, "TEL: 03-9999-8888")

    # 件名
    y -= 15*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "件名: オフィス機器購入及び環境整備")

    # 明細（シンプルな表）
    y -= 15*mm
    c.setFont(font_name, 10)

    # ヘッダー行
    c.setFillGray(0.85)
    c.rect(25*mm, y - 7*mm, 160*mm, 7*mm, stroke=1, fill=1)
    c.setFillGray(0)
    c.drawString(27*mm, y - 5*mm, "品目")
    c.drawString(100*mm, y - 5*mm, "数量")
    c.drawString(125*mm, y - 5*mm, "単価")
    c.drawString(155*mm, y - 5*mm, "金額")

    # 明細行（CAPITAL_LIKEキーワード: 購入, 整備）
    items = [
        ("業務用PC購入", "10台", "150,000", "1,500,000"),
        ("モニター購入", "10台", "50,000", "500,000"),
        ("デスク・チェア購入", "10セット", "80,000", "800,000"),
        ("OAフロア整備工事", "1式", "300,000", "300,000"),
        ("電源環境整備", "1式", "200,000", "200,000"),
    ]

    y -= 7*mm
    for item in items:
        y -= 7*mm
        c.rect(25*mm, y, 160*mm, 7*mm, stroke=1, fill=0)
        c.drawString(27*mm, y + 2*mm, item[0])
        c.drawString(102*mm, y + 2*mm, item[1])
        c.drawRightString(145*mm, y + 2*mm, item[2])
        c.drawRightString(182*mm, y + 2*mm, item[3])

    # 合計
    y -= 10*mm
    c.setFont(font_name, 11)
    c.drawString(120*mm, y, "小計: 3,300,000円")
    y -= 7*mm
    c.drawString(120*mm, y, "消費税: 330,000円")
    y -= 8*mm
    c.setFont(font_name, 12)
    c.drawString(120*mm, y, "合計: 3,630,000円")

    # 支払条件
    y -= 20*mm
    c.setFont(font_name, 10)
    c.drawString(25*mm, y, "【支払条件】")
    y -= 8*mm
    c.drawString(30*mm, y, "納品検収後、月末締め翌月末払い")

    # 備考
    y -= 15*mm
    c.drawString(25*mm, y, "※本発注書はデモ用の架空データです")

    c.save()
    print(f"Created: {filepath}")


def create_maintenance_contract_pdf(filename: str, font_name: str):
    """
    パターンD: 保守契約書形式（EXPENSE_LIKE用）
    - 契約書スタイル
    - 箇条書き中心
    - キーワード: 保守, 点検, 修理, 調整
    """
    filepath = OUTPUT_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4

    # ヘッダー
    c.setFont(font_name, 22)
    c.drawCentredString(width / 2, height - 35*mm, "年間保守契約 御見積書")

    # 基本情報
    c.setFont(font_name, 10)
    c.drawRightString(width - 25*mm, height - 50*mm, "見積番号: M-2024-0088")
    c.drawRightString(width - 25*mm, height - 57*mm, "発行日: 2024年2月1日")

    # 宛先
    c.setFont(font_name, 12)
    c.drawString(25*mm, height - 55*mm, "株式会社サンプル製作所 御中")

    # 発行元
    c.setFont(font_name, 10)
    c.drawRightString(width - 25*mm, height - 72*mm, "架空メンテナンス株式会社")
    c.drawRightString(width - 25*mm, height - 79*mm, "保守サービス事業部")

    # 契約概要
    y = height - 95*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【契約概要】")
    y -= 10*mm
    c.setFont(font_name, 10)
    c.drawString(30*mm, y, "契約期間: 2024年4月1日 〜 2025年3月31日（12ヶ月）")
    y -= 7*mm
    c.drawString(30*mm, y, "対象設備: 空調設備、電気設備、防災設備")

    # サービス内容（EXPENSE_LIKEキーワード: 保守, 点検, 修理, 調整）
    y -= 15*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【サービス内容】")

    c.setFont(font_name, 10)
    y -= 10*mm
    c.drawString(30*mm, y, "1. 定期点検サービス（年4回）")
    y -= 7*mm
    c.drawString(35*mm, y, "- 空調機器点検・調整作業")
    y -= 7*mm
    c.drawString(35*mm, y, "- 電気設備点検作業")
    y -= 7*mm
    c.drawString(35*mm, y, "- 防災設備点検作業")

    y -= 10*mm
    c.drawString(30*mm, y, "2. 保守サービス")
    y -= 7*mm
    c.drawString(35*mm, y, "- 設備保守・メンテナンス作業")
    y -= 7*mm
    c.drawString(35*mm, y, "- フィルター清掃作業")

    y -= 10*mm
    c.drawString(30*mm, y, "3. 修理対応")
    y -= 7*mm
    c.drawString(35*mm, y, "- 軽微な修理作業（部品代別途）")
    y -= 7*mm
    c.drawString(35*mm, y, "- 緊急時の調整対応")

    # 費用
    y -= 15*mm
    c.setFont(font_name, 11)
    c.drawString(25*mm, y, "【年間費用】")

    c.setFont(font_name, 10)
    y -= 10*mm
    c.drawString(30*mm, y, "定期点検費用 .................. 240,000円")
    y -= 7*mm
    c.drawString(30*mm, y, "保守基本料金 .................. 180,000円")
    y -= 7*mm
    c.drawString(30*mm, y, "緊急対応費用（基本枠）......... 60,000円")

    y -= 10*mm
    c.line(30*mm, y + 3*mm, 140*mm, y + 3*mm)
    c.drawString(30*mm, y, "小計 .......................... 480,000円")
    y -= 7*mm
    c.drawString(30*mm, y, "消費税（10%）.................. 48,000円")
    y -= 8*mm
    c.setFont(font_name, 11)
    c.drawString(30*mm, y, "年間合計 ...................... 528,000円")

    # 備考
    y -= 20*mm
    c.setFont(font_name, 9)
    c.drawString(25*mm, y, "※本見積書はデモ用の架空データです")
    y -= 6*mm
    c.drawString(25*mm, y, "※部品代・消耗品は別途実費請求となります")

    c.save()
    print(f"Created: {filepath}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    font = register_japanese_font()
    print(f"Using font: {font}")

    # パターンA: 正式見積書形式 -> CAPITAL_LIKE
    create_formal_estimate_pdf("demo_capital.pdf", font)

    # パターンB: 作業報告書形式 -> GUIDANCE
    create_simple_delivery_pdf("demo_guidance.pdf", font)

    # パターンC: 発注書形式 -> CAPITAL_LIKE（別様式）
    create_purchase_order_pdf("demo_capital2.pdf", font)

    # パターンD: 保守契約書形式 -> EXPENSE_LIKE
    create_maintenance_contract_pdf("demo_expense.pdf", font)

    print("\n=== デモ用PDF作成完了（4パターン）===")
    print(f"出力先: {OUTPUT_DIR}")
    print("\n期待される判定結果:")
    print("  demo_capital.pdf  -> CAPITAL_LIKE（資産寄り）")
    print("    様式: 正式な見積書 / キーワード: 新設, 設置, 導入, 構築")
    print("")
    print("  demo_capital2.pdf -> CAPITAL_LIKE（資産寄り）")
    print("    様式: 発注書 / キーワード: 購入, 整備")
    print("")
    print("  demo_expense.pdf  -> EXPENSE_LIKE（費用寄り）")
    print("    様式: 保守契約書 / キーワード: 保守, 点検, 修理, 調整, 清掃")
    print("")
    print("  demo_guidance.pdf -> GUIDANCE（要確認）")
    print("    様式: 作業報告書 / キーワード: 既設, 撤去, 移設, 一式")
    print("")
    print("【デモのポイント】")
    print("  4つの異なる様式のPDFを正しく読み取り・判定できることをアピール")


if __name__ == "__main__":
    main()
