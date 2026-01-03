- 该文件夹包含所有目标文件，从以下链接获取目标：https://github.com/QRXqrx/NJU-AT-fuzz-targets
- 注意，要将源文件解压至targets中，不要修改名字，否则Makefile可能识别失败。
- 一个可能的解压脚本：
```bash
#!/bin/bash

for tarball in *.tar.gz; do
    # 跳过 :Zone.Identifier
    if [[ -f "$tarball" ]]; then
        echo "解压 $tarball ..."
        tar -xzf "$tarball" -C PATH/TO/MY-FUZZER/targets/
    fi
done
```