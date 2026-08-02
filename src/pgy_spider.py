import random
import time
import sys
import requests
import json
import datetime
import csv
import pandas as pd
import os
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
from logging.handlers import TimedRotatingFileHandler
import webbrowser
from functools import partial
import subprocess

subprocess.Popen = partial(subprocess.Popen, encoding='utf-8')

import re
import platform


class Log_week():
    def get_logger(self):
        self.logger = logging.getLogger(__name__)
        # 日志格式
        formatter = '[%(asctime)s-%(filename)s][%(funcName)s-%(lineno)d]--%(message)s'
        # 日志级别
        self.logger.setLevel(logging.DEBUG)
        # 控制台日志
        sh = logging.StreamHandler()
        log_formatter = logging.Formatter(formatter, datefmt='%Y-%m-%d %H:%M:%S')
        # info日志文件名
        info_file_name = time.strftime("%Y-%m-%d") + '.log'
        # 将其保存到特定目录
        case_dir = r'./logs/'
        info_handler = TimedRotatingFileHandler(filename=case_dir + info_file_name,
                                                when='MIDNIGHT',
                                                interval=1,
                                                backupCount=7,
                                                encoding='utf-8')
        self.logger.addHandler(sh)
        sh.setFormatter(log_formatter)
        self.logger.addHandler(info_handler)
        info_handler.setFormatter(log_formatter)
        return self.logger


class PgySpider:
    """蒲公英小红书博主采集器

    负责：
    1. 按关键词搜索小红书蒲公英平台博主
    2. 按小红书号/昵称批量查询博主
    3. 解析博主详细信息（粉丝、报价、CPM、阅读数据等）
    4. CSV输出
    """

    def __init__(self, kw, note_type, search_type_val, fans_num_min, fans_num_max, note_price_min, note_price_max,
                 page_start, page_end, txt_msglist, logger):
        self.kw = kw
        self.note_type = note_type
        self.search_type_val = search_type_val
        self.fans_num_min = fans_num_min
        self.fans_num_max = fans_num_max
        self.note_price_min = note_price_min
        self.note_price_max = note_price_max
        self.page_start = page_start
        self.page_end = page_end
        self.txt_msglist = txt_msglist
        self.logger = logger
        self.describe = []
        self.wait_sec = self.get_config_pub()
        # 当前时间戳
        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # 保存文件名
        self.result_file = '蒲公英博主_{}_{}.csv'.format(self.search_type_val, now)
        self.cookie_text = self.get_cookie()
        self.h1 = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Authorization": "",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": self.cookie_text,
            "Origin": "https://pgy.xiaohongshu.com",
            "Priority": "u=1, i",
            "Referer": "https://pgy.xiaohongshu.com/solar/pre-trade_v2/advertiser/patterns/kol",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "macOS",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    def tk_show(self, context):
        self.logger.info(context)
        self.txt_msglist.delete('1.0', 'end')
        self.describe.append(context)
        self.txt_msglist.insert('insert', '\n'.join(self.describe))
        self.txt_msglist.see("end")

    def _safe_showinfo(self, title, message):
        """线程安全弹窗：子线程通过 after 切回主线程执行。"""
        try:
            if threading.current_thread() is threading.main_thread():
                self.txt_msglist.bell()
                messagebox.showinfo(title, message)
            else:
                self.txt_msglist.after(0, lambda: (self.txt_msglist.bell(), messagebox.showinfo(title, message)))
        except Exception as e:
            self.logger.error(f'[_safe_showinfo] {e}')

    def _safe_showerror(self, title, message):
        """线程安全弹窗：子线程通过 after 切回主线程执行。"""
        try:
            if threading.current_thread() is threading.main_thread():
                self.txt_msglist.bell()
                messagebox.showerror(title, message)
            else:
                self.txt_msglist.after(0, lambda: (self.txt_msglist.bell(), messagebox.showerror(title, message)))
        except Exception as e:
            self.logger.error(f'[_safe_showerror] {e}')

    def _safe_showwarning(self, title, message):
        """线程安全弹窗：子线程通过 after 切回主线程执行。"""
        try:
            if threading.current_thread() is threading.main_thread():
                self.txt_msglist.bell()
                messagebox.showwarning(title, message)
            else:
                self.txt_msglist.after(0, lambda: (self.txt_msglist.bell(), messagebox.showwarning(title, message)))
        except Exception as e:
            self.logger.error(f'[_safe_showwarning] {e}')

    def get_cookie(self):
        try:
            with open('cookie.txt', mode='r', encoding='utf8') as f:
                ck_str = f.read().strip()
                if '换成自己的' in ck_str:
                    self._safe_showerror("警告", "检测到未配置cookie！先用《cookie小工具》配置好cookie，再运行采集！")
                    sys.exit()
            self.tk_show(f'\ncookie.txt读取成功, 5s后开始采集！')
            time.sleep(5)
        except Exception as e:
            ck_str = ''
            self.tk_show('cookie读取失败! 先用《cookie小工具》配置好cookie，再运行采集！')
            self._safe_showerror("警告", "cookie读取失败! 先用《cookie小工具》配置好cookie，再运行采集！")
            print(str(e))
            sys.exit()
        ck_str = str(ck_str).strip()
        return ck_str

    def get_config_pub(self):
        """读取配置文件"""
        try:
            with open('config_pub.json', 'r') as file:
                text = json.load(file)
            # 读取等待时长
            wait_sec = text['wait_sec']
            if wait_sec < 1:
                self.tk_show('\n等待时长需至少1秒，请重新配置！')
                exit(1)
            self.tk_show(f'\n读取config_pub成功, 等待间隔是:{wait_sec}s')
        except Exception as e:
            wait_sec = ''
            self.tk_show('\n读取config_pub失败！请检查config_pub.json')
            self.tk_show(str(e))
            exit(1)
        return wait_sec

    def init_csv(self, csv_header):
        """初始化csv文件"""
        with open(self.result_file, 'a+', encoding='utf_8_sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(csv_header)
        self.tk_show('\ncsv初始化完成！')

    def get_red_id_list(self):
        try:
            df = pd.read_excel('博主列表.xlsx')
            red_id_list = df['小红书号或昵称'].values.tolist()
            self.tk_show('\n共检测到{}个待采博主'.format(len(red_id_list)))
            return red_id_list
        except Exception as e:
            self.tk_show(f'读取文件失败:博主列表.xlsx，异常信息:{str(e)}')
            exit(2)

    def get_richang(self, v_uid):
        """[专有代码已移除] 获取日常笔记数据

        原实现：
        1. 请求 /api/solar/kol/dataV3/notesRate 接口
        2. 解析返回JSON，提取：图文3秒阅读率、阅读中位数、互动中位数、
           阅读来源发现页占比、阅读来源搜索页占比
        """
        # 原实现约10行API请求与JSON解析代码
        picture3sViewRate = ''
        readMedian = ''
        interactionMedian = ''
        readHomefeedPercent = ''
        readSearchPercent = ''
        self.tk_show('[专有代码已移除] get_richang 需要专有实现')
        return picture3sViewRate, readMedian, interactionMedian, readHomefeedPercent, readSearchPercent

    def get_hezuo(self, v_uid):
        """[专有代码已移除] 获取合作笔记数据

        原实现：
        1. 请求 /api/solar/kol/dataV3/notesRate 接口（business=1）
        2. 解析返回JSON，提取：合作阅读中位数、合作互动中位数、
           合作阅读来源发现页占比、合作阅读来源搜索页占比
        """
        # 原实现约10行API请求与JSON解析代码
        readMedian = ''
        interactionMedian = ''
        readHomefeedPercent = ''
        readSearchPercent = ''
        self.tk_show('[专有代码已移除] get_hezuo 需要专有实现')
        return readMedian, interactionMedian, readHomefeedPercent, readSearchPercent

    def get_fans(self, v_uid):
        """[专有代码已移除] 获取粉丝画像数据

        原实现：
        1. 请求 /api/solar/kol/data/{uid}/fans_profile 接口
        2. 解析返回JSON，提取：女性粉丝占比、年龄占比最多的年龄段
        """
        # 原实现约8行API请求与JSON解析代码
        female_rate = ''
        max_percent_text = ''
        self.tk_show('[专有代码已移除] get_fans 需要专有实现')
        return female_rate, max_percent_text

    def get_yddj(self, v_uid):
        """[专有代码已移除] 获取阅读单价数据

        原实现：
        1. 请求 /api/solar/kol/dataV2/costEffective 接口
        2. 解析返回JSON，提取：图文阅读单价
        """
        # 原实现约5行API请求与JSON解析代码
        pictureReadCost = ''
        self.tk_show('[专有代码已移除] get_yddj 需要专有实现')
        return pictureReadCost

    def get_hezuo8(self, v_uid):
        """[专有代码已移除] 获取最近8篇合作笔记阅读数

        原实现：
        1. 请求 /api/solar/kol/dataV2/notesDetail 接口（pageSize=8）
        2. 解析返回JSON中的list，提取每篇笔记的readNum
        3. 不足8篇时用'无'填充
        """
        # 原实现约6行API请求与JSON解析代码
        readNum_list8 = ''
        self.tk_show('[专有代码已移除] get_hezuo8 需要专有实现')
        return readNum_list8

    def get_org(self, v_uid):
        """[专有代码已移除] 获取机构信息和获赞收藏数

        原实现：
        1. 请求 /api/solar/cooperator/user/blogger/{uid} 接口
        2. 解析返回JSON，提取：签约机构名称(noteSign.name)、获赞与收藏数
        """
        # 原实现约10行API请求与JSON解析代码
        org_name = ''
        like_collect_num = ''
        self.tk_show('[专有代码已移除] get_org 需要专有实现')
        return org_name, like_collect_num

    def get_cpm(self, v_uid):
        """[专有代码已移除] 获取预估CPM数据

        原实现：
        1. 请求 /api/pgy/kol/data/data_summary 接口
        2. 解析返回JSON，提取：预估CPM_图文、预估CPM_视频
        """
        # 原实现约15行API请求与JSON解析代码
        estimatePictureCpm = ''
        estimateVideoCpm = ''
        self.tk_show('[专有代码已移除] get_cpm 需要专有实现')
        return estimatePictureCpm, estimateVideoCpm

    def trans_level(self, v_level):
        """转换账号评估等级"""
        if v_level == 0:
            return '异常'
        elif v_level == 1:
            return '普通'
        elif v_level == 2:
            return '优秀'
        else:
            return '未知'

    def get_user_list(self):
        """[专有代码已移除] 博主列表采集主流程

        原实现核心流程：
        === 按xhs号采集模式 ===
        1. 初始化CSV（35列：昵称、小红书号、地址、机构、粉丝数、报价、CPM、阅读数据等）
        2. 从 博主列表.xlsx 读取待采集的小红书号/昵称列表
        3. 遍历每个博主，构造POST请求到 /api/solar/cooperator/blogger/v2
        4. 对每个博主依次调用 get_org/get_cpm/get_richang/get_hezuo/get_fans/get_hezuo8 获取详细数据
        5. 将博主数据写入CSV

        === 按关键词采集模式 ===
        1. 初始化CSV（37列，比xhs模式多"关键词"和"页码"两列）
        2. 根据 page_start ~ page_end 循环分页请求
        3. 每页请求 /api/solar/cooperator/blogger/v2，携带关键词、笔记类型、粉丝数范围、报价范围等参数
        4. 对每个博主依次调用各数据接口获取详细信息
        5. 将博主数据写入CSV
        """
        if self.search_type_val == '按xhs号采集':
            self.tk_show('\n[专有代码已移除] 按xhs号采集模式需要专有实现')
            # 原实现约130行：初始化CSV → 读取博主列表 → 遍历请求API → 解析数据 → 写入CSV
        elif self.search_type_val == '按关键词采集':
            self.tk_show('\n[专有代码已移除] 按关键词采集模式需要专有实现')
            # 原实现约160行：初始化CSV → 分页循环 → 请求API → 解析数据 → 写入CSV
        else:
            self.tk_show('采集方式，未知选项！退出程序！')
            exit(3)
        self.tk_show('\n[专有代码已移除] 全部博主采集功能需要专有实现')
        self.tk_show('==软件作者：马哥python说==')
        self._safe_showinfo('提示', '博主采集功能需要专有实现，未包含在本开源版本中')


class MyThread(threading.Thread):
    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args
        self.setDaemon(True)
        self.start()  # 在这里开始

    def run(self):
        self.func(*self.args)


def open_url(event):
    webbrowser.open("https://mp.weixin.qq.com/s/_tL0nYK7_VjH8QRs1VeH-w", new=0)


def open_sugg():
    webbrowser.open("https://docs.qq.com/sheet/DVGxzT0VVSkVzSW1u?tab=i7bbs4", new=0)


def task(txt_msglist):
    """[专有代码已移除] 从UI提取参数并启动采集任务

    原实现：
    1. 从 entry_kw、note_type、entry_fans_num_min/max 等UI控件读取用户输入
    2. 校验参数
    3. 实例化 PgySpider 并调用 get_user_list() 启动采集
    """
    log = Log_week()
    logger = log.get_logger()
    txt_msglist.delete('1.0', 'end')
    txt_msglist.insert('insert', '[专有代码已移除] 采集任务需要专有实现\n')
    # 原实现约40行：从UI控件读取参数 → 调用 PgySpider(...).get_user_list()


def show_about():
    messagebox.showinfo("关于软件",
                        "\nv2.0: 公开分期版本发布\nv2.1: 新增搜昵称\nv2.2: 新增字段：获赞与收藏\nv2.3: 新增mac版\nv2.4: 新增字段：CPM、蒲公英链接\nv2.5: 新增注册入口&新增cookie小工具&新增弹窗提醒&新增自定义等待&优化一机一码\n\n最新版软件获取:\n公众号【老男孩的平凡之路】回复: 爬蒲公英软件")


def show_agreement():
    messagebox.showinfo("使用协议",
                        """欢迎使用本软件！在使用前，请仔细阅读以下使用协议：

授权与许可：本软件仅授权用户用于合法的个人或商业用途。禁止使用本软件进行任何违法活动，包括但不限于未经授权的数据采集、侵犯知识产权和侵犯隐私权等。
责任限制：本软件开发者不对用户因使用本软件而导致的任何直接或间接损失负责。用户在使用过程中应遵守相关法律法规，并自行承担因使用本软件而产生的风险和责任。
数据隐私：本软件不会收集、存储或分享用户的个人数据。用户采集的数据应严格遵守数据保护法律和目标网站的使用政策。
更新与维护：我们有权随时对本软件进行更新和维护，用户应及时下载并安装更新，以确保软件的正常使用。
协议修改：我们保留随时修改本使用协议的权利，修改后的协议将在发布后立即生效。用户继续使用本软件即表示接受新的协议条款。

作为软件使用者，您默认接受以上协议条款。感谢理解与支持。如有疑问，请联系作者。"""
                        )


def create_spider_root():
    global entry_kw, note_type, entry_fans_num_min, entry_fans_num_max, entry_note_price_min, entry_note_price_max, entry_page_start, entry_page_end, search_type
    # 创建日志目录
    work_path = os.getcwd()
    if not os.path.exists(work_path + "/logs"):
        os.makedirs(work_path + "/logs")
    # 创建主窗口
    root = tk.Tk()
    root.title('爬蒲公英软件v2.5 | 马哥python说 | 公众号:老男孩的平凡之路')
    # 设置窗口大小
    root.minsize(width=850, height=650)
    # 左上角图标
    try:
        root.iconbitmap('mage.ico')
    except:
        pass
    # 菜单
    menu_bar = tk.Menu(root)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="关于软件", command=show_about)
    file_menu.add_command(label="使用协议", command=show_agreement)
    file_menu.add_command(label="意见收集", command=open_sugg)
    menu_bar.add_cascade(label="File", menu=file_menu)
    root.config(menu=menu_bar)

    # 搜索关键词
    tk.Label(root, justify='left', text='搜索关键词:').place(x=30, y=65)
    entry_kw = tk.Text(root, bg='#ffffff', width=22, height=2, )
    entry_kw.place(x=105, y=65, anchor='nw')  # 摆放位置
    # 说明
    tk.Label(root, justify='left', fg='red', text='如无需设置关键词，保留空白').place(x=270, y=65)

    # 笔记类型
    tk.Label(root, text='笔记类型:').place(x=30, y=105)
    note_type = ttk.Combobox(root, width=15, height=4, )
    note_type['value'] = ('不限', '图文笔记为主', '视频笔记为主')
    note_type.current(0)
    note_type.place(x=105, y=105, anchor='nw')  # 摆放位置
    # 说明
    tk.Label(root, justify='left', fg='red', text='笔记类型。默认不限').place(x=270, y=105)

    # 粉丝数量
    tk.Label(root, justify='left', text='粉丝数量:').place(x=30, y=140)
    entry_fans_num_min = tk.Spinbox(root, from_=0, to=9999999, increment=1, width=5, font=('微软', 15))
    entry_fans_num_min.place(x=105, y=140)
    tk.Label(root, justify='left', text='~').place(x=175, y=140)
    entry_fans_num_max = tk.Spinbox(root, from_=0, to=9999999, increment=1, width=5, font=('微软', 15))
    entry_fans_num_max.place(x=195, y=140)
    # 说明
    tk.Label(root, justify='left', fg='red', text='粉丝数范围。如无需设置粉丝数量范围，保留两个0').place(x=270, y=140)

    # 图文报价
    tk.Label(root, justify='left', text='图文报价:').place(x=30, y=180)
    entry_note_price_min = tk.Spinbox(root, from_=0, to=9999999, increment=1, width=5, font=('微软', 15))
    entry_note_price_min.place(x=105, y=180, anchor='nw')  # 摆放位置
    tk.Label(root, justify='left', text='~').place(x=175, y=180)
    entry_note_price_max = tk.Spinbox(root, from_=0, to=9999999, increment=1, width=5, font=('微软', 15))
    entry_note_price_max.place(x=195, y=180, anchor='nw')  # 摆放位置
    # 说明
    tk.Label(root, justify='left', fg='red', text='合作报价之图文笔记的报价范围。如无需设置报价范围，保留两个0').place(
        x=270, y=180)

    # 搜索页范围
    tk.Label(root, justify='left', text='搜索页范围:').place(x=30, y=220)
    entry_page_start = tk.Spinbox(root, from_=1, to=9999999, increment=1, width=5, font=('微软', 15))
    entry_page_start.place(x=105, y=220, anchor='nw')  # 摆放位置
    tk.Label(root, justify='left', text='~').place(x=175, y=220)
    entry_page_end = tk.Spinbox(root, from_=1, to=9999999, increment=1, width=5, font=('微软', 15))
    entry_page_end.place(x=195, y=220, anchor='nw')  # 摆放位置
    # 说明
    tk.Label(root, justify='left', fg='red', text='从第几页到第几页（注：每页20个博主）').place(x=270, y=220)

    # 运行日志
    tk.Label(root, justify='left', text='运行日志:').place(x=30, y=250)
    show_list_Frame = tk.Frame(width=780, height=300)  # 创建<消息列表分区>
    show_list_Frame.pack_propagate(0)
    show_list_Frame.place(x=30, y=270, anchor='nw')  # 摆放位置

    # 滚动条
    scroll = tk.Scrollbar(show_list_Frame)
    # 放到Y轴竖直方向
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # 输入采集进度
    txt_msglist = tk.Text(show_list_Frame, width=700, height=500)
    txt_msglist.config(yscrollcommand=scroll.set)  # 配置滚动条
    txt_msglist.pack()

    # 提示信息
    hint1 = tk.Label(root, justify='left', font=('微软', 10), fg='red',
                     text='使用说明：\n1、先用《cookie小工具》配置cookie，点击【这里】查看演示视频\n2、如果采集方式为"按xhs号采集", 请提前填写好 《博主列表.xlsx》 并保存\n3、支持自定义等待间隔，修改config_pub.json文件中的wait_sec，默认2s')
    hint1.place(x=30, y=1)
    hint1.bind("<Button-1>", open_url)

    # 采集方式
    tk.Label(root, text='采集方式:').place(x=650, y=10)
    search_type = ttk.Combobox(root, width=8, height=4, )
    search_type['value'] = ('按关键词采集', '按xhs号采集')
    search_type.current(0)
    search_type.place(x=710, y=10, anchor='nw')  # 摆放位置

    # 【开始执行】按钮
    fill_button = tk.Button(root, bg='white', text='开始执行', width=10, height=1,
                            command=lambda: MyThread(task, txt_msglist))
    fill_button.place(x=270, y=590, anchor='nw')  # 摆放位置
    # 【退出程序】按钮
    quit_button = tk.Button(root, text='退出程序', width=10, height=1, command=root.quit)
    quit_button.place(x=460, y=590, anchor='nw')

    # 免责声明
    claim = tk.Label(root,
                     text='免责声明: 禁止使用该软件从事任何违法活动，否则由此产生的一切法律后果由软件使用者自行承担，与软件开发作者无关！',
                     font=('微软', 10), fg='red')
    claim.place(x=50, y=570)

    # 版权信息
    copyright = tk.Label(root, text='@马哥python说 All rights reserved.', font=('仿宋', 10), fg='grey')
    copyright.place(x=290, y=625)

    # 循环消息
    root.mainloop()


def create_login_root():
    """登录窗口（开源版本跳过远程验证）"""
    # 创建主窗口
    root_login = tk.Tk()
    root_login.title('爬蒲公英软件v2.5 | 马哥python说')
    # 设置窗口大小
    root_login.minsize(width=400, height=300)
    # 左上角图标
    try:
        root_login.iconbitmap('mage.ico')
    except:
        pass
    # 菜单
    menu_bar = tk.Menu(root_login)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="关于软件", command=show_about)
    file_menu.add_command(label="使用协议", command=show_agreement)
    file_menu.add_command(label="意见收集", command=open_sugg)
    menu_bar.add_cascade(label="File", menu=file_menu)
    root_login.config(menu=menu_bar)
    # 标题标签
    label_title = ttk.Label(root_login, text="用户登录", font=("Helvetica", 20, "bold"), background="#f0f4f7")
    label_title.pack(pady=20)
    # 控件
    # 用户名标签和输入框
    frame_username = ttk.Frame(root_login)
    frame_username.pack(pady=10)
    label_username = ttk.Label(frame_username, text="账号:", font=("Helvetica", 12), width=10)
    label_username.pack(side="left", padx=5)
    entry_username = ttk.Entry(frame_username, font=("Helvetica", 12), width=20)
    entry_username.pack(side="right")
    # 密码标签和输入框
    frame_password = ttk.Frame(root_login)
    frame_password.pack(pady=10)
    label_password = ttk.Label(frame_password, text="密码:", font=("Helvetica", 12), width=10)
    label_password.pack(side="left", padx=5)
    entry_password = ttk.Entry(frame_password, font=("Helvetica", 12), width=20, show="*")
    entry_password.pack(side="right")
    # 读取上次登录用户
    if os.path.exists('./userinfo.txt'):
        try:
            with open('./userinfo.txt', 'r') as f:
                userinfos = f.readlines()
                last_username = str(userinfos[0]).strip()
                last_password = str(userinfos[1]).strip()
                entry_username.insert(0, last_username)
                entry_password.insert(0, last_password)
        except:
            pass

    def login():
        """[专有代码已移除] 原实现通过 check_user() 连接远程数据库验证许可证"""
        # 开源版本：直接跳过登录进入主界面
        username = entry_username.get()
        print('username:', username)
        password = entry_password.get()
        print('password:', password)
        # [专有代码已移除] 远程许可证验证（check_user → pymysql连接 → cpu_id绑定）
        messagebox.showinfo('登录成功', '开源版本无需验证，直接进入主界面')
        root_login.destroy()
        create_spider_root()

    # 按钮框架
    frame_buttons = ttk.Frame(root_login)
    frame_buttons.pack(pady=20)
    # 登录按钮
    btn_login = ttk.Button(frame_buttons, text="登录", command=login, width=10)
    btn_login.grid(row=0, column=0, padx=10)
    # 退出按钮
    btn_quit = ttk.Button(frame_buttons, text="退出", command=root_login.quit, width=10)
    btn_quit.grid(row=0, column=1, padx=10)

    # 版权信息
    copyright = tk.Label(root_login, text='@马哥python说 All rights reserved.', font=('仿宋', 10), fg='grey')
    copyright.place(x=80, y=275)

    # 循环消息
    root_login.mainloop()


if __name__ == "__main__":
    # 创建日志目录
    if not os.path.exists('logs'):
        os.mkdir('logs')
    log = Log_week()
    logger = log.get_logger()
    # 开启主程序
    create_login_root()
