# Python 概念筆記

開發過程中，每個功能實際用到的 Python 概念與原因。

## Task 1：專案骨架

- **src layout**：程式碼放在 `src/yoga_relief/` 而不是專案根目錄。好處是測試一定是對「安裝後的套件」跑，不會因為當前目錄剛好在根目錄而意外 import 成功。
- **pyproject.toml**：現代 Python 專案的單一設定檔。`[project]` 是套件中繼資料與相依，`[dependency-groups] dev` 是只有開發才裝的工具，`[tool.*]` 是各工具的設定。
- **uv**：同時負責建立虛擬環境、鎖定版本（`uv.lock`）、執行指令。`uv run X` 等於「在專案的 venv 裡跑 X」，不用手動 activate。
- **`__init__.py`**：有這個檔的資料夾才是「套件」，可以被 `import yoga_relief`。

## Task 2：資料模型

- **`StrEnum`**（Python 3.11+）：成員同時是字串，`Severity.MILD == "mild"` 為真，f-string 直接印出值。API 傳 `"mild"` 進來，pydantic 會自動轉成 `Severity.MILD`。
- **pydantic `BaseModel`**：宣告欄位與型別，建立物件時自動驗證、型別轉換；不合法就丟 `ValidationError`。FastAPI 直接用它產生 422 回應。
- **`Field(min_length=1)`**：對 list 做「至少一項」的限制，不用自己寫 if。
- **類別繼承當作「欄位擴充」**：`AdviceRequest(Answers)` 多一個 `body_part`，所以任何收 `Answers` 的函式都能直接收 `AdviceRequest`（里氏替換）。
- **可變預設值**：pydantic 的 `cautions: list[str] = []` 是安全的（每個實例會拷貝）；一般 Python 函式的預設參數 `def f(x=[])` 則會共用同一個 list，這是常見陷阱。
