# Interactive Python Editor

## 功能说明

这是一个交互式 Python 编辑器，支持以下功能：

1. **代码高亮与主题切换**：
   - 支持多种编辑器主题（如 Monokai、Eclipse、Dracula 等）。
   - 用户可通过下拉菜单选择不同主题。

2. **代码语法检查**：
   - 实时检查代码的语法错误，并在错误处显示详细提示信息。
   - 鼠标悬停在错误标记上时，显示语法错误的详细描述。

3. **代码自动补全**：
   - 支持 Python 代码自动补全功能。
   - 用户可通过 `Ctrl-Space` 快捷键触发补全，也支持自动触发。

4. **代码运行功能**：
   - 点击 `运行` 按钮执行代码。
   - 支持文本和图像类型的输出。

5. **结果自适应显示**：
   - 运行结果的显示区域会根据内容的高度自动调整，不会出现滚动条。

## 文件说明

### 文件结构
- `index.html`：主 HTML 文件，包含代码编辑器的结构和基础功能。
- 引入的外部库：
  - [CodeMirror](https://codemirror.net/) 用于代码编辑器。
  - 相关主题和插件（如 Lint、Hint）。

### 主要功能实现

#### 代码高亮与主题切换
```html
<select id="theme" onchange="changeTheme()">
    <option value="default">Default</option>
    <option value="monokai" selected>Monokai</option>
    <option value="eclipse">Eclipse</option>
    <option value="dracula">Dracula</option>
</select>
```
- 用户可以通过下拉菜单选择不同的编辑器主题。
- `changeTheme()` 函数动态应用所选主题：
```javascript
function changeTheme() {
    const theme = document.getElementById("theme").value;
    editor.setOption("theme", theme);
}
```

#### 语法检查
- 引入 `getAnnotations` 方法异步获取代码的语法错误：
```javascript
lint: {
    async: true,
    getAnnotations: async (code, updateLinting) => {
        const response = await fetch('/lint_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        const annotations = await response.json();
        updateLinting(annotations);
    }
}
```
- 鼠标悬停错误标记时，显示详细错误信息。

#### 自动补全
- 利用 CodeMirror 的 `showHint` 方法：
```javascript
editor.on('inputRead', async (cm) => {
    const cursor = cm.getCursor();
    const token = cm.getTokenAt(cursor);

    if (token.string === '.' || token.string.trim().length > 0) {
        cm.showHint({
            hint: async () => {
                const code = cm.getValue();
                const response = await fetch('/autocomplete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code, cursor })
                });

                const suggestions = await response.json();
                return {
                    list: suggestions.map(s => ({
                        text: s.text,
                        displayText: `${s.text} (${s.type})`
                    })),
                    from: CodeMirror.Pos(cursor.line, token.start),
                    to: CodeMirror.Pos(cursor.line, token.end)
                };
            }
        });
    }
});
```

#### 运行代码
- 使用 `fetch` 向后端发送代码并获取运行结果：
```javascript
async function runCode(button) {
    const container = button.closest('.code-container');
    const resultDiv = container.querySelector(".result");
    const code = editor.getValue();

    resultDiv.innerHTML = ''; 
    resultDiv.style.height = 'auto'; // 重置高度

    try {
        const response = await fetch('/run_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });

        const result = await response.json();
        if (result.error) {
            resultDiv.innerHTML = `<p class="error">${result.error}</p>`;
        } else {
            result.outputs.forEach(output => {
                if (output.type === 'text') {
                    const p = document.createElement('p');
                    p.textContent = output.content;
                    resultDiv.appendChild(p);
                } else if (output.type === 'image') {
                    const img = document.createElement('img');
                    img.src = `data:image/png;base64,${output.content}`;
                    resultDiv.appendChild(img);
                }
            });
        }
    } catch (error) {
        resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    }

    resultDiv.style.height = `${resultDiv.scrollHeight}px`; // 根据内容高度调整
}
```

## 使用方式

1. 打开 `index.html` 文件。
2. 编写 Python 代码。
3. 点击 `运行` 按钮，查看运行结果。
4. 切换主题或利用补全功能提升开发体验。

## 依赖

- 浏览器支持的现代 HTML、CSS 和 JavaScript。
- 后端 API（示例接口）：
  - `/lint_code`：返回代码的语法检查结果。
  - `/autocomplete`：返回代码的自动补全建议。
  - `/run_code`：执行代码并返回结果。

## 常见问题

1. **主题未切换生效？**
   - 确保正确引入主题 CSS 文件。
2. **语法检查未生效？**
   - 检查后端 `/lint_code` 接口是否正常响应。
3. **运行结果无响应？**
   - 确保后端 `/run_code` 接口正确配置并返回数据。