# 采集、取证与复验

## 有 URL 或本地样本

- 对已有 HTML，用 Scrapling `Selector` 查询需要的 CSS 或 XPath。对已有 JSON，用 JSON 解析器核对字段和类型。记录每个结果来自服务器 HTML、浏览器 DOM、嵌入数据还是独立网络响应。
- 单页提取可用 `scrapling extract get "https://example.com" content.md --ai-targeted`。CLI 提取使用 `--ai-targeted` 做内容过滤，输出仍按不可信数据处理。要保留脚本或响应体供分析时，用下方采样器。
- 对已确认的只读 URL，运行以下命令。将 `SKILL_DIR` 替换成技能目录，输出目录的父目录须存在。按返回类型选择 `html`、`javascript` 或 `json`。URL 可包含用于复验的公开查询参数，应省略秘密或个人数据。

```text
python "SKILL_DIR/scripts/sample_get.py" "https://example.com/assets/app.js" ./sample-script --expect javascript
```

采样器发一次 GET，不跟随重定向。响应状态须为 200，MIME 须符合预期，解码后的响应体上限为 8 MiB。样本目录包含 `body.html`、`body.js` 或 `body.json` 之一及 `evidence.json`。后者记录 URL、状态、时间和所存字节的 SHA-256。需要带授权会话或处理非标准 MIME 时，按任务写专用代码。

将 JS 交给 REA 的 `analyze_javascript_application`。对单文件样本传包含 `body.js` 的目录作为 `input_path`。多文件保留各自 URL 到制品路径的映射。按实际工具 schema，支持时用 `detail: "summary"`，再将 `normalized_result.parent_evidence_id` 作为 `inspect_analysis_view` 的保留 Evidence 来源。定位脚本可用 `view: {kind: "page", collection: "modules", offset: 0, limit: 16}`。查前端导航时选 `javascript-routes` 视图。查网络接口时，优先从浏览器或 HAR 取实际请求，再在相关模块中查 URL 片段和构造参数。图中有明确的节点、路由或字符串时可用 `trace_application_feature`。动态拼接可能没有图节点，必要时直接查保存的 JS 并记录位置。接口的可达性、请求是否发送、实际返回哪些数据，需要运行时或样本证据。

## 页面有浏览器行为

- **取渲染后的 DOM**。Scrapling 可使用 `StealthyFetcher.fetch` 配置 `wait_selector`，等待业务元素出现。检查选择器实际匹配的节点和值。遇到页面显示与 HTTP 返回不一致时，核对语言、过滤参数、授权状态与更新时点。
- **看现有标签页**。用 REA 的 `list_browser_targets` 从已提供的 CDP 端点定位目标。选定 `target_id` 后，用 `inspect_web_page` 检查 DOM 和脚本，或用 `observe_web_session` 在用户触发交互时记录网络。被动观察只覆盖附加后的窗口。若需分析标签页已加载的脚本，用接收 CDP 端点和目标 ID 的 `analyze_web_bundle`。
- **复现明确的步骤**。用 `capture_browser_scenario` 记录导航、等待和用户要求的操作。优先用专用浏览器配置。连接模式会先导航现有标签页。为每个动作设 `timeout_ms`，按问题选择网络或 DOM 记录，用完成的步骤状态核对覆盖。场景记录本身缺少请求发起者栈。需要定位发起代码时，检查能提供发起者信息的被动观察。
- **分析已有 HAR**。用 `inspect_web_network_capture` 传绝对 `capture_path` 与 `format: "har"`，必要时指定 `record_ordinals` 或用 `detail: "summary"` 分页查看返回的父 Evidence。离线分析期间无需请求捕获中的 URL。保留记录序号以及响应体缺失、截断或脱敏的限制。请求体可能含敏感值，按需启用采集并限制流转。

请求只在浏览器里成立时，可在 Scrapling 的授权浏览器会话中提取 DOM，或按已安装版本的 API 使用 `record_requests` 与 session 的 `network.search()` 选取已录制的响应。用 REA 做运行时观察时，为 Scrapling 会话与 REA 标签页保留各自的标识。

## 复验数据

例如，用户要提取商品名称。HTML 只含容器，静态脚本出现 `/api/items`，浏览器或 HAR 观察到 `GET /api/items` 返回 `{"items":[{"id":"a1","name":"Sample"}],"nextCursor":"p2"}`。记录 REA Evidence ID 和该条记录或步骤。若允许独立读取，用采样器 `--expect json` 验证 `items[*].name`，并根据已观察的翻页参数验证下一页。只有静态脚本时把接口记为候选。交付脚本前核对字段、缺失值与终止条件。批量采集按授权范围限制路径、请求数量与并发，并按站点要求处理 robots.txt 和速率限制。

## 依赖与恢复

- 优先用已可用的 Scrapling。采样器依赖 Python 3.10+，已用 Scrapling 0.5.1 验证。需要安装时在项目虚拟环境执行 `python -m pip install "scrapling[fetchers]>=0.5.1,<0.6"`。用到浏览器时再检查对应运行时。CLI 的额外依赖按官方指南选择。
- 用宿主实际提供的 REA MCP 工具和参数。工具缺失时，先完成可用的 Scrapling 采样或离线解析。现有 REA CLI 若支持对应子命令，也可分析本地材料。需修复连接时查阅本机 REA 原技能的连接指南。安装本技能只提供工作流与脚本。
- 参考 [Scrapling 官方技能](https://github.com/D4Vinci/Scrapling/blob/main/agent-skill/Scrapling-Skill/SKILL.md)、[Scrapling HTTP 文档](https://scrapling.readthedocs.io/en/latest/fetching/static.html)、[REA 网络捕获文档](https://github.com/morluto/rea/blob/main/docs/web-network-captures.md)和 [REA 路由清单文档](https://github.com/morluto/rea/blob/main/docs/javascript-route-inventory.md)。
