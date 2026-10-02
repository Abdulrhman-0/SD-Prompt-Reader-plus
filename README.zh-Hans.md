<div align="center">
    <img alt="icon" src="sd_prompt_reader/resources/icon-cube.png" width=20% height=20%>
    <h1>SD Prompt Reader+</h1>
    <a href="https://github.com/Abdulrhman-0/SD-Prompt-Reader-plus/releases/latest">
        <img alt="GitHub releases" src="https://img.shields.io/github/downloads/Abdulrhman-0/SD-Prompt-Reader-plus/total"></a>
    <a href="https://github.com/Abdulrhman-0/SD-Prompt-Reader-plus/blob/main/LICENSE">
        <img alt="GitHub" src="https://img.shields.io/github/license/Abdulrhman-0/SD-Prompt-Reader-plus"></a>
    <a href="https://github.com/Abdulrhman-0/SD-Prompt-Reader-plus/releases/latest">
        <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/Abdulrhman-0/SD-Prompt-Reader-plus"></a>
    <a href="https://github.com/psf/black">
        <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
    <img alt="platform" src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey">
    <br><br>

[English](README.md) | [简体中文](README.zh-Hans.md)

一个独立的 AI 图片 prompt 查看器与批量转换工具 —— 可浏览整个文件夹、查看任意图片的 prompt，并批量转换，无需依赖 webui
    <br>
  <p>
    <a href="#功能">功能</a> •
    <a href="#支持格式">支持格式</a> •
    <a href="#下载">下载</a> •
    <a href="#使用方式">使用方式</a> •
    <a href="#常见问题">常见问题</a> •
    <a href="#credits">Credits</a>
  </p>
    <img src="./images/screenshot_v1.0.0.jpg">
</div>

> [!NOTE]
> **SD Prompt Reader+** 是 [Stable Diffusion Prompt Reader](https://github.com/receyuki/stable-diffusion-prompt-reader) 的增强分支 (fork)，原作者为 [receyuki](https://github.com/receyuki)，以 MIT 许可证发布。所有原有功能均保留，新增内容见 [本分支新增功能](#本分支新增功能)。

> [!TIP]
> 上游另有一个独立的 [ComfyUI Prompt Reader Node](https://github.com/receyuki/comfyui-prompt-reader-node)
> 项目，本项目（分支）不包含该功能。

## 本分支新增功能
本分支保留了全部原有功能，并新增了文件夹工作流与批量转换功能：

- 📁 **文件夹浏览** — 一次打开整个文件夹，在左侧 **Photos** 面板中逐个点击查看图片，无需再逐张拖入。
- 🔄 **批量转换（右侧面板）** — 新增的 **Convert** 面板可将整个文件夹的图片转换为 **JPG / PNG / WEBP**，并保留图片中的 prompt 元数据。
- ⏱️ **进度与取消** — 转换在后台线程运行，带有实时进度与 **Cancel** 按钮，窗口不会卡死。
- ♻️ **刷新按钮** — 重新扫描文件夹，获取打开后新增或删除的图片。
- 💾 **记忆设置** — 下次启动时会恢复上次的文件夹、导出目录、格式与质量设置。
- 📂 **更广的输入格式** — 支持 BMP、GIF、TIFF 等 Pillow 可读取的格式，甚至没有扩展名的图片。
- 🧱 **更稳健的文件夹扫描** — Unicode 文件名、超长路径、无法读取的条目不再使完整文件夹显示为空。

*以上实现了原项目路线图中的三项计划：图像批处理、多图像/文件夹模式、用户设置。*

## 功能
- 支持 macOS、 Windows 和 Linux
- 仅提供图形界面
- 简单的拖放交互
- 复制 prompt 到剪贴板
- 去除图片中的 prompt
- 导出 prompt 到 txt 文件
- 编辑或导入 prompt 到图片
- 竖排显示以及根据字母排序
- 检测生成工具
- 支持多种格式
- 支持系统深色和浅色模式
- **文件夹浏览** — 一次打开整个文件夹，在左侧 *Photos* 面板中点击查看每张图片
- **批量转换** — 在右侧 *Convert* 面板将整个文件夹转换为 JPG / PNG / WEBP，并保留其中的 prompt

## 支持格式
|                                                                                     | PNG | JPEG | WEBP | TXT* |
|-------------------------------------------------------------------------------------|:---:|:----:|:----:|:----:|
| [A1111's webUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)            |  ✅  |  ✅   |  ✅   |  ✅   |
| [Easy Diffusion](https://github.com/easydiffusion/easydiffusion)                    |  ✅  |  ✅   |  ✅   |      |
| [StableSwarmUI](https://github.com/Stability-AI/StableSwarmUI)*                     |  ✅  |  ✅   |      |      |
| [StableSwarmUI (0.5.8-alpha 之前的版本)](https://github.com/Stability-AI/StableSwarmUI)* |  ✅  |  ✅   |      |      |
| [Fooocus-MRE](https://github.com/MoonRide303/Fooocus-MRE)*                          |  ✅  |  ✅   |      |      |
| [NovelAI (stealth pnginfo)](https://novelai.net/)                                   |  ✅  |      |  ✅   |      |
| [NovelAI (旧版)](https://novelai.net/)                                                |  ✅  |      |      |      |
| [InvokeAI](https://github.com/invoke-ai/InvokeAI)                                   |  ✅  |      |      |      |
| [InvokeAI (2.3.5-post.2 之前的版本)](https://github.com/invoke-ai/InvokeAI)              |  ✅  |      |      |      |
| [InvokeAI (1.15 之前的版本)](https://github.com/invoke-ai/InvokeAI)                      |  ✅  |      |      |      |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI)*                               |  ✅  |      |      |      |
| [Draw Things](https://drawthings.ai/)                                               |  ✅  |      |      |      |
| Naifu(4chan)                                                                        |  ✅  |      |      |      |

\* 见[格式限制](#TXT).

> [!NOTE]
> 如果你使用的工具或格式不在这个列表中, 请帮助我支持你的格式: 将你的工具生成的原始图片文件上传到 issues, 谢谢.

> [!TIP]
> 上游另有一个独立的 ComfyUI 节点项目，本项目（分支）不包含该功能。

## 下载
### Windows 用户
从 [GitHub Releases](https://github.com/Abdulrhman-0/SD-Prompt-Reader-plus/releases/latest) 下载可执行文件
### macOS 用户
从 [GitHub Releases](https://github.com/Abdulrhman-0/SD-Prompt-Reader-plus/releases/latest) 下载可执行文件
### Linux 用户 (不定期测试)
~~我很确定 Linux 用户可以在没有可执行文件的情况下搞明白怎么用~~
- 最低Python版本要求: 3.10
- 确保你的 Python 中安装了 tkinter 包.  
如果没有，请使用软件包管理器安装 python3-tk 包.  
e.g. `sudo apt-get install python3-tk` (基于 Debian 的发行版)  

你可以按照下方说明从源码运行
#### 手动运行源码
1. Clone repo
    ```bash
    git clone https://github.com/Abdulrhman-0/SD-Prompt-Reader-plus.git
    ```
   或者直接下载 repo 为 zip 格式.
2. CD 到文件夹并安装依赖
    ```bash
    cd SD-Prompt-Reader-plus
    pip install -r requirements.txt
    ```
3. Run
    ```bash
   python -m sd_prompt_reader.app
   ```

## 使用方式
### 读取 prompt
- 打开可执行文件 (.exe 或 .app) 并将图片拖入窗口.

或
- 右键图片选择使用 SD Prompt Reader 作为打开方式

或
- 直接将图片拖入可执行文件 (.exe 或 .app).

### 浏览文件夹
左侧 **Photos** 面板会列出文件夹内的所有图片，无需逐张打开。
- 点击 **Photos** 面板中的 **Add Folder** 选择文件夹，其中（含子文件夹）所有受支持的图片都会列出。
- 点击列表中的任意名称即可显示该图片及其 prompt。
- 新增或删除图片后，点击 **Refresh** 重新扫描文件夹。
- 面板标题会显示找到的图片数量。

### 转换图片（右侧面板）
右侧 **Convert** 面板可将整个文件夹的图片批量转换为 **JPG**、**PNG** 或 **WEBP**，同时保留生成 prompt 的元数据。
- 点击 **Add Folder** 选择要转换的文件夹；若留空，则使用 **Photos** 面板中已打开的文件夹。
- 选择导出目录与目标格式，然后调整质量 / 压缩选项。
- 点击 **Convert**。转换过程中会显示实时进度，按钮会变为 **Cancel**，窗口保持响应。
- 若图片有增删，点击 **Refresh** 重新扫描文件夹。
- 转换后的文件仍保留 prompt 元数据，依然可以读取。

![右侧面板（转换图片）](./images/Right%20panel%5Bconvert%20photos%5D.jpg)

### 导出 prompt 到 txt 文件
- 点击 "Export" 将在图像文件旁生成一个txt文件.
- 要保存到另一个位置, 点击展开的箭头并点击 "select directory".  
![export](./images/export.png)

### 去除图片中的 prompt
- 点击 "Clear" 将在原图像文件旁生成一个后缀为"_data_removed"的图像文件.
- 要保存到另一个位置, 点击展开的箭头并点击 "select directory".  
- 要覆盖原始图像文件, 点击展开的箭头并点击 "overwrite the original image".  
![remove](./images/remove.png)

### 编辑图片
> [!NOTE]
> 编辑后的图片将以 A1111 格式进行写入, 这意味着任何格式的图片在编辑后都将变为 A1111 格式.

- 点击 "Edit" 进入编辑模式
- 直接在文本框中编辑 prompt, 或者导入 txt 格式的prompt数据.  
- 点击 "Save" 将在原图像文件旁生成一个后缀为 "_edited" 的编辑后图像文件.  
- 要保存到另一个位置, 点击展开的箭头并点击 "select directory".  
- 要覆盖原始图像文件, 点击展开的箭头并点击 "overwrite the original image".  
![save](./images/save.png)

### 复制为单行 prompt
将图片 prompt 和设置复制为可被 [Prompts from file or textbox](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features#prompts-from-file-or-textbox) 读取的格式
支持以下参数:

| 设置                      | 参数                   |
|-------------------------|----------------------|
| Seed                    | --seed               |
| Variation seed strength | --subseed_strength   |
| Seed resize from        | --seed_resize_from_h |
| Seed resize from        | --seed_resize_from_w |
| Sampler                 | --sampler_name       |
| Steps                   | --steps              |
| CFG scale               | --cfg_scale          |
| Size                    | --width              |
| Size                    | --height             |
| Face restoration        | --restore_faces      |

- 点击展开的箭头并点击 "single line prompt".
- 将其粘贴到 webui 脚本 "Prompts from file or textbox" 下方的文本框.  
![single line prompt](./images/single_line_prompt.png)

### ComfyUI SDXL 流程
> [!NOTE]
> SDXL 流程不支持编辑，如有需要请去除图片中的 prompt 后再进行编辑

如果图片中 workflow 包含多组 SDXL 的 prompt, 
也就是 Clip G(text_g), Clip L(text_l) 和 Refiner 时, 
SD Prompt Reader 会切换到如下图所示的多组 prompt 显示模式.
多组 prompt 显示模式有两种界面供你选择，你可以通过按钮来进行切换.  
![comfyui_sdxl.png](./images/comfyui_sdxl.png)

## 格式限制
### TXT
1. txt 文件仅能在编辑模式下导入.
2. 仅支持 A1111 格式的 txt 文件. 你可以使用 A1111 webui 生成的txt文件, 或使用 SD prompt reader 从 A1111 生成的图片中导出 txt.
### StableSwarmUI
> [!IMPORTANT]
> StableSwarmUI 依然处于 Alpha 测试状态，其格式未来可能会发生改变, 我将会持续跟进 StableSwarmUI 未来的更新.
### ComfyUI
> [!IMPORTANT]
> 当流程过于复杂或者使用自定义节点时，本程序有很大概率无法正确显示元数据。这是由于 ComfyUI 并不储存元数据，而是储存完整的流程。
> 本程序仅能处理基础的工作流程.

1. 如果设置框中有多组数据(seed, steps, CFG, etc.)，这意味着流程中有多个 KSampler 节点
2. 由于 ComfyUI 的特性, workflow 中的所有节点和流程都存储在图像中, 包括没有被使用的. 并且一个流程可以有多个分支，多个输入和输出.
(e.g. 在一个流程中同时生成原图和 hires. fix 后的图像)
SD Prompt Reader 会遍历所有的流程和分支，并显示拥有完整的输入和输出的最长分支.
3. [ComfyUI SDXL 流程](README.zh-Hans.md#comfyui-sdxl-%E6%B5%81%E7%A8%8B)
### Easy Diffusion
默认设置下, Easy Diffusion 不会将 prompt 写入图片. 请更改设置中的 _Metadata format_ 为 _embed_ 来写入 prompt 到图片中.
### Fooocus-MRE
由于原版的 [Fooocus](https://github.com/lllyasviel/Fooocus) 并不支持将 metadata 写入图片文件, 
SD Prompt Reader 仅支持由 [Fooocus MoonRide Edition](https://github.com/MoonRide303/Fooocus-MRE) 生成的图片.

## 常见问题
### 病毒警告
> [!WARNING]
> 错误的病毒警报是由我使用的打包工具 _pyinstaller_ 造成的, 这对 _pyinstaller_ 用户是一个常见的问题. 
> 我花费了许多时间来解决 Windows Defender 的错误警报, 但我没法对每个杀毒软件单独解决问题. 
> 因此, 你可以选择相信 Windows Defender 或者使用 Linux 用户的使用说明来使用 app.
### "SD Prompt Reader.app" 已损坏，无法打开。您应该将它移到废纸篓。
> [!IMPORTANT]
> 这是一个使用非 appstore 的未签名软件时常见的 macOS 问题, 开发者需要付给苹果每年 $99 来避免这个问题. 
> 你可以在设置中**隐私与安全性**的**安全性**中选择**允许任何来源**, 但这可能造成危险. 
> 我推荐的方式是移除 quarantine attributes.
1. 在应用程序中打开终端. 
2. 输入以下命令并按回车. 

    `xattr -r -d com.apple.quarantine app的路径`

    比如:

    `xattr -r -d com.apple.quarantine /Applications/SD\ Prompt\ Reader.app`

如果你仍然担心安全性可以选择使用 Linux 用户的使用说明来使用 app.

## 待办
原项目路线图中的计划已在本分支全部实现：
- ~~图像批处理功能~~ ✅ *（右侧 **Convert** 面板）*
- ~~多图像/文件夹模式~~ ✅ *（左侧 **Photos** 面板）*
- ~~用户设置~~ ✅ *（设置会在会话之间保留）*

## Credits
- **本分支** — 以 *SD Prompt Reader+* 维护。文件夹浏览与批量转换为在原项目基础上的新增功能。
- 原项目：[Stable Diffusion Prompt Reader](https://github.com/receyuki/stable-diffusion-prompt-reader)，作者 [receyuki](https://github.com/receyuki)，MIT 许可证。
- Inspired by [Stable Diffusion web UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui/)
- App icon generated using Stable Diffusion with [IconsMI](https://huggingface.co/jvkape/IconsMI-AppIconsModelforSD)
- Special thanks to [Azusachan](https://github.com/Azusachan) for providing SD server
- The NovelAI stealth pnginfo parser is based on [the official metadata extraction script of NovelAI](https://github.com/NovelAI/novelai-image-metadata)
