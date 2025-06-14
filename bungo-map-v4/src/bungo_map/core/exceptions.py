"""
Bungo Map v4.0 Custom Exceptions

システム専用の例外クラス定義
"""


class BungoMapError(Exception):
    """Bungo Map基底例外"""
    pass


class DatabaseError(BungoMapError):
    """データベース関連エラー"""
    pass


class ExtractionError(BungoMapError):
    """地名抽出関連エラー"""
    pass


class ValidationError(BungoMapError):
    """データ検証エラー"""
    pass


class APIError(BungoMapError):
    """API関連エラー"""
    pass


class ConfigurationError(BungoMapError):
    """設定関連エラー"""
    pass


class MigrationError(DatabaseError):
    """データ移行エラー"""
    pass


class SchemaError(DatabaseError):
    """スキーマ関連エラー"""
    pass 