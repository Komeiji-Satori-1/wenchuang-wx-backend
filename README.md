# WX_wenchuang_backend

一个基于 **Django** 的微信文创小程序后台管理系统。  
主要功能包括：用户登录、商品管理、订单管理、后台数据监控等。

---

## 🚀 运行环境

- **操作系统**: Windows 10 / 11  
- **Python**: 3.12  
- **Django**: 5.0+  
- **数据库**: MySQL 8.0  
- **前端**: 微信小程序 (WXML, WXSS, JS)  
- **包管理**: pip / virtualenv  

---

## 📦 依赖插件

### 本项目使用的主要 Python 依赖：
Django==5.0.7
mysqlclient==2.2.0 # 或者 PyMySQL==1.1.0
djangorestframework==3.15.2
MySQL==8.0.
### 👉 推荐在虚拟环境中运行，先创建虚拟环境：
bash
python -m venv .venv
### 然后激活虚拟环境：
Windows (PowerShell):
.venv\Scripts\activate

Mac/Linux:
source .venv/bin/activate
### 安装依赖：
pip install -r requirements.txt


## ⚙️ 数据库配置
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
python manage.py makemigrations
python manage.py migrate


## ▶️ 启动项目
### 运行开发服务器：
python manage.py runserver
### 然后访问：
http://127.0.0.1:8000/

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