# 本気の「運」攻略戦略

信じる前に、確かめる。万年不運な男が、運を論理で攻略する実験室。

## 手元で動かす
```
python build.py            # 今日の内容で docs/ を生成
python build.py 2026-10-11 # 日付を指定して生成
python -m pytest -q        # 暦のテスト（pytest が必要）
```
生成後、`docs/index.html` をブラウザで開くと確認できます。

## 公開
Cloudflare Pages で `main` ブランチの `docs` を公開します（ビルドコマンドは空、出力ディレクトリは `docs`）。
毎日 0:05 JST に GitHub Actions が `docs` を更新してコミットし、それを検知して Cloudflare Pages が自動で公開し直します。
