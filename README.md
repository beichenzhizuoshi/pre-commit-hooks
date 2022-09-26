## pre-commit hook 钩子

### 1. 自动编码转换Hook `transform_encoding`
当项目代码包含国际化语言时,有些编译器使用 `UTF-8` 编译失败(例如: `MSVC`), 在 `MacOS` 和 `Linux` 系统上编译器基本都支持 `UTF-8` 编译.而上传代码仓库时编码尽量保持一致, 否则部分平台在线查看会显示乱码.因此需要在提交代码前自动转换不满足编码要求的文件,同时在提交之后恢复到原来的编码,这样才不会影响本地编译器编译.

配置项目文件 `.pre-commit-config.yaml` 添加以下内容:
```yaml
- repo: https://github.com/beichenzhizuoshi/pre-commit-hooks
    rev: v1.0.0
    hooks:
      # automatically convert file encoding before submitting file
      - id: auto-transform-encoding
      # restore the original encoding after submitting the file
      - id: auto-restore-encoding
      - id: chinese-transform-encoding
```
### 2. 中文文件编码转换 `chinese-transform-encoding`
转换项目中包含中文的文件,统一文件编码.如包含中文的文件转换为 `UTF-8 BOM` 编码,适配 `MSVC` 编译器.通常该 `hook` 只需执行一次,因此默认设置手动调用,推荐在项目中调用以下命令修改文件编码
```shell
pre-commit run --all-file --hook-stage manual chinese-transform-encoding
```
配置文件 `.pre-commit-config.yaml` 如下:
```yaml
- repo: https://github.com/beichenzhizuoshi/pre-commit-hooks
    rev: v1.0.0
    hooks:
      # need to be called manually
      - id: chinese-transform-encoding
```

### 3. CRLF 与 LF 相互转换
跨平台开发存在 `CRLF` 与 `LF` 混用,根据需要它们之间相互转换

配置 `pre-commit`
```yaml
- repo: https://github.com/beichenzhizuoshi/pre-commit-hooks
    rev: v1.0.0
    hooks:
      - id: crlf-to-lf
      # stages: [post-checkout, post-merge]
      - id: lf-to-crlf
```
