# Description

使用天勤SDK监控仓位盈亏变化。

## 前置包安装

```powershell
pip install rich
pip install tqsdk
```

## 用法示例

```powershell
python main.py --src positions_P01S03_HXO_20240108-TS2.csv --account user_account --password user_password --info InstrumentInfoPath --config ConfigPath
```

## 说明

+ --src 后面的文件是仓位文件，应当包含以下几个字段
  + contract 合约代码 MA405
  + direction 方向 多=1，空=-1
  + qty 数量，>=0
  + aver_cost_price 成本价
  + last_market_price 前一日收盘价,或结算价
+ --account 天勤SDK账户
+ --password 天勤SDK密码
+ --info InstrumentInfoPath "InstrumentInfo3.csv" 包含合约乘数等信息的文本文件
+ --config ConfigPath "viewer.ini" 包含输出的色彩配置信息
