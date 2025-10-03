# 文创产品购买小程序后台管理系统

一个基于 **Django** 的微信文创小程序后台管理系统。  
主要功能包括：用户登录、商品管理、订单管理、后台数据监控等。

---

## 🚀 运行环境

- **操作系统**: Windows 10 / 11  
- **Python**: 3.12  
- **Django**: 5.0+  
- **数据库**: MySQL 8.0.43  
- **前端**: 微信小程序 (WXML, WXSS, JS)  
- **包管理**: pip / virtualenv  

---

## 📦 依赖插件

### 本项目使用的主要 Python 依赖：
Django==5.0.7
mysqlclient==2.2.0 # 或者 PyMySQL==1.1.0
djangorestframework==3.15.2
MySQL==8.0.43  
## 安装必要的软件：
### 安装 Python 3.12  

Python 官网下载https://www.python.org/downloads/  

安装时勾选 Add Python to PATH。 

### 安装 Git（用于从 GitHub 拉取代码）。
Git 官网下载https://git-scm.com/downloads

安装后在命令行输入：git --version  
出现版本号证明安装成功
### 安装 MySQL
推荐b站安装视频BV1jcabemEr7，一定要完全按照其流程规范安装！  

安装时设置 root 密码（记住它，后面要用）

安装后在命令行可以用mysql --version检验

### 安装 PyCharm 作为开发工具

## 获取项目代码
打开命令行，进入一个存放项目的目录，比如：  
cd D:\workspace（此处的workspace为你的项目目录，你可以任意取英文名。如有修改注意在之后的地址要保持一致）  
或者在存放项目的目录界面（没错你必须要新建一个文件夹）右键空白处，点击Open Git Bash here  
输入git clone https://github.com/Komeiji-Satori-1/wenchuang-wx-backend.git  
进入D:\workspace\wenchuang-wx-backend文件夹

## 创建虚拟环境并安装依赖
在命令行（不是Git Bash而是Cmd）输入python -m venv .venv以创建虚拟环境  
激活虚拟环境  
Win：.venv\Scripts\activate  

Mac/Linux：source .venv/bin/activate  
安装依赖：
pip install -r requirements.txt

## ⚙️ 数据库配置
### 登录MySQL
Cmd中输入："D:\MySQL\MySQL server8.0\bin" -u root -p后输入密码  

- **注意**"D:\MySQL\MySQL server8.0\bin"是你自己MySQL安装时选择的安装目录的bin文件夹的绝对路径，请自行替换或保持一致  
### 创建数据库
CREATE DATABASE wenchuang_program DEFAULT CHARSET utf8mb4;  

- **注意**wenchuang_program是你自己MySQL创建的数据库名，请自行替换或保持一致
### 在 settings.py 中配置 MySQL 数据库：  

    DATABASES = {  

        'default': {  

            'ENGINE': 'django.db.backends.mysql',  

            'NAME': 'wenchuang_program',  

            'USER': 'root',  

            'PASSWORD': '你的数据库密码',  

            'HOST': '127.0.0.1',  

            'PORT': '3306',
        }  

    }  

### 初始化数据库表：
Cmd中输入：  

python manage.py makemigrations
python manage.py migrate  

MySQL中输入：  

INSERT INTO admin_user (username, password) VALUES ('admin', '123456');


## ▶️ 启动项目
### 运行开发服务器：
python manage.py runserver
### 然后访问：
http://127.0.0.1:8000/  
输入：  
账户：admin  
密码：123456

## 📌 功能模块
用户登录与权限验证
后台管理
商品管理
订单管理
用户管理
微信小程序 API 接口

## 📝 开发记录
 登录接口编写
 跨 App URL 配置
 商品管理模块
 订单管理模块
 微信小程序数据交互

## 🤝 贡献
欢迎提交 PR 或 issue 来改进项目。

## 📄 License
本项目仅供学习与交流使用。
