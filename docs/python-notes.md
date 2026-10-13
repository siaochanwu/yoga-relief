# Python 概念筆記

開發過程中，每個功能實際用到的 Python 概念與原因。

## Task 1：專案骨架

- **src layout**：程式碼放在 `src/yoga_relief/` 而不是專案根目錄。好處是測試一定是對「安裝後的套件」跑，不會因為當前目錄剛好在根目錄而意外 import 成功。
- **pyproject.toml**：現代 Python 專案的單一設定檔。`[project]` 是套件中繼資料與相依，`[dependency-groups] dev` 是只有開發才裝的工具，`[tool.*]` 是各工具的設定。
- **uv**：同時負責建立虛擬環境、鎖定版本（`uv.lock`）、執行指令。`uv run X` 等於「在專案的 venv 裡跑 X」，不用手動 activate。
- **`__init__.py`**：有這個檔的資料夾才是「套件」，可以被 `import yoga_relief`。
