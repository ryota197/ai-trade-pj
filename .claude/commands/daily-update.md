---
description: Update today's daily note
allowed-tools: mcp__obsidian-mcp-tools__get_vault_file, mcp__obsidian-mcp-tools__patch_vault_file, mcp__obsidian-mcp-tools__show_file_in_obsidian
---

# Daily Note更新

今日のデイリーノートに内容を追記してください。

## 設定
- 対象: `00_Development_Notes/ai-trade-pj/daily_notes/YYYY-MM-DD.md`（今日の日付）

## 引数
$ARGUMENTS に追記内容が渡されます。

## 手順
1. 今日のデイリーノートを取得
2. 引数の内容を適切なセクションに追記
   - タスク系 → Tasks セクション（チェックボックス形式）
   - それ以外 → Notes セクション
3. patch_vault_file で追記
4. 完了メッセージを表示
