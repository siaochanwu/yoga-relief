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

## Task 5：分流規則

- **純函式**：輸入決定輸出、沒有副作用。最容易測，也最容易被其他地方（API、產生腳本）重用。
- **`pytest.mark.parametrize`**：一個測試函式跑多組資料，每組獨立顯示 pass/fail。邊界案例（差一點就命中）一定要列進去。
- **`is` 比較 Enum 成員**：Enum 成員是單例，用 `is` 比 `==` 更明確表達「是不是同一個成員」。
- **把中性名稱給中間變數**（`chronic_severe`、`injury_not_mild`）：規則讀起來像規格書，之後加規則只要多一行。

## Task 6：AdviceStore

- **`logging` 而不是 `print`**：模組頂端 `log = logging.getLogger(__name__)`，訊息會帶模組名稱、可以設等級、測試可用 `caplog` 擷取。
- **atomic write**：先寫到 `.tmp` 再 `os.replace()`。寫到一半當機也不會留下半截的 JSON（腳本每筆都存檔，這很重要）。
- **`json.dumps(ensure_ascii=False)`**：中文直接存，不然檔案全是 `小`，diff 看不懂。
- **`sorted()` key 再輸出**：同樣內容永遠產出同樣檔案，git diff 只會顯示真的改了的部分。
- **dunder 方法 `__len__`、`__contains__`**：讓自訂類別支援 `len(store)` 與 `"k" in store`，用起來像內建容器。
- **`set(a) == set(b)`**：比較「集合是否相同」而忽略順序。
- **`Path.with_suffix` / `Path.exists`**：`pathlib` 把路徑當物件操作，比字串拼接安全。

## Task 7：呼叫 Claude

- **依賴注入（dependency injection）**：`generate_advice(client, ...)` 把 client 當參數傳進來，而不是在函式裡自己 `anthropic.Anthropic()`。測試就能塞一個假的 `FakeClient`，不用真的打 API、不用 key、不花錢。
- **鴨子型別（duck typing）**：`FakeClient` 沒有繼承任何 SDK 類別，只要有 `.messages.parse()` 就能用。Python 看的是「有沒有這個方法」，不是「是不是這個類別」。
- **keyword-only 參數**（`*` 之後的參數）：強迫呼叫端寫 `model=...`，避免位置搞錯。
- **structured output**：`output_format=AdviceOutput` 讓 SDK 要求模型輸出符合 pydantic schema 的 JSON，並直接解析成物件（`response.parsed_output`）。
- **信任但要驗證**：schema 只保證「形狀」對，不保證「內容」對（例如 `order` 可能漏一個 id）。所以還是要自己 `_validate`。
- **triple-quoted string 當 prompt**：多行字串放在模組層級當常數，測試可以直接比對。
- **`getattr(obj, "name", default)`**：安全地讀可能不存在的屬性。

## Task 8：產生腳本

- **邏輯放套件、入口放 scripts/**：`scripts/build_advice.py` 只有三行，真正的程式在 `yoga_relief/build_advice.py`。這樣測試可以 `import` 它，而 `scripts/` 不需要是套件。
- **`if __name__ == "__main__":`**：只有「直接執行這個檔」時才跑；被 import 時不會。
- **`@dataclass`**：自動產生 `__init__`、`__eq__`、`__repr__`，適合純資料的小物件（這裡的 `Summary`）。`field(default_factory=list)` 是可變預設值的正確寫法。
- **`itertools.product`**：多層 for 迴圈的扁平寫法，產生所有組合。
- **`enumerate(..., start=1)`**：同時拿到索引與元素，`start=1` 讓進度顯示從 1 開始。
- **`Callable[[str], None]` 當參數**：把「怎麼輸出 log」也注入進來，測試可以收集訊息而不是印到螢幕。
- **區域 import**（`main()` 裡的 `import anthropic`）：讓只跑測試的人不需要 API 相關設定就能 import 這個模組；平常不建議，但入口函式是合理的例外。
- **`except Exception` 的取捨**：一般程式碼應該抓具體的例外；長時間跑的批次腳本例外，因為「一筆壞了繼續跑」比「整批中斷」更重要，所以明確註解原因並用 `# noqa` 標記。
- **`datetime.now(UTC).isoformat()`**：永遠用帶時區的時間，不要 naive datetime。

## Task 9：設定、Service、API

- **pydantic-settings**：`BaseSettings` 的欄位自動從環境變數與 `.env` 讀，型別轉換（`"true"` → `True`）也包辦。`validation_alias` 指定環境變數名稱。
- **三層分工**：`api.py`（HTTP：status code、request/response）→ `service.py`（流程：查部位、分流、查 advice、排序）→ `repository/advisor/triage`（各自一件事）。service 不知道 HTTP，所以 `test_service.py` 不用啟動 web server。
- **application factory `create_app()`**：每次呼叫都建一個獨立的 app，參數可換資料路徑與設定。測試用 `tmp_path` 就不會互相污染；模組層級的 `app = create_app()` 給 uvicorn 用。
- **`app.state`**：FastAPI 提供的「掛東西」的地方，路由用 `request.app.state.service` 取得，不用全域變數。
- **`HTTPException` + `raise ... from e`**：把內部例外轉成 HTTP 狀態碼，同時保留原因鏈。
- **`response_model=`**：FastAPI 依 pydantic 模型序列化輸出並產生 OpenAPI 文件（打開 `/docs` 看）。
- **`TestClient`**：不開 port、直接在程序內呼叫 app，測 HTTP 層最快的方法。
- **`monkeypatch.setenv / delenv`**：測試裡暫時改環境變數，測完自動還原。
- **`dict | dict`**（3.9+）：合併兩個 dict，右邊覆蓋左邊，測試裡用來「基底 + 覆寫」。
- **`model_copy(update=...)`**：pydantic 物件是不可變思維，要改就產生新的拷貝。

## Task 10：前端骨架（Python 的部分）

- **用 Python 測前端資產**：`test_static.py` 用 `re` 解析 SVG，確認每個部位在它宣告的視圖裡都有可點區塊。前端沒有自動化測試框架時，這種「資料一致性測試」是最便宜的保險。
- **`re.S`（DOTALL）**：讓 `.` 也能匹配換行，抓多行的 `<g>...</g>`。
- **`rf"..."`**：raw + f-string 同時用，正則裡的反斜線不用跳脫，又能插變數。
- **`StaticFiles` 與 `FileResponse`**：FastAPI 直接當靜態檔伺服器，不需要 nginx 就能跑整個 app。
