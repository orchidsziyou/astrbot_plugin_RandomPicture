# Setu Plugin

## 介绍

这是一个随机图片的插件，主要功能为：<br>
    -用户上传图片，bot保存到本地作为资源库<br>
    -用户发送指令，bot随机返回一张本地资源库中的图片<br>
因此，使用该插件需要保证部署机器人的服务器有足够的存储空间，否则无法正常运行。<br>

## 功能
- 上传图片：用户上传图片到机器人，机器人将图片保存到本地资源库中。<br>
     具体指令有：
- /上传涩图：上传一张涩图到本地资源库中,支持回复、发送指令的时顺带发送的图片，支持一次性上传多张图片。暂不支持聊天记录里面上传图片。<br>
- /随机涩图 (/setu)：随机返回本地资源库中的一张图片。<br>
- /随机鬼图 (/guitu)：随机返回本地资源库中的一张鬼图。<br>
- /上传鬼图：上传一张鬼图到本地资源库中,支持回复、发送指令的时顺带发送的图片，支持一次性上传多张图片。暂不支持聊天记录里面上传图片。<br>
- /涩图（鬼图）排行榜：统计用户上传到本地资源库的涩图（鬼图）数量，返回上传数量最多的前10个用户ID及其上传数量。<br>

## 使用前提
本插件只针对使用了Napcat的用户开发，插件中调用了aiocqhttp上面的一些API.<br>
如果您没用使用Napcat来部署机器人，本插件不适用于您的机器人:(((( <br>

## 安装
直接在Astrbot控制台上一键安装即可,也可以下载项目安装包到本地，通过Astrbot控制台上传安装（网络不好的情况下推荐使用这种方法）。

## 配置
1.发图CD
    可以再astrbot控制台里面设置随机图片的cd，单位为s，默认30s<br>
2.资源库路径
    资源库路径是指机器人本地保存图片的路径，默认路径为'./data/plugins/astrbot_plugin_RandomPicture_Data ',若有需要修改存储的路径，在部署bot的'./data/plugins/astrbot_plugin_RandomPicture/config.json '里面更改，请务必确保路径存在且有写入权限，并且不要修改json当中各个项目的名字，否则会导致插件运行异常。<br>
    PS：尽量不要修改，修改不当可能导致插件运行异常:( <br>


