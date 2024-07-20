
## 伶伦转换器 - 机器人版使用文档

命令为标题，后面是功能和子命令。

支持传入 `.midi`、`.mid`、`.json` 文件载入服务器缓存。

<!-- 若子命令为参数项，后面需要参数。

若子命令为开关项，后面无需参数。 -->

**以下所有命令中，若字符串类型的参数需要且可以填入多个内容，则可用 `all` 代替参数中的全部数据；此情况下，也可以用和符`&`分割多个你想要填写的信息；同样的，若参数中需要包含空格，则须以英文双引号`"`扩起。**

### llmscvt | linglun_convert | 音乐转换 | midi转换 | 转换音乐 | linglun_music_convert

转换midi音乐到指定的格式，支持批量格式批量文件。每次转换默认基础增加 0.5 点数，每多一种转换格式多增加 0.5 点数，`MSQ`格式不计入后续点数消耗。每日点数在凌晨四时整归零，点数达到20则不可进行转换。

-   `-f | --file <字符串>` : 缓存中的midi文件名称，需提前上传mid文件；默认为`all`

-   `-emr | --enable-mismatch-error` : 对音符的不匹配报错；默认为关

-   `-ps | --play-speed <小数>` : 播放速度；默认为`1.0`

-   `-dftp | --default-tempo <整数>` : 默认的tempo；默认为`500000`

-   `-ptc | --pitched-note-table <字符串>` : **不可多填** : 乐音乐器对照表，需要提前上传json文件，此处输入缓存中的json文件名称，或者默认存有的三组对照表名称：`touch`、`classic`、`dislink`；默认为`touch`

-   `-pcs | --percussion-note-table <字符串>` : **不可多填** : 打击乐器对照表，需要提前上传json文件，此处输入缓存中的json文件名称，或者默认存有的三组对照表名称：`touch`、`classic`、`dislink`；默认为`touch`

-   `-e | --old-execute-format` : 是否使用旧版execute指令格式；默认为关

-   `-mv | --minimal-volume <小数>` : 最小播放音量；默认为`0.1`

-   `-vpf | --volume-processing-function <字符串>` : 音量处理函数，支持两种音量函数：`natural`、`straight`；默认为`natural`

-   `-t | --type <字符串>` : 转换结果类型，支持的类型有：`addon-delay`、`addon-score`、 `mcstructure-dalay`、`mcstructure-score`、`bdx-delay`、`bdx-score`、`msq`；默认为`all`

-   `-htp | --high-time-precision` : **仅当结果类型包含 `msq` 时生效** : 是否使用高精度时间存储MSQ文件；默认为关

-   `-pgb | --progress-bar <字符串> <字符串> <字符串>` : **仅当结果包含 `addon-*`、`bdx-*` 之一时生效、不可多填** : 进度条样式，参照[进度条自定义](https://gitee.com/TriM-Organization/Musicreater/blob/master/docs/%E5%BA%93%E7%9A%84%E7%94%9F%E6%88%90%E4%B8%8E%E5%8A%9F%E8%83%BD%E6%96%87%E6%A1%A3.md#%E8%BF%9B%E5%BA%A6%E6%9D%A1%E8%87%AA%E5%AE%9A%E4%B9%89)，以空格拆分三个字符串；默认请查阅上述文档

-   `-s | --scoreboard-name <字符串>` : **仅当结果类型包含 `*-score` 之一时生效、不可多填** : 播放使用的计分板名称；默认为`mscplay`

-   `-dsa | --disable-scoreboard-autoreset` : **仅当结果类型包含 `*-score` 之一时生效** : 是否禁用计分板自动重置；默认为关

-   `-p | --player-selector <字符串>` : **仅当结果类型包含 `*-delay` 之一时生效、不可多填** : 播放使用的玩家选择器；默认为`@a`

-   `-h | --height-limit <整数>` : **仅当结果类型包含 `*-delay`、`bdx-*` 之一时生效** : 生成结构的最大高度限制；默认为`32`

-   `-a | --author <字符串>` : **仅当结果类型包含 `bdx-*` 之一时生效、不可多填** : 音乐文件的作者署名；默认为`Eilles`

-   `-fa | --forward-axis <字符串>` : **仅当结果类型包含 `*-repeater` 之一时生效、不可多填** : 生成结构的朝向；默认为`z+`（**未来功能**）


### 查看缓存 | listCache | 查看文件缓存 | 查看缓存文件

查看自己上传到服务器的文件

### 清除缓存 | clearCache | 清除文件缓存 | 清除缓存文件 | 清空缓存

删除自己所有上传到服务器的文件

### 转换帮助 | 查看转换帮助 | 查看帮助 | cvt_help | convert_help | cvthlp

查看此帮助文档


