# Python lru_cache

## 概要

`functools.lru_cache` は関数の結果をキャッシュするデコレータ。
同じ引数での呼び出し結果をメモリに保存し、2回目以降は計算をスキップして高速に返す。

---

## 基本的な使い方

```python
from functools import lru_cache

@lru_cache
def expensive_function(n: int) -> int:
    print(f"計算中: {n}")
    return n * 2

# 実行
expensive_function(5)  # "計算中: 5" が出力され、10を返す
expensive_function(5)  # 出力なし（キャッシュから10を返す）
expensive_function(3)  # "計算中: 3" が出力され、6を返す
```

---

## 名前の由来

- **LRU** = Least Recently Used（最も最近使われていないものから削除）
- キャッシュが一杯になると、最も古いエントリから削除される

---

## オプション

```python
# キャッシュサイズを指定（デフォルト: 128）
@lru_cache(maxsize=256)
def func(): ...

# 無制限キャッシュ
@lru_cache(maxsize=None)
def func(): ...

# 型を区別しない（1 と 1.0 を同じとみなす）
@lru_cache(typed=False)
def func(): ...
```

---

## ユースケース

### 1. シングルトンパターン（設定管理）

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://..."

@lru_cache
def get_settings() -> Settings:
    """設定を1回だけ読み込み、以降はキャッシュを返す"""
    return Settings()
```

### 2. 高コストな計算のキャッシュ

```python
@lru_cache(maxsize=1000)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

### 3. API呼び出し結果のキャッシュ

```python
@lru_cache(maxsize=100)
def get_stock_info(symbol: str) -> dict:
    """同じシンボルの情報は再取得しない"""
    return yfinance.Ticker(symbol).info
```

---

## 注意点

### 1. 引数はハッシュ可能である必要がある

```python
@lru_cache
def func(data: list):  # ❌ リストはハッシュ不可
    ...

@lru_cache
def func(data: tuple):  # ✅ タプルはOK
    ...
```

### 2. キャッシュはプロセス内でのみ有効

- サーバー再起動でクリアされる
- 永続化が必要なら Redis 等を使用

### 3. メモリ使用量に注意

- `maxsize=None` は無制限にメモリを消費する可能性
- 大量のユニークな引数がある場合は注意

---

## キャッシュの操作

```python
@lru_cache
def func(n): ...

# キャッシュ統計を確認
func.cache_info()
# CacheInfo(hits=10, misses=3, maxsize=128, currsize=3)

# キャッシュをクリア
func.cache_clear()
```

---

## 関連

- `@cache` (Python 3.9+): `@lru_cache(maxsize=None)` のショートカット
- `@cached_property`: プロパティ用のキャッシュ

---

## 参考

- [Python公式ドキュメント - functools.lru_cache](https://docs.python.org/ja/3/library/functools.html#functools.lru_cache)
