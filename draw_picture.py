# 导入数据处理模块
import pandas as pd
import re
# 导入配置项
from pyecharts import options as opts
# 导入图形
from pyecharts.charts import Pie, Bar, Line

# 读取CSV文件
try:
    df = pd.read_csv('./csv_data/LLM_jobs1.csv')
    print("LLM_jobs1.csv文件读取成功！")
    
    # 打印列名以便确认
    print("CSV文件的列名:", df.columns.tolist())
    
    # 检查必要的列是否存在
    if '招聘地区' not in df.columns:
        print("错误: CSV文件中没有'招聘地区'列")
        exit()
    
    # 数据清洗：提取城市名称（去除区名）
    def extract_city(location):
        if pd.isna(location):
            return "未知"
        # 匹配城市名称（通常是2-3个汉字）
        location_str = str(location)
        # 先尝试匹配直辖市和特别行政区
        if any(city in location_str for city in ['北京', '上海', '天津', '重庆', '香港', '澳门']):
            for city in ['北京', '上海', '天津', '重庆', '香港', '澳门']:
                if city in location_str:
                    return city
        # 匹配普通城市（通常是2-3个汉字后跟"市"）
        match = re.search(r'^([\u4e00-\u9fa5]{2,3})市?', location_str)
        if match:
            return match.group(1) + "市"
        return location_str
    
    # 应用清洗函数
    df['清洗后城市'] = df['招聘地区'].apply(extract_city)
    
    # 获取招聘地区分布情况数据（饼图）
    x_area = df['清洗后城市'].value_counts().index.to_list()
    y_area = df['清洗后城市'].value_counts().to_list()

    pie_chart = (
        Pie()
        .add(
            "",
            [list(z) for z in zip(x_area, y_area)],
            center=["40%", "50%"],
        )
        .set_global_opts(
            # 设置可视化标题
            title_opts=opts.TitleOpts(title="招聘地区分布情况"),
            legend_opts=opts.LegendOpts(type_="scroll", pos_left="80%", orient="vertical"),
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        # 导出可视化效果: 保存html文件
        .render("pie_招聘地区分布情况.html")
    )

    # 获取要求工作经验分布情况数据（柱状图）
    if '要求工作经验' in df.columns:
        x_work_exp = df['要求工作经验'].value_counts().index.to_list()
        y_work_exp = df['要求工作经验'].value_counts().to_list()

        bar_chart = (
            Bar()
            .add_xaxis(x_work_exp)
            .add_yaxis("要求工作经验", y_work_exp, stack="stack1")
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-要求工作经验分布情况"))
            .render("bar_要求工作经验分布情况.html")
        )
    else:
        print("警告: CSV文件中没有'要求工作经验'列")

    # 获取要求学历分布情况数据（折线图）
    if '要求学历' in df.columns:
        x_edu = df['要求学历'].value_counts().index.to_list()
        y_edu = df['要求学历'].value_counts().to_list()

        line_chart = (
            Line()
            .add_xaxis(x_edu)
            .add_yaxis("要求学历", y_edu, is_connect_nones=True)
            .set_global_opts(title_opts=opts.TitleOpts(title="Line-要求学历分布"))
            .render("line_要求学历分布.html")
        )
    else:
        print("警告: CSV文件中没有'要求学历'列")
        
    print("图表生成完成！")
    
except FileNotFoundError:
    print("LLM_jobs1.csv文件不存在，请检查文件路径是否正确！")
except pd.errors.ParserError:
    print("LLM_jobs1.csv文件格式可能有问题，无法正确解析，请检查文件内容格式。")
except Exception as e:
    print(f"处理过程中出现错误: {e}")