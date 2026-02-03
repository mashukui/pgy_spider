# pgy_spider
> _马哥原创：用python开发的小红书蒲公英采集软件，一键自动采集蒲公英平台上的达人数据。_

# 一、背景介绍
## 1.0 爬取目标

![爬取目标](https://files.mdnice.com/user/32110/3d7db129-54f5-41fb-9311-2a912de03580.png)

众所周知，蒲公英是小红书推出的优质创作者商业合作服务平台，致力于为品牌和博主提供内容合作服务，可以高效的为品牌匹配出最符合的优质博主。
蒲公英平台，需要有一定权限的企业资质账号才能申请开通。开通之后，进入【寻找博主】页面，即可根据一定的筛选条件过滤出满足的博主列表，如下:
![寻找博主页面](https://files.mdnice.com/user/32110/1c4c584d-2623-466c-b531-c34af8aaffc6.png)

上面是筛选条件，下面是筛选结果。

爬虫功能分为2大类模块：第一是根据筛选条件爬取博主列表，第二是根据爬取到的博主id进入详情页面爬取详细数据。

详情页如下：
![某个博主的详情页](https://files.mdnice.com/user/32110/96bf2ae9-298b-4829-b2e1-ce1d67ca4d61.png)

通过分析网页接口，开发出了爬虫GUI软件，界面如下：(目前已升至v2.3版)<img width="1700" height="1356" alt="蒲公英v2 3" src="https://github.com/user-attachments/assets/ba9c4954-038e-48cf-8613-ee336d81143f" />


共爬取到34个字段，字段如下：

![爬取到的字段](https://files.mdnice.com/user/32110/2677969f-0688-44fc-9ce9-d5899c4897ca.png)

详细演示数据：（看《蒲公英》这个sheet页）
> https://docs.qq.com/sheet/DVEFhZlFKR1NXVEdN?tab=suenot

## 1.1 演示视频
软件操作演示视频：[【爬虫软件】批量采集小红书蒲公英博主信息](https://www.bilibili.com/video/BV14J4m1T7tb)

## 1.2 软件说明
重要说明，请详读：
```python
1. Windows用户可直接双击打开使用，无需Python运行环境，非常方便！
2. 需要在cookie.txt中填入cookie值，持久存储，方便长期使用，支持自动化一键配置
3. 支持筛选笔记搜索关键词、笔记类型(不限/图文笔记为主/视频笔记为主)、粉丝数量、图文报价、搜索页范围。
4. 爬取过程中，有log文件详细记录运行过程，方便回溯
5. 爬取过程中，自动保存结果到csv文件（每爬一条存一次，防止数据丢失）
6. 可爬34个关键字段，含：关键词,页码,小红书昵称,小红书号,地址,机构,数据更新至,小红书链接,粉丝数,账号类型,图文报价,视频报价,合作笔记数,预估阅读单价_图文,图文3秒阅读,日常_阅读中位数,日常_互动中位数,日常_阅读来源发现页占比,日常_阅读来源搜索页占比,合作_阅读中位数,合作_互动中位数,合作_阅读来源发现页占比,合作_阅读来源搜索页占比,女性粉丝占比,年龄占比最多的,账号评估,合作笔记1阅读数,合作笔记2阅读数,合作笔记3阅读数,合作笔记4阅读数,合作笔记5阅读数,合作笔记6阅读数,合作笔记7阅读数,合作笔记8阅读数。
7. 以上爬取字段已经包含，如无法满足个性化要求，可定制开发（接口已调通）
```
以上。
# 二、代码讲解
## 2.0 关于接口
由于采集字段较多，开发者模式中分析接口不止一个，采集程序整合多个接口开发而成，归纳如下：
1. 博主列表接口
2. 日常笔记接口
3. 合作笔记接口
4. 粉丝数接口
5. 阅读单价接口
6. 合作笔记阅读数接口
7. 所属机构接口

以上。
## 2.1 爬虫采集模块
此软件开发成本较高，代码量大、实现逻辑复杂，为保护个人知识版权，防止恶意盗版软件，不展示爬虫核心代码。
## 2.2 一键配置cookie
开始采集前，先用内置的《cookie小工具》自动配置好cookie。
<img width="1734" height="1250" alt="ScreenShot_2026-02-04_074716_952" src="https://github.com/user-attachments/assets/9e561fee-564f-48af-ab2c-2f135a319986" />
这样，获取到的cookie值就自动写入cookie.txt文件中了，告别繁琐的手动获取。

## 2.3 软件界面模块
主窗口部分：
```python
# 创建主窗口
root = tk.Tk()
root.title('蒲公英爬虫v2.0 | 马哥python说')
# 设置窗口大小
root.minsize(width=850, height=650)
```
部分界面控件：
```python
# 笔记关键词
tk.Label(root, justify='left', text='笔记关键词:').place(x=30, y=65)
entry_kw = tk.Text(root, bg='#ffffff', width=22, height=2, )
entry_kw.place(x=105, y=65, anchor='nw')  # 摆放位置
```
日志输出控件：
```python
# 运行日志
tk.Label(root, justify='left', text='运行日志:').place(x=30, y=250)
show_list_Frame = tk.Frame(width=780, height=300)  # 创建<消息列表分区>
show_list_Frame.pack_propagate(0)
show_list_Frame.place(x=30, y=270, anchor='nw')  # 摆放位置
```
## 2.4 日志模块
好的日志功能，方便软件运行出问题后快速定位原因，修复bug。

核心代码：
```python
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
```
软件运行过程中生成的日志文件：
![log文件](https://files.mdnice.com/user/32110/8ffc7309-e1a7-473a-b972-815fb9016063.png)

# 三、付费说明
## 3.1 卡密说明
费用如下：
```python
日卡：使用期限1天，39元。日卡仅能购买一次。适合试用等临时需求
月卡：使用期限1个月，199元。月卡可多次购买。适合短期采集需求
季卡：使用期限3个月，499元。季卡可多次购买。适合中期采集需求
年卡：使用期限1年，999元。年卡可多次购买。适合长期采集需求
```
**方式一：自助开通（推荐）**

开通入口：https://mgnb.pro/product/pgy

**方式二：自助开通**

开通入口：https://kjyjf.xetlk.com/s/2uCpIG

**方式三：手动开通，付费后加v（493882434）对接**
<img width="2324" height="604" alt="收款码v5" src="https://github.com/user-attachments/assets/4c6f2a78-e2b0-4993-a839-92da7b16fe64" />

## 3.2 一机一码
为防止软件被恶意转卖，采用一机一码机制，一个卡密只能在一台电脑运行、不可多电脑运行

## 3.3 软件多开
一台电脑仅允许运行一个软件，不支持软件多开。

## 3.4 软件维护
软件由本人独立原创开发，长期维护更新，提供稳定运行​。

# 四、软件首发
公众号"**老男孩的平凡之路**"，后台回复"**爬蒲公英软件**"获取最新版软件安装包。
<img width="1938" height="364" alt="二维码-公众号放底部v2" src="https://github.com/user-attachments/assets/1e49f616-5b7c-4857-80bb-39412cf7e175" />


