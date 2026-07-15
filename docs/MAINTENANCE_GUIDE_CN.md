# ChemAuto 更新与维护说明

## 1. 版本编号

采用语义化版本：

- 修复错误、不改变主要功能：`7.1.2 → 7.1.3`
- 增加向后兼容的新功能：`7.1.x → 7.2.0`
- 出现不兼容的重大架构变化：`7.x → 8.0.0`

版本号应在源码中的统一版本位置修改，并同步更新窗口标题、CMD 信息、README、CHANGELOG、发布文件名和 GitHub Release 标签。

## 2. 每次更新的标准流程

1. 从 `main` 创建分支，例如 `fix/global-energy-sort` 或 `release/7.1.2`。
2. 修改源码并补充或更新自动测试。
3. 运行根目录中的 `test_windows.bat`。
4. 若涉及 PyMOL，运行 `scripts/windows/verify_pymol_renderer.bat`。
5. 更新 `CHANGELOG.md`。
6. 使用 `scripts/windows/build_chemauto_portable.bat` 或根目录中的 `BUILD_FROM_SCRATCH.bat` 构建。
7. 在未安装 Python 的 Windows 环境中测试便携目录。
8. 合并到 `main`，创建版本标签和 GitHub Release。

## 3. 禁止提交到仓库的内容

`.gitignore` 已排除：

- `.venv/`
- `build/`、`dist/`、`release/`
- `__pycache__/`、`.pyc`
- 用户配置、远程服务器配置和日志
- 临时导出的 Excel、PNG、OGG、OPJU 等文件

不得提交密码、私钥、访问令牌、服务器口令或含有敏感数据的个人配置文件。

## 4. 测试维护

每次修复一个错误，都应建立能够复现该错误的最小测试。测试数据应去除个人路径、服务器地址、密码和不必要的研究数据。解析逻辑、能量排序、Stable、VDE/ADE、PES/DOS、Excel 和 PyMOL 相关改动均应运行对应回归测试。

## 5. 发布文件

源码保存在 `main` 分支。编译后的便携 ZIP 不直接提交进 Git 历史，而应上传为 GitHub Release 附件：

- `ChemAuto_<version>_Portable.zip`
- `ReferenceExplorer_<version>_Portable.zip`
- `ChemAuto_Suite_<version>.zip`

同时提供 SHA-256 校验值和简要发布说明。

## 6. 外部依赖说明

Origin、GaussView、OpenSSH 和远程服务器均属于外部环境，不应打包进项目。PyMOL 运行时随当前构建源码提供，其上游许可证必须保留。Reference Explorer 的网页检索功能可能因出版平台页面结构、访问权限和反自动化策略变化而需要维护。

## 7. 兼容性与回退

发布前保留上一个稳定版本的标签和 Release。发现严重问题时，不覆盖旧 Release；发布修复版本并在 CHANGELOG 中说明。对经过长期验证的旧版 DOS/Origin 和 PyMOL 核心逻辑，修改前应建立对比测试，避免无依据重写。
