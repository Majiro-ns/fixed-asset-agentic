"""
固定資産台帳インポートモジュール

CSV/Excelファイルから固定資産台帳を読み込み、
統一されたフォーマットの辞書リストとして返す。
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# カラム名のマッピング定義
# キー: 正規化後のカラム名、値: 対応する可能性のある元カラム名パターン
COLUMN_MAPPINGS = {
    "name": [
        "資産名", "資産名称", "品名", "名称", "資産", "固定資産名",
        "asset_name", "name", "item_name", "description"
    ],
    "amount": [
        "取得価額", "取得価格", "価額", "金額", "取得金額", "購入価格",
        "acquisition_cost", "amount", "cost", "price", "value"
    ],
    "account": [
        "勘定科目", "科目", "資産区分", "資産種類", "分類",
        "account", "account_name", "category", "asset_type"
    ],
    "useful_life": [
        "耐用年数", "耐用", "年数", "償却年数", "法定耐用年数",
        "useful_life", "life", "years", "depreciation_years"
    ],
}

# オプショナルカラムのマッピング
OPTIONAL_COLUMN_MAPPINGS = {
    "acquisition_date": [
        "取得日", "取得年月日", "購入日", "取得日付",
        "acquisition_date", "purchase_date", "date"
    ],
    "asset_id": [
        "資産番号", "管理番号", "資産コード", "No", "番号",
        "asset_id", "asset_no", "id", "code"
    ],
    "location": [
        "設置場所", "所在地", "場所", "使用場所",
        "location", "place"
    ],
    "department": [
        "部門", "部署", "管理部門",
        "department", "dept"
    ],
}


class LedgerImportError(Exception):
    """台帳インポート時のエラー"""
    pass


class ColumnMappingError(LedgerImportError):
    """カラムマッピングエラー"""
    pass


class ValidationError(LedgerImportError):
    """バリデーションエラー"""
    pass


def _normalize_column_name(col: str) -> str:
    """カラム名を正規化（空白除去、小文字化）"""
    if not isinstance(col, str):
        col = str(col)
    # 全角・半角スペース、改行を除去
    col = re.sub(r'[\s\u3000]+', '', col)
    return col.lower().strip()


def _find_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """
    DataFrameのカラム名から、必須カラムへのマッピングを検出

    Returns:
        Dict[str, str]: {正規化カラム名: 元カラム名}
    """
    mapping = {}
    normalized_to_original = {_normalize_column_name(c): c for c in df_columns}

    # 必須カラムのマッピング
    for target_col, patterns in COLUMN_MAPPINGS.items():
        for pattern in patterns:
            normalized_pattern = _normalize_column_name(pattern)
            if normalized_pattern in normalized_to_original:
                mapping[target_col] = normalized_to_original[normalized_pattern]
                break

    # オプショナルカラムのマッピング
    for target_col, patterns in OPTIONAL_COLUMN_MAPPINGS.items():
        for pattern in patterns:
            normalized_pattern = _normalize_column_name(pattern)
            if normalized_pattern in normalized_to_original:
                mapping[target_col] = normalized_to_original[normalized_pattern]
                break

    return mapping


def _validate_required_columns(mapping: Dict[str, str]) -> None:
    """必須カラムが全て存在するか検証"""
    required = set(COLUMN_MAPPINGS.keys())
    found = set(mapping.keys()) & required
    missing = required - found

    if missing:
        missing_names = {
            "name": "資産名",
            "amount": "取得価額",
            "account": "勘定科目",
            "useful_life": "耐用年数",
        }
        missing_display = [missing_names.get(m, m) for m in missing]
        raise ColumnMappingError(
            f"必須カラムが見つかりません: {', '.join(missing_display)}"
        )


def _convert_to_numeric(value: Any) -> Optional[float]:
    """値を数値に変換"""
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # カンマ、円記号、スペースを除去
        cleaned = re.sub(r'[,\s¥￥円]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def _convert_to_int(value: Any) -> Optional[int]:
    """値を整数に変換（耐用年数用）"""
    numeric = _convert_to_numeric(value)
    if numeric is not None:
        return int(numeric)
    return None


def _read_csv_with_encoding(file_path: str) -> pd.DataFrame:
    """
    UTF-8 → Shift-JIS の順でCSVを読み込む
    """
    encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'cp932']

    last_error = None
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            # 空のDataFrameでないか確認
            if not df.empty:
                return df
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue

    raise LedgerImportError(
        f"CSVファイルの読み込みに失敗しました。対応エンコーディング: UTF-8, Shift-JIS\n"
        f"詳細: {last_error}"
    )


def _read_excel(file_path: str) -> pd.DataFrame:
    """
    Excelファイルを読み込む
    openpyxlが利用可能な場合のみ動作
    """
    try:
        # openpyxlがインストールされているか確認
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except ImportError:
        raise LedgerImportError(
            "Excelファイルの読み込みにはopenpyxlが必要です。\n"
            "pip install openpyxl でインストールしてください。"
        )
    except Exception as e:
        raise LedgerImportError(f"Excelファイルの読み込みに失敗しました: {e}")


def import_ledger(file_path: str) -> List[Dict[str, Any]]:
    """
    固定資産台帳ファイルを読み込み、統一フォーマットの辞書リストを返す

    Args:
        file_path: CSVまたはExcelファイルのパス

    Returns:
        List[Dict[str, Any]]: 固定資産データのリスト
        [
            {
                "name": "ノートPC",
                "amount": 150000,
                "account": "器具備品",
                "useful_life": 4,
                # 以下はオプショナル（存在する場合のみ）
                "acquisition_date": "2024-04-01",
                "asset_id": "A001",
                "location": "本社",
                "department": "総務部"
            },
            ...
        ]

    Raises:
        LedgerImportError: ファイル読み込みに失敗した場合
        ColumnMappingError: 必須カラムが見つからない場合
        ValidationError: データのバリデーションに失敗した場合
    """
    path = Path(file_path)

    if not path.exists():
        raise LedgerImportError(f"ファイルが見つかりません: {file_path}")

    # ファイル形式に応じて読み込み
    suffix = path.suffix.lower()
    if suffix == '.csv':
        df = _read_csv_with_encoding(file_path)
    elif suffix in ['.xlsx', '.xls']:
        df = _read_excel(file_path)
    else:
        raise LedgerImportError(
            f"サポートされていないファイル形式です: {suffix}\n"
            "対応形式: .csv, .xlsx, .xls"
        )

    if df.empty:
        raise LedgerImportError("ファイルにデータが含まれていません")

    # カラムマッピングを検出
    column_mapping = _find_column_mapping(df.columns.tolist())

    # 必須カラムの検証
    _validate_required_columns(column_mapping)

    # データを変換
    results = []
    errors = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # Excelの行番号（ヘッダー行=1）

        try:
            record = {}

            # 必須カラムの処理
            # name
            name_col = column_mapping['name']
            name_value = row[name_col]
            if pd.isna(name_value) or str(name_value).strip() == '':
                errors.append(f"行{row_num}: 資産名が空です")
                continue
            record['name'] = str(name_value).strip()

            # amount
            amount_col = column_mapping['amount']
            amount_value = _convert_to_numeric(row[amount_col])
            if amount_value is None:
                errors.append(f"行{row_num}: 取得価額を数値に変換できません: {row[amount_col]}")
                continue
            record['amount'] = amount_value

            # account
            account_col = column_mapping['account']
            account_value = row[account_col]
            if pd.isna(account_value) or str(account_value).strip() == '':
                errors.append(f"行{row_num}: 勘定科目が空です")
                continue
            record['account'] = str(account_value).strip()

            # useful_life
            life_col = column_mapping['useful_life']
            life_value = _convert_to_int(row[life_col])
            if life_value is None:
                errors.append(f"行{row_num}: 耐用年数を数値に変換できません: {row[life_col]}")
                continue
            if life_value <= 0:
                errors.append(f"行{row_num}: 耐用年数は正の整数である必要があります: {life_value}")
                continue
            record['useful_life'] = life_value

            # オプショナルカラムの処理
            for opt_col in OPTIONAL_COLUMN_MAPPINGS.keys():
                if opt_col in column_mapping:
                    opt_value = row[column_mapping[opt_col]]
                    if not pd.isna(opt_value):
                        record[opt_col] = str(opt_value).strip()

            results.append(record)

        except Exception as e:
            errors.append(f"行{row_num}: 処理エラー: {e}")
            continue

    # エラーがあれば報告（ただし部分的に成功した場合は結果も返す）
    if errors and not results:
        raise ValidationError(
            f"全てのデータでバリデーションエラーが発生しました:\n" +
            "\n".join(errors[:10])  # 最初の10件のみ表示
        )

    if errors:
        # 警告として記録（ログ出力は呼び出し側に任せる）
        import warnings
        warnings.warn(
            f"{len(errors)}件のデータでエラーが発生しました:\n" +
            "\n".join(errors[:5]),
            UserWarning
        )

    return results


def import_ledger_safe(file_path: str) -> Dict[str, Any]:
    """
    import_ledgerの安全版。エラー情報も含めて結果を返す

    Returns:
        Dict[str, Any]: {
            "success": bool,
            "data": List[Dict] or None,
            "error": str or None,
            "warnings": List[str]
        }
    """
    import warnings

    result = {
        "success": False,
        "data": None,
        "error": None,
        "warnings": []
    }

    # 警告をキャプチャ
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")

        try:
            data = import_ledger(file_path)
            result["success"] = True
            result["data"] = data
        except LedgerImportError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"予期しないエラー: {e}"

        # 警告を収集
        result["warnings"] = [str(w.message) for w in caught_warnings]

    return result
