模糊目标种子详细信息

下表为模糊目标/被测程序信息，从左到右每一列分别为目标ID、目标名称、使用afl/afl++运行该目标时`--`部分后面的命令行内容，以及初始种子来源。

**注**：构建`lua`时注意阅读`src/Makefile`。

| TID  | Target  |  AFL-CMD  |  Initial Seeds  |
|--------|--------|--------| --------|
| T01 | `cxxfilt` |  `cxxfilt` | `"_Z1fv"`, (LLM-Generate) |
| T02 | `readelf` | `readelf -a @@ @@` | `afl++/testcases/others/elf/` |
| T03 | `nm-new` |  `nm-new @@` | `afl++/testcases/others/elf/` |
| T04 | `objdump` |  `objdump -d @@` | `afl++/testcases/others/elf/` |
| T05 | `djpeg` |  `djpeg @@` | `afl++/testcases/images/jpeg`, `<project>/testimages/` |
| T06 | `readpng` |  `readpng` | `afl++/testcases/images/png/`, `<project>/tests/` |
| T07 | `xmllint` |  `xmllint @@` | `afl++/testcases/others/xml/`, `<project>/test/` |
| T08 | `lua` |  `lua @@` | https://github.com/lua/lua/tree/master/testes |
| T09 | `mjs` |  `mjs -f @@` | `afl++/testcases/others/mjs/`, `<project>/tests/` |
| T10 | `tcpdump` |  `tcpdump -nr @@` | `afl++/testcases/others/pcap/`, `<project>/tests/` |