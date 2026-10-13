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

## Task 3：Repository

- **Repository 模式**：把「資料從哪來、怎麼驗證」包在一個類別裡，其他程式只呼叫 `poses_for()`，不碰 YAML。以後換成資料庫，只改這一個檔。
- **`@classmethod` 當替代建構子**：`Repository.load(dir)` 讀檔後再呼叫 `cls(...)`；建構子本身只收已經是物件的資料，測試就能不經過檔案系統直接建。
- **`@property`**：讓 `repo.body_parts` 看起來像屬性但其實是方法，順便回傳拷貝避免外部改到內部 list。
- **自訂例外 `DataError(ValueError)`**：啟動時抓這一種例外就能印出清楚訊息；繼承 `ValueError` 讓不認識它的程式也能用一般方式處理。
- **`raise ... from e`**：保留原始例外的追蹤鏈，除錯時看得到底層原因。
- **`TypeAdapter(list[Pose])`**：對「不是 BaseModel 的型別」（這裡是 list）做 pydantic 驗證。
- **PEP 695 泛型語法 `def f[T](...)`**（3.12+）：宣告型別變數，讓型別檢查器知道回傳的是 `list[T]`。
- **`Counter`**：數重複用的標準工具，比自己寫 dict 計數簡潔。

## Task 4：正式資料檔

- **資料即程式碼**：動作內容放 YAML 隨 git 版控，改內容走 PR、有歷史、有測試保護（`test_data.py`）。這是「設定與程式分離」但又「一起版控」的折衷。
- **YAML 與 Python 型別的對應**：`[a, b]` → list，`key: value` → dict，`[]` → 空 list。載入後立刻用 pydantic 轉成物件，之後程式碼不再碰 dict。
- **測試分層**：`test_repository.py` 用小的假資料測「規則」，`test_data.py` 用真資料測「內容」。兩者分開，規則改了不用改內容測試。
