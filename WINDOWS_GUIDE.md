# 如何在 Windows 上运行本程序

## 方法一：打包成 EXE（推荐，最方便）

这个方法会将程序打包成一个独立的 `.exe` 文件，以后双击就能运行，不需要配置环境。

1. **安装 Python**
   - 下载并安装 [Python 3.12](https://www.python.org/downloads/) (安装时请勾选 "Add Python to PATH")

2. **安装打包工具和依赖**
   - 在项目文件夹内，按住 `Shift` + 右键，选择 "此处打开 Powershell 窗口" (或者终端)
   - 输入以下命令安装依赖：
     ```bash
     pip install -r requirements.txt
     pip install pyinstaller
     ```

3. **执行打包**
   - 输入以下命令开始打包：
     ```bash
     pyinstaller --noconsole --onefile --name="基金套利监控" --icon=resources/icon.ico src/main.py
     ```
     *(注意：如果还没有 `resources/icon.ico` 图标文件，可以去掉 `--icon=...` 这部分参数)*
     *(如果打包出错找不到模块，可能需要调整命令为 `pyinstaller --noconsole --name="基金套利监控" --add-data "src;src" src/main.py`)*

4. **完成**
   - 打包完成后，在生成的 `dist` 文件夹里找到 `基金套利监控.exe`，直接双击即可运行。您可以把它复制到任何地方。

---

## 方法二：直接运行源码

如果您只是想偶尔运行一下：

1. **安装 Python** (同上)
2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
3. **运行程序**
   - 双击运行 `run.bat` (如果没有，新建一个文本文件，写入 `python -m src.main`，保存为 `run.bat`)
