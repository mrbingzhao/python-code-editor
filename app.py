#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   app.py
@Describe :  交互式 Python 编辑器,实现在线运行python代码并输出运行结果
@Contact :   mrbingzhao@qq.com
@License :   (C)Copyright 2024/12/25 15:54, Liugroup-NLPR-CASIA

@Modify Time        @Author       @Version    @Desciption
----------------   -----------   ---------    -----------
2024/12/25 15:54    liubingzhao      1.0           ml
'''

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

from flask import Flask, request, jsonify
import io
import matplotlib.pyplot as plt
import sys
import base64
import pyflakes.api
import pyflakes.reporter
import jedi

app = Flask(__name__)

class OutputCapture:
    """自定义 stdout 捕获类"""
    def __init__(self, outputs):
        self.outputs = outputs  # 引用外部输出列表

    def write(self, text):
        """捕获文本输出"""
        if text.strip():  # 忽略空白文本
            self.outputs.append({'type': 'text', 'content': text.strip()})

    def flush(self):
        """必须实现的 flush 方法，用于兼容 stdout"""
        pass

@app.route('/')
def home():
    return "Welcome to the Python Code Runner"

@app.route('/run_code', methods=['POST'])
def run_code():
    code = request.json.get('code', '')

    # 输出列表
    outputs = []  # 按顺序存储文本和图像输出
    error = None

    # 自定义 plt.show() 方法
    def custom_show():
        """替换 plt.show()，捕获图像并存储到 outputs 列表"""
        image_stream = io.BytesIO()
        plt.savefig(image_stream, format='png')
        plt.close()
        image_stream.seek(0)
        image_data = base64.b64encode(image_stream.getvalue()).decode('utf-8')
        outputs.append({'type': 'image', 'content': image_data})

    try:
        # 重定向 stdout
        sys.stdout = OutputCapture(outputs)

        # 替换 plt.show() 全局方法
        original_show = plt.show
        plt.show = custom_show

        # 执行用户代码
        exec_globals = {'plt': plt}
        exec(code, exec_globals)

    except Exception as e:
        error = str(e)

    finally:
        # 恢复 stdout 和 plt.show
        sys.stdout = sys.__stdout__
        plt.show = original_show

    # 返回结果
    return jsonify({
        'error': error,
        'outputs': outputs
    })

@app.route('/lint_code', methods=['POST'])
def lint_code():
    code = request.json.get('code', '')
    errors = []

    try:
        # Use pyflakes for static analysis
        output = io.StringIO()
        reporter = pyflakes.reporter.Reporter(output, output)
        pyflakes.api.check(code, filename='<string>', reporter=reporter)
        error_lines = output.getvalue().strip().split('\n')
        for error in error_lines:
            if error:
                parts = error.split(':', 3)
                if len(parts) >= 3:
                    line = int(parts[1].strip())
                    message = parts[2].strip()
                    errors.append({
                        'message': message,
                        'severity': 'error',  # CodeMirror uses "error", "warning", etc.
                        'from': {'line': line - 1, 'ch': 0},  # Line and character positions
                        'to': {'line': line - 1, 'ch': 80}   # Mark the entire line
                    })
    except Exception as e:
        errors.append({
            'message': str(e),
            'severity': 'error',
            'from': {'line': 0, 'ch': 0},
            'to': {'line': 0, 'ch': 1}
        })

    return jsonify(errors)

@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    data = request.json
    code = data.get('code', '')
    cursor = data.get('cursor', {})
    line = cursor.get('line', 0)
    column = cursor.get('ch', 0)

    try:
        script = jedi.Script(code, line=line + 1, column=column)  # jedi 使用 1 基索引
        completions = script.complete()
        suggestions = [
            {'text': comp.name, 'type': comp.type}
            for comp in completions
        ]
        return jsonify(suggestions)
    except Exception as e:
        return jsonify([]), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
