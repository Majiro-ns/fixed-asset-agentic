#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デモ用PDF 4パターン作成スクリプト v3（fpdf2使用版）

reportlabでのTTCフォント埋め込み問題を回避するため、fpdf2を使用。

使い方:
    cd C:/Users/owner/Desktop/fixed-asset-ashigaru
    pip install fpdf2
    python scripts/create_demo_pdfs_v3.py

出力:
    data/demo_pdf/demo_capital.pdf   -> CAPITAL_LIKE 確定
    data/demo_pdf/demo_expense.pdf   -> EXPENSE_LIKE 確定
    data/demo_pdf/demo_guidance.pdf  -> GUIDANCE 確定
    data/demo_pdf/demo_capital2.pdf  -> CAPITAL_LIKE 確定
"""

import os
from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 がインストールされていません。")
    print("pip install fpdf2 を実行してください。")
    exit(1)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "demo_pdf"


class JapanesePDF(FPDF):
    """日本語対応PDF"""
    def __init__(self):
        super().__init__()
        # Windowsの日本語フォントを登録
        font_paths = [
            ("C:/Windows/Fonts/msgothic.ttc", "MSGothic"),
            ("C:/Windows/Fonts/meiryo.ttc", "Meiryo"),
            ("C:/Windows/Fonts/YuGothM.ttc", "YuGothic"),
            # WSL paths
            ("/mnt/c/Windows/Fonts/msgothic.ttc", "MSGothic"),
            ("/mnt/c/Windows/Fonts/meiryo.ttc", "Meiryo"),
            ("/mnt/c/Windows/Fonts/YuGothM.ttc", "YuGothic"),
        ]

        self.font_name = None
        for path, name in font_paths:
            if os.path.exists(path):
                try:
                    self.add_font(name, "", path, uni=True)
                    self.font_name = name
                    print(f"Font registered: {name}")
                    break
                except Exception as e:
                    print(f"Failed to register {name}: {e}")
                    continue

        if not self.font_name:
            print("WARNING: No Japanese font found")
            self.font_name = "Helvetica"

    def set_jp_font(self, size=10):
        self.set_font(self.font_name, size=size)


def create_capital_pdf():
    """
    CAPITAL_LIKE用: データセンター新設工事の見積書
    キーワード: 新設, 設置, 導入, 構築
    """
    pdf = JapanesePDF()
    pdf.add_page()

    # タイトル
    pdf.set_jp_font(24)
    pdf.cell(0, 20, "御 見 積 書", align="C", ln=True)
    pdf.ln(10)

    # 宛先
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "株式会社サンプル商事 御中", ln=True)
    pdf.ln(5)

    # 発行情報
    pdf.set_jp_font(10)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "見積番号: Q-2024-0115", ln=True)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "発行日: 2024年1月15日", ln=True)
    pdf.ln(5)

    # 発行元
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "架空ITソリューションズ株式会社", ln=True)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "東京都港区架空1-2-3", ln=True)
    pdf.ln(10)

    # 件名
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "件名: データセンター新設工事", ln=True)
    pdf.ln(5)

    # 合計金額
    pdf.set_jp_font(14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, "御見積金額: 1,100,000円（税込）", border=1, ln=True, fill=True)
    pdf.ln(10)

    # 明細テーブルヘッダー
    pdf.set_jp_font(10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(15, 8, "No", border=1, fill=True)
    pdf.cell(80, 8, "品名・作業内容", border=1, fill=True)
    pdf.cell(25, 8, "数量", border=1, fill=True)
    pdf.cell(35, 8, "金額", border=1, ln=True, fill=True)

    # 明細行（CAPITAL_LIKEキーワード: 新設, 設置, 導入, 構築）
    items = [
        ("1", "サーバー機器新設工事", "1式", "400,000円"),
        ("2", "ネットワーク設備設置工事", "1式", "300,000円"),
        ("3", "セキュリティシステム導入", "1式", "200,000円"),
        ("4", "インフラ基盤構築作業", "1式", "100,000円"),
    ]

    pdf.set_fill_color(255, 255, 255)
    for item in items:
        pdf.cell(15, 8, item[0], border=1)
        pdf.cell(80, 8, item[1], border=1)
        pdf.cell(25, 8, item[2], border=1)
        pdf.cell(35, 8, item[3], border=1, ln=True)

    # 小計・税・合計
    pdf.cell(95, 8, "", border=0)
    pdf.cell(25, 8, "小計", border=1)
    pdf.cell(35, 8, "1,000,000円", border=1, ln=True)

    pdf.cell(95, 8, "", border=0)
    pdf.cell(25, 8, "消費税", border=1)
    pdf.cell(35, 8, "100,000円", border=1, ln=True)

    pdf.set_jp_font(11)
    pdf.cell(95, 8, "", border=0)
    pdf.cell(25, 8, "合計", border=1)
    pdf.cell(35, 8, "1,100,000円", border=1, ln=True)

    # 備考
    pdf.ln(10)
    pdf.set_jp_font(9)
    pdf.cell(0, 6, "【備考】", ln=True)
    pdf.cell(0, 6, "・納期: ご発注後30営業日", ln=True)
    pdf.cell(0, 6, "・支払条件: 納品月末締め翌月末払い", ln=True)

    filepath = OUTPUT_DIR / "demo_capital.pdf"
    pdf.output(str(filepath))
    print(f"Created: {filepath}")


def create_expense_pdf():
    """
    EXPENSE_LIKE用: 年間保守契約の見積書
    キーワード: 保守, 点検, 修理, 調整, 清掃
    """
    pdf = JapanesePDF()
    pdf.add_page()

    # タイトル
    pdf.set_jp_font(22)
    pdf.cell(0, 20, "年間保守契約 御見積書", align="C", ln=True)
    pdf.ln(10)

    # 宛先
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "株式会社サンプル製作所 御中", ln=True)
    pdf.ln(5)

    # 発行情報
    pdf.set_jp_font(10)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "見積番号: M-2024-0088", ln=True)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "発行日: 2024年2月1日", ln=True)
    pdf.ln(5)

    # 発行元
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "架空メンテナンス株式会社", ln=True)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "保守サービス事業部", ln=True)
    pdf.ln(10)

    # 契約概要
    pdf.set_jp_font(11)
    pdf.cell(0, 8, "【契約概要】", ln=True)
    pdf.set_jp_font(10)
    pdf.cell(0, 6, "契約期間: 2024年4月1日〜2025年3月31日（12ヶ月）", ln=True)
    pdf.cell(0, 6, "対象設備: 空調設備、電気設備、防災設備", ln=True)
    pdf.ln(8)

    # サービス内容（EXPENSE_LIKEキーワード）
    pdf.set_jp_font(11)
    pdf.cell(0, 8, "【サービス内容】", ln=True)
    pdf.set_jp_font(10)
    pdf.cell(0, 6, "1. 定期点検サービス（年4回）", ln=True)
    pdf.cell(0, 6, "   - 空調機器点検・調整作業", ln=True)
    pdf.cell(0, 6, "   - 電気設備点検作業", ln=True)
    pdf.ln(3)
    pdf.cell(0, 6, "2. 保守サービス", ln=True)
    pdf.cell(0, 6, "   - 設備保守・メンテナンス作業", ln=True)
    pdf.cell(0, 6, "   - フィルター清掃作業", ln=True)
    pdf.ln(3)
    pdf.cell(0, 6, "3. 修理対応", ln=True)
    pdf.cell(0, 6, "   - 軽微な修理作業（部品代別途）", ln=True)
    pdf.ln(8)

    # 費用
    pdf.set_jp_font(11)
    pdf.cell(0, 8, "【年間費用】", ln=True)
    pdf.set_jp_font(10)
    pdf.cell(0, 6, "定期点検費用 ..................... 40,000円", ln=True)
    pdf.cell(0, 6, "保守基本料金 ..................... 50,000円", ln=True)
    pdf.cell(0, 6, "緊急修理対応費用（基本枠）......... 10,000円", ln=True)
    pdf.ln(3)
    pdf.cell(0, 6, "─────────────────────────", ln=True)
    pdf.cell(0, 6, "小計 ............................. 100,000円", ln=True)
    pdf.cell(0, 6, "消費税（10%）..................... 10,000円", ln=True)
    pdf.set_jp_font(11)
    pdf.cell(0, 8, "年間合計 ......................... 110,000円", ln=True)

    filepath = OUTPUT_DIR / "demo_expense.pdf"
    pdf.output(str(filepath))
    print(f"Created: {filepath}")


def create_guidance_pdf():
    """
    GUIDANCE用: 撤去・移設混在の作業報告書
    キーワード: 既設, 撤去, 移設（判断が割れる）
    """
    pdf = JapanesePDF()
    pdf.add_page()

    # タイトル
    pdf.set_jp_font(22)
    pdf.cell(0, 20, "作 業 完 了 報 告 書", align="C", ln=True)
    pdf.ln(10)

    # 基本情報
    pdf.set_jp_font(11)
    pdf.cell(0, 7, "報告日: 2024年1月20日", ln=True)
    pdf.cell(0, 7, "作業場所: 本社サーバールーム", ln=True)
    pdf.cell(0, 7, "担当: 架空エンジニアリング株式会社", ln=True)
    pdf.ln(8)

    # 宛先
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "株式会社テスト工業 情報システム部 御中", ln=True)
    pdf.ln(10)

    # 作業内容（GUIDANCEキーワード: 既設, 撤去, 移設）
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "【作業内容】", ln=True)
    pdf.set_jp_font(11)
    pdf.ln(3)
    pdf.cell(0, 7, "1. 既設サーバー撤去作業", ln=True)
    pdf.cell(0, 7, "   - 既設ラック内機器の取り外し", ln=True)
    pdf.cell(0, 7, "   - ケーブル撤去及び廃棄処理", ln=True)
    pdf.ln(5)
    pdf.cell(0, 7, "2. 機器移設工事", ln=True)
    pdf.cell(0, 7, "   - 移設先ラックへの機器設置", ln=True)
    pdf.cell(0, 7, "   - 既設配線の再接続作業", ln=True)
    pdf.ln(10)

    # 費用明細
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "【費用明細】", ln=True)
    pdf.set_jp_font(11)
    pdf.ln(3)
    pdf.cell(0, 7, "既設サーバー撤去作業 ............. 150,000円", ln=True)
    pdf.cell(0, 7, "機器移設工事 ..................... 100,000円", ln=True)
    pdf.ln(3)
    pdf.cell(0, 6, "─────────────────────────", ln=True)
    pdf.cell(0, 7, "小計 ............................. 250,000円", ln=True)
    pdf.cell(0, 7, "消費税（10%）..................... 25,000円", ln=True)
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "合計 ............................. 275,000円", ln=True)
    pdf.ln(10)

    # 特記事項
    pdf.set_jp_font(11)
    pdf.cell(0, 8, "【特記事項】", ln=True)
    pdf.set_jp_font(10)
    pdf.cell(0, 6, "・既設機器の一部は再利用のため保管", ln=True)
    pdf.cell(0, 6, "・移設作業は夜間帯に実施", ln=True)

    filepath = OUTPUT_DIR / "demo_guidance.pdf"
    pdf.output(str(filepath))
    print(f"Created: {filepath}")


def create_capital2_pdf():
    """
    CAPITAL_LIKE用（別様式）: 発注書形式
    キーワード: 購入, 整備
    """
    pdf = JapanesePDF()
    pdf.add_page()

    # タイトル
    pdf.set_jp_font(24)
    pdf.cell(0, 20, "発 注 書", align="C", ln=True)
    pdf.ln(10)

    # 発注情報
    pdf.set_jp_font(10)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "発注番号: PO-2024-0312", ln=True)
    pdf.cell(100, 6, "")
    pdf.cell(0, 6, "発注日: 2024年3月12日", ln=True)
    pdf.ln(5)

    # 発注先
    pdf.set_jp_font(12)
    pdf.cell(0, 8, "株式会社オフィス機器販売 御中", ln=True)
    pdf.ln(5)

    # 発注元
    pdf.set_jp_font(10)
    pdf.cell(0, 6, "発注元: 架空産業株式会社 総務部", ln=True)
    pdf.cell(0, 6, "担当者: 山田太郎", ln=True)
    pdf.ln(8)

    # 件名
    pdf.set_jp_font(11)
    pdf.cell(0, 8, "件名: オフィス機器購入及び環境整備", ln=True)
    pdf.ln(8)

    # 明細テーブルヘッダー
    pdf.set_jp_font(10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(70, 8, "品目", border=1, fill=True)
    pdf.cell(25, 8, "数量", border=1, fill=True)
    pdf.cell(30, 8, "単価", border=1, fill=True)
    pdf.cell(35, 8, "金額", border=1, ln=True, fill=True)

    # 明細行（CAPITAL_LIKEキーワード: 購入, 整備）
    items = [
        ("業務用PC購入", "10台", "150,000", "1,500,000円"),
        ("モニター購入", "10台", "50,000", "500,000円"),
        ("デスク・チェア購入", "10セット", "80,000", "800,000円"),
        ("OAフロア整備工事", "1式", "300,000", "300,000円"),
        ("電源環境整備", "1式", "200,000", "200,000円"),
    ]

    pdf.set_fill_color(255, 255, 255)
    for item in items:
        pdf.cell(70, 8, item[0], border=1)
        pdf.cell(25, 8, item[1], border=1)
        pdf.cell(30, 8, item[2], border=1)
        pdf.cell(35, 8, item[3], border=1, ln=True)

    # 合計
    pdf.ln(8)
    pdf.set_jp_font(11)
    pdf.cell(100, 7, "")
    pdf.cell(0, 7, "小計: 3,300,000円", ln=True)
    pdf.cell(100, 7, "")
    pdf.cell(0, 7, "消費税: 330,000円", ln=True)
    pdf.set_jp_font(12)
    pdf.cell(100, 8, "")
    pdf.cell(0, 8, "合計: 3,630,000円", ln=True)

    filepath = OUTPUT_DIR / "demo_capital2.pdf"
    pdf.output(str(filepath))
    print(f"Created: {filepath}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("デモ用PDF作成 v3（fpdf2使用）")
    print("=" * 50)
    print()

    # 4パターン作成
    create_capital_pdf()
    create_expense_pdf()
    create_guidance_pdf()
    create_capital2_pdf()

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
    print()
    print("次のステップ: python scripts/test_demo_pdfs.py でテスト実行")


if __name__ == "__main__":
    main()
