# 🔧 文豪地図システム v3.0 セットアップガイド

## 📋 初期セットアップ

### 1. **システム要件**
- Python 3.12+
- OpenAI APIアカウント
- 2GB以上のディスク容量

### 2. **依存関係インストール**
```bash
pip install -r requirements.txt
```

### 3. **OpenAI APIキー設定**

#### 🎯 推奨方法: 対話式セットアップ
```bash
python main.py setup init --interactive
```

#### ⚡ クイックセットアップ
```bash
# ユーザーディレクトリに設定保存（推奨）
python main.py setup init --api-key "sk-..." --user-config

# プロジェクトディレクトリに設定保存
python main.py setup init --api-key "sk-..."
```

#### 📋 手動セットアップ
```bash
# 1. 設定ファイルをコピー
cp env.example .env

# 2. .envファイルを編集
nano .env
# OPENAI_API_KEY=your_actual_api_key_here

# 3. 設定確認
python main.py setup check
```

### 4. **OpenAI APIキー取得方法**

1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. アカウントにログイン（または新規作成）
3. 「+ Create new secret key」をクリック
4. キー名を入力（例: "bungo-map-system"）
5. 生成されたキーをコピー（一度しか表示されません！）

### 5. **設定確認**
```bash
python main.py setup check
```

### 6. **AI機能テスト**
```bash
python main.py ai test-connection
```

## 🛡️ セキュリティのベストプラクティス

### APIキー管理
- ✅ **DO**: 環境変数または設定ファイルで管理
- ✅ **DO**: 定期的にキーをローテーション
- ✅ **DO**: .gitignoreでAPIキーを除外
- ❌ **DON'T**: コードに直接記述
- ❌ **DON'T**: GitHubなど公開リポジトリにプッシュ
- ❌ **DON'T**: 他人と共有

### 設定ファイルの種類と用途

| ファイル | 用途 | 場所 | Git管理 |
|---------|------|------|---------|
| `env.example` | テンプレート | プロジェクト | ✅ 管理対象 |
| `.env` | 開発用設定 | プロジェクト | ❌ 除外 |
| `~/.bungo_map/.env` | ユーザー設定 | ホームディレクトリ | ❌ 除外 |

## 🌍 配布・デプロイメント

### 開発者向け配布
```bash
# リポジトリクローン
git clone https://github.com/your-username/bungo-map-system-v3.git
cd bungo-map-system-v3

# セットアップ
pip install -r requirements.txt
python main.py setup init --interactive
```

### エンドユーザー向け配布
```bash
# ZIP配布の場合
# 1. env.example が含まれていることを確認
# 2. README.md にセットアップ手順を明記
# 3. .env ファイルは除外（セキュリティ）

# パッケージ配布の場合
pip install bungo-map-system
bungo-map setup init --interactive
```

### Docker環境
```dockerfile
# Dockerfile例
FROM python:3.12-slim

# 環境変数でAPIキー設定
ENV OPENAI_API_KEY=""

# アプリケーション設定
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# 起動時に設定チェック
CMD ["python", "main.py", "setup", "check"]
```

```bash
# Docker実行
docker run -e OPENAI_API_KEY="sk-..." bungo-map-system
```

### クラウドデプロイ

#### Heroku
```bash
# 環境変数設定
heroku config:set OPENAI_API_KEY="sk-..."

# アプリデプロイ
git push heroku main
```

#### AWS/GCP
```bash
# AWS Secrets Manager
aws secretsmanager create-secret --name bungo-map-openai-key --secret-string "sk-..."

# 環境変数注入
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id bungo-map-openai-key --query SecretString --output text)
```

## 🔧 トラブルシューティング

### よくある問題

#### 1. **APIキーエラー**
```
❌ OpenAI APIキーが設定されていません
```
**解決策**: `python main.py setup init --interactive`

#### 2. **APIキー形式エラー**
```
❌ API接続エラー: Invalid API key
```
**解決策**: 
- APIキーが正しいか確認
- キーが有効期限内か確認
- OpenAIアカウントに残高があるか確認

#### 3. **設定ファイルが見つからない**
```
⚠️ 設定ファイル: なし
```
**解決策**: `python main.py setup init --user-config`

#### 4. **権限エラー**
```
Permission denied: ~/.bungo_map/.env
```
**解決策**: `chmod 600 ~/.bungo_map/.env`

### ログとデバッグ
```bash
# 詳細ログを有効化
export LOG_LEVEL=DEBUG
python main.py ai analyze --limit 1

# 設定状況の詳細確認
python main.py setup check
```

## 📞 サポート

- 🐛 **バグ報告**: GitHub Issues
- 💬 **質問**: Discussions
- 📧 **セキュリティ問題**: security@example.com

---

**重要**: APIキーは機密情報です。取り扱いには十分注意してください。 