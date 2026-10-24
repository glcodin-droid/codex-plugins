# Codex 插件集合

这个仓库集中存放 Codex 插件。每个插件放在 `plugins/` 下的独立目录，根目录的 `.agents/plugins/marketplace.json` 提供安装目录。以后添加插件时，继续扩展这个仓库即可。

| 插件 | 用途 | 版本 |
| --- | --- | --- |
| [聊天标题格式化](plugins/codex-title-formatter/) | `MM.DD｜项目｜主题`，无项目时为 `MM.DD｜主题` | 1.0.0 |

## 安装

在安装了 Codex CLI 的电脑上执行：

```sh
codex plugin marketplace add glcodin-droid/codex-plugins
codex plugin add codex-title-formatter@glcodin-plugins
```

然后在 Codex 桌面 app 中刷新插件列表，必要时重启 app，确认「聊天标题格式化」已启用，再新建聊天使用。客户端需要支持插件市场；命令以本机 `codex plugin --help` 为准。

也可以先克隆仓库，再把本地目录注册为市场：

```sh
git clone https://github.com/glcodin-droid/codex-plugins.git
codex plugin marketplace add ./codex-plugins
codex plugin add codex-title-formatter@glcodin-plugins
```

安装和包结构参考 [OpenAI 插件文档](https://developers.openai.com/plugins/build/plugins)。GitHub 仓库分发和 OpenAI 公开插件目录的审核上架是两个独立流程。

## 使用

安装后，在新聊天中直接说：

```text
按规范格式化当前聊天标题。
```

或选择技能：

```text
$format-chat-title 将当前聊天标题整理为日期｜项目｜主题。
```

明确指定字段也可以：

```text
使用标题格式化插件：日期用 10.29，项目用 Codin，主题是修复登录失败。
```

结果：

```text
10.29｜Codin｜修复登录失败
```

没有项目：

```text
10.29｜比较鼠标连接稳定性
```

批量任务要说明范围，例如「整理项目 Codin 下 10 月 20 日至 29 日的聊天标题」。插件只处理指定范围，不会自行遍历并修改全部聊天。

## 日期和项目规则

- 日期示例不是固定日期。按用户指定日期、旧标题的有效日期、聊天创建日期的顺序确定日期；读取时间戳时使用用户时区。
- 整理历史聊天时保留原日期依据，不统一改成操作当天。
- 没有明确项目依据时省略项目段，临时目录、UUID、品牌名不会自动当作项目。
- 使用全角 `｜`，不留空字段；重复执行不会叠加日期。
- 直接重命名使用宿主提供的聊天管理工具。工具不可用时只输出建议标题，并说明未完成实际修改。

此插件是可按相关请求调用的技能包，不包含后台监听器。安装后不会自动改写所有聊天，也不会修改 app 的自动命名设置。

## 不依赖外部服务

插件不提供新的 MCP 服务，也不读取 Codex 的本地数据库或凭据。实际改名通过当前 Codex 宿主已有的会话管理工具完成。可选的 Python 3.9+ 辅助脚本使用标准库，只负责生成和校验标题文字。

```sh
python3 plugins/codex-title-formatter/skills/format-chat-title/scripts/format_title.py \
  --date 2026-10-29 --project Codin --topic 修复登录失败
```

## 开发与检查

```sh
python3 -m unittest discover -s tests -v
ruby scripts/validate_package.rb
```

前者检查日期、空项目、重复运行、旧标题和命令行行为；后者使用 Ruby 标准库检查市场、JSON/YAML、资源引用和双份清单的一致性。它们不修改真实聊天。

目录结构：

```text
.agents/plugins/marketplace.json
plugins/
  codex-title-formatter/
    plugin.json
    .codex-plugin/plugin.json
    assets/icon.svg
    skills/format-chat-title/
      SKILL.md
      agents/openai.yaml
      scripts/format_title.py
tests/
scripts/
```

添加下一款插件：在 `plugins/新插件名/` 创建插件，再向市场配置的 `plugins` 数组添加一项。插件名保持唯一，路径相对仓库根目录。

## 许可

[MIT](LICENSE)
