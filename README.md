### 介绍

这是[gogotester](https://github.com/azzvx/gogotester)的python版本，原版本使用C#，在windows下可以使用。本版本主要针对Linux系统下。本版本在[NKUCoingCat/gogotester_python](https://github.com/NKUCodingCat/gogotester_python)的基础上使用py3+eventlet重写，代码风格和性能有小小提高，内存需求50M以内。

### 安装和运行

> Ubuntu
```python
sudo apt-get install python3-pip
sudo pip3 install IPy eventlet
# 会输出若干个搜索到的可用IP地址
python3 gogotester.py
```

### 设置文件

```ini
[DEFAULT]
# 需要搜索到的IP地址数量
limit = 10

# socket和ssl的端口数，视性能而定，一般200-300没问题
socket_num = 30
ssl_num = 10

# socket和ssl超时时间
socket_timeout = 1
ssl_timeout = 10

```

###IPv6
修改gogotester文件

```python
gogo = Gogotester("./ggc.txt", "config.ini")
# gogo.run(family="IPv4")
gogo.run(family="IPv6")
```