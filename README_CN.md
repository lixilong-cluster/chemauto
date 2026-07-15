# ChemAuto 7.1.2

**ChemAuto——团簇化学计算数据自动分析程序**

ChemAuto 是面向 Windows 的量子化学计算数据批量处理与可视化程序，主要服务于团簇体系的 Gaussian 计算工作。程序由早期公开版本和日常研究中长期使用的独立脚本持续整合而成，同时保留命令行入口和图形用户界面。

当前归档版本：**7.1.2**  
发布日期：**2026 年 7 月 15 日**  
开发者：**李喜龙**

## 主要功能

- 递归读取 Gaussian `.log` 文件，批量提取 HF、ZPE、Etot、点群、电子态、虚频、优化/频率收敛状态、终止状态及波函数稳定性等信息。
- 在 GUI 中联动显示初始结构、优化结构、SCF 能量轨迹和当前计算详情，并支持排序、筛选及 CSV/Excel 导出。
- 对当前载入记录采用统一的全局最低 Etot 作为相对能零点；点击表头后按所选字段主排序，并以 Etot/HF 作为副排序依据。
- 支持结构提取、多帧 XYZ 查看、`.fchk → XYZ`、多 Link1 `.gjf/.com` 读取与修改。
- 生成 Stable/Stable=Opt 输入，并处理 Gen/GenECP、ChkBasis 等情况。
- 生成和分析 VDE/ADE 计算任务。
- 生成 PES 绘图数据，并通过 Origin/OriginPro 自动绘制 DOS 谱图。
- 导出包含初始/优化结构图的 Excel；默认使用经长期验证的旧版 PyMOL 球棍渲染逻辑，并保留内置渲染器作为备用。
- 生成原子光谱项。
- 可独立启动 Reference Explorer，辅助查询文献元数据和下载引文文件。

## 从零构建

系统要求：Windows 10/11 64 位、64 位 Python 3.11。首次安装依赖需要联网。

双击：

```text
BUILD_FROM_SCRATCH.bat
```

脚本会自动创建 `.venv`、安装依赖、运行回归测试与 PyMOL 绘图测试、构建便携程序，并在 `release` 目录生成发布 ZIP。其他高级构建和清理脚本统一放在 `scripts/windows/`。

## 目录说明

```text
src/chemauto/                 ChemAuto 完整源码
src/pymol/                    旧版 PyMOL 球棍渲染运行时
tools/reference_explorer/     Reference Explorer 源码
assets/                       图标和资源
requirements/                 Python 依赖列表
tests/                        自动回归测试
test_data/                    小型测试数据
tests/build_checks/           PyMOL 构建前后绘图检查
```

## 维护与更新

版本编号、源码修改、自动测试、CHANGELOG、便携版构建及 GitHub Release 的维护要求见 [docs/MAINTENANCE_GUIDE_CN.md](docs/MAINTENANCE_GUIDE_CN.md)。

## 外部依赖

- DOS 自动绘图要求安装 Origin/OriginPro。
- 远程 `.chk → .fchk` 要求 OpenSSH、网络和服务器账号。
- `.fchk/.fch` 查看需要 GaussView 或用户指定的其他查看程序。
- ChemAuto 不保存服务器密码或私钥口令。

## 许可证与第三方组件

项目沿用仓库的 Apache-2.0 许可证。捆绑的第三方组件保留各自上游许可证与声明，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
