import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
from datetime import datetime
from pathlib import Path
import src.utils as utils
import time
from src.tracking import DATA_LOCK


def rsi(df, workbook):
    df['RSI'] = df.ta.rsi(length=14)
    comment = ""
    rsi_format = {}
    if df['RSI'].iloc[-1] > 70:
        comment = "Overbought (Risk of Pullback)"
        rsi_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    elif df['RSI'].iloc[-1] < 30:
        comment = "Oversold (Potential Reversal)"
        rsi_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif 70 >= df['RSI'].iloc[-1] >= 30:
        comment = "Neutral"
        rsi_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
    return {
        "comment": comment,
        "format": rsi_format
    }


def sma(df, workbook):
    df['SMA_50'] = df.ta.sma(length=50)
    df["SMA_200"] = df.ta.sma(length=200)
    price = df["Close"].iloc[-1]
    sma50_comment = ""
    sma50_format = {}
    sma200_comment = ""
    sma200_format = {}
    sma50_vs_sma200_comment = ""
    sma50_vs_sma200_format = {}
    if price > df["SMA_50"].iloc[-1]:
        sma50_comment = "Bullish"
        sma50_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif price < df["SMA_50"].iloc[-1]:
        sma50_comment = "Bearish"
        sma50_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'ref'})

    if price > df["SMA_200"].iloc[-1]:
        sma200_comment = "Long-Term Bullish Trend"
        sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif price < df["SMA_200"].iloc[-1]:
        sma200_comment = "Long-Term Bearish Trend"
        sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    sma50_vs_sma200_val = ""
    if df["SMA_200"].iloc[-1] > df["SMA_50"].iloc[-1]:
        sma50_vs_sma200_comment = "Death Cross (Strong Sell)"
        sma50_vs_sma200_val = f"{df['SMA_50'].iloc[-1]:.2f} < {df['SMA_200'].iloc[-1]:.2f}"
        sma50_vs_sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    elif df["SMA_200"].iloc[-1] < df["SMA_50"].iloc[-1]:
        sma50_vs_sma200_comment = "Golden Cross (Strong Buy)"
        sma50_vs_sma200_val = f"{df['SMA_50'].iloc[-1]:.2f} > {df['SMA_200'].iloc[-1]:.2f}"
        sma50_vs_sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})

    return {
        "sma50": sma50_comment,
        "sma50_format": sma50_format,
        "sma200": sma200_comment,
        "sma200_format": sma200_format,
        "sma50_vs_sma200": sma50_vs_sma200_comment,
        "sma50_vs_sma200_val": sma50_vs_sma200_val,
        "sma50_vs_sma200_format": sma50_vs_sma200_format,
    }


def volatility(df, workbook):
    # Historical volatility
    df['Returns'] = df['Close'].pct_change()
    # Short-term (1 month)
    df['HV_21'] = df['Returns'].rolling(window=21).std() * (252 ** 0.5) * 100
    # Mid-term (3 months)
    df['HV_63'] = df['Returns'].rolling(window=63).std() * (252 ** 0.5) * 100
    # Long-term (1 year)
    df['HV_252'] = df['Returns'].rolling(window=252).std() * (252 ** 0.5) * 100
    # Historical volatility

    hv_21_comment = ""
    hv_21_format = {}
    hv_63_comment = ""
    hv_63_format = {}
    hv_252_comment = ""
    hv_252_format = {}
    volatility_cone = df["HV_21"].iloc[-1] - df["HV_252"].iloc[-1]
    volatility_cone_comment = ""
    volatility_cone_format = {}
    if df['HV_21'].iloc[-1] < 15:
        hv_21_comment = "Low (Stable)"
        hv_21_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif 15 <= df['HV_21'].iloc[-1] <= 40:
        hv_21_comment = "Moderate (Normal)"
        hv_21_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
    elif 40 < df['HV_21'].iloc[-1]:
        hv_21_comment = "High (Volatile/Risky)"
        hv_21_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    if 0 <= df['HV_63'].iloc[-1] < 15:
        hv_63_comment = "Low (Stable)"
        hv_63_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif 15 <= df['HV_63'].iloc[-1] <= 40:
        hv_63_comment = "Moderate (Normal)"
        hv_63_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
    elif 40 < df['HV_63'].iloc[-1] <= 100:
        hv_63_comment = "High (Volatile/Risky)"
        hv_63_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    if df['HV_252'].iloc[-1] < 15:
        hv_252_comment = "Low (Stable)"
        hv_252_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif 15 <= df['HV_252'].iloc[-1] <= 40:
        hv_252_comment = "Moderate (Normal)"
        hv_252_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
    elif 40 < df['HV_252'].iloc[-1]:
        hv_252_comment = "High (Volatile/Risky)"
        hv_252_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    if volatility_cone > 10:
        volatility_cone_comment = "Expanded (High Stress)"
        volatility_cone_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    elif volatility_cone < -10:
        volatility_cone_comment = "Compressed (Breakout Soon)"
        volatility_cone_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'orange'})
    else:
        volatility_cone_comment = "Normal Deviation"
        volatility_cone_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})

    return {
        "hv21": hv_21_comment,
        "hv21_format": hv_21_format,
        "hv63": hv_63_comment,
        "hv63_format": hv_63_format,
        "hv252": hv_252_comment,
        "hv252_format": hv_252_format,
        "volatility_cone": volatility_cone,
        "volatility_cone_comment": volatility_cone_comment,
        "volatility_cone_format": volatility_cone_format
    }


def volume(df, workbook):
    curr_volume = df["Volume"].iloc[-1]
    vol_avg_short = df["Volume"].rolling(window=10).mean().iloc[-1]
    vol_avg_mid = df["Volume"].rolling(window=50).mean().iloc[-1]
    vol_avg_long = df["Volume"].rolling(window=90).mean().iloc[-1]
    ratio_short = curr_volume / vol_avg_short
    ratio_mid = curr_volume / vol_avg_mid
    ratio_long = curr_volume / vol_avg_long
    short_comment = ""
    short_comment_format = {}
    mid_comment = ""
    mid_comment_format = {}
    long_comment = ""
    long_comment_format = {}
    if ratio_short > 2.0:
        short_comment = "Volume Spike (High Interest)"
        short_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif ratio_short < 0.5:
        short_comment = "Low Liquidity"
        short_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    elif 0.5 <= ratio_short <= 2.0:
        short_comment = "Normal Activity"
        short_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})

    if ratio_mid > 1.0:
        mid_comment = "Trend Supported"
        mid_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    else:
        mid_comment = "Weak Participation"
        mid_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    if ratio_long > 1.0:
        long_comment = "Accumulation Phase"
        long_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    else:
        long_comment = "Distribution Phase"
        long_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    return {
        "ratio_short": ratio_short,
        "ratio_long": ratio_long,
        "ratio_mid": ratio_mid,
        "short_comment": short_comment,
        "short_comment_format": short_comment_format,
        "mid_comment": mid_comment,
        "mid_comment_format": mid_comment_format,
        "long_comment": long_comment,
        "long_comment_format": long_comment_format
    }


def create_image(df, code, currency_symbol):
    if df.empty:
        return None

    plots = []
    if 'RSI' in df.columns and not df['RSI'].dropna().empty:
        plots.append(mpf.make_addplot(df['RSI'], panel=2, color='#9F4800', label='RSI (14)', ylabel = 'RSI', width=2))
    if 'SMA_50' in df.columns and not df['SMA_50'].dropna().empty:
        plots.append(mpf.make_addplot(df['SMA_50'], panel=0, color='orange', label='SMA 50 (short-term)', width=1.5))
    if 'SMA_200' in df.columns and not df['SMA_200'].dropna().empty:
        plots.append(mpf.make_addplot(df['SMA_200'], panel=0, color='blue', label="SMA 200 (long-term)", width=1.5))
    if 'HV_21' in df.columns and not df['HV_21'].dropna().empty:
        plots.append(mpf.make_addplot(df['HV_21'], panel=3, color='#E8020B', width=2, label='HV-21 (short-term)', ylabel = 'HV'))
    if 'HV_63' in df.columns and not df['HV_63'].dropna().empty:
       plots.append( mpf.make_addplot(df['HV_63'], panel=3, color='#FF7C01', width=2, label='HV-63 (mid-term)'))
    if 'HV_252' in df.columns and not df['HV_252'].dropna().empty:
        plots.append(mpf.make_addplot(df['HV_252'], panel=3, color='#1CC838', width=2, label='HV-252 (annual)'))

    my_style = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.size': 12}, y_on_right = False)
    fig, axlist = mpf.plot(
        df,
        type='candle',
        style=my_style,
        volume=True,
        volume_panel=1,
        ylabel = f"Price ({currency_symbol})",
        xrotation=15,
        datetime_format = "%Y-%m-%d",
        addplot=plots,
        panel_ratios=(6, 3, 3, 3),
        num_panels=4,
        figsize=(30, 20),
        returnfig=True
    )
    fig.suptitle(f'{code} Annual Analysis', y=0.90, fontsize=14, weight='bold')
    fig.subplots_adjust(top=0.95)
    axlist[0].legend(loc='lower right', fontsize=10)
    for ax in axlist:
        if ax.get_legend_handles_labels()[1]:
            ax.legend(loc='lower right', fontsize=10)

    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
    plt.close(fig)
    return img_buffer


def analysis_report(data, which_asset, username, code):
    ticker = yf.Ticker(code)
    # to calculate hv-252 properly, we need data with at least 253 days
    # therefore we use 2y period
    df = ticker.history(period="2y", interval="1d")
    with DATA_LOCK:
        currency = data["users"][username][which_asset][code]["currency"]
    currency_symbol = utils.get_currency(currency)

    now = datetime.now()
    file_date = now.strftime("%Y-%m-%d_%H.%M.%S")
    file_name = f"{code}{file_date}report.xlsx"
    desktop_path = Path.home() / "Desktop"
    full_path = desktop_path / file_name

    with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        rsi_comment = rsi(df, workbook)
        sma_comment = sma(df, workbook)
        volatility_comment = volatility(df, workbook)
        volume_comment = volume(df, workbook)
        df_1y = df.iloc[-252:].copy()
        left_title_format = workbook.add_format({'bold':True, 'italic':True, 'align':'left'})
        right_title_format = workbook.add_format({'bold':True, 'italic':True, 'align': 'right'})
        center_title_format = workbook.add_format({'bold':True, 'italic':True, 'align': 'center'})
        center_format = workbook.add_format({'align': 'center'})
        left_format = workbook.add_format({'align': 'left'})
        right_format = workbook.add_format({'align': 'right'})
        # Sheet 'Summary'
        worksheet_summary = workbook.add_worksheet("Summary")
        worksheet_summary.write(0, 0, "Analysis Date:", left_title_format)
        current_date = now.date().strftime("%Y-%m-%d")
        current_time = now.time().strftime("%H:%M:%S")
        worksheet_summary.write(0, 1, f"{current_date} {current_time}")
        worksheet_summary.write(1, 0, "Financial Asset:", left_title_format)
        worksheet_summary.write(1, 1, f"{code}")
        worksheet_summary.write(2, 0, "Price:", left_title_format)
        worksheet_summary.write(2, 1, f"{df_1y['Close'].iloc[-1]:.2f} {currency_symbol}")
        worksheet_summary.write(4, 0, "1. TREND & MOMENTUM", left_title_format)
        worksheet_summary.write(4, 1, "VALUE", center_title_format)
        worksheet_summary.write(4, 2, "COMMENT", right_title_format)
        worksheet_summary.write(5, 0, "RSI (14)", left_format)
        worksheet_summary.write(5, 1, f"{df_1y['RSI'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(5, 2, f"{rsi_comment['comment']}", rsi_comment['format'])
        worksheet_summary.write(6, 0, "SMA 50", left_format)
        worksheet_summary.write(6, 1, f"{df_1y['SMA_50'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(6, 2, f"{sma_comment['sma50']}", sma_comment['sma50_format'])
        worksheet_summary.write(7, 0, "SMA 200", left_format)
        worksheet_summary.write(7, 1, f"{df_1y['SMA_200'].iloc[-1]:.2f}",center_format)
        worksheet_summary.write(7, 2, f"{sma_comment['sma200']}", sma_comment['sma200_format'])
        worksheet_summary.write(8, 0, "SMA 50 vs SMA 200", left_format)
        worksheet_summary.write(8, 1, f"{sma_comment['sma50_vs_sma200_val']}", center_format)
        worksheet_summary.write(8, 2, f"{sma_comment['sma50_vs_sma200']}", sma_comment['sma50_vs_sma200_format'])
        worksheet_summary.write(10, 0, "2. RISK & VOLATILITY", left_title_format)
        worksheet_summary.write(10, 1, "ANNUALIZED", center_title_format)
        worksheet_summary.write(10, 2, "COMMENT", right_title_format)
        worksheet_summary.write(11, 0, "Short-term (21 days)", left_format)
        worksheet_summary.write(11, 1, f"{df_1y['HV_21'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(11, 2, f"{volatility_comment['hv21']}", volatility_comment['hv21_format'])
        worksheet_summary.write(12, 0, "Mid-term (63 days)", left_format)
        worksheet_summary.write(12, 1, f"{df_1y['HV_63'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(12, 2, f"{volatility_comment['hv63']}", volatility_comment['hv63_format'])
        worksheet_summary.write(13, 0, "Long-term (252 days)", left_format)
        worksheet_summary.write(13, 1, f"{df_1y['HV_252'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(13, 2, f"{volatility_comment['hv252']}", volatility_comment['hv252_format'])
        worksheet_summary.write(14, 0, "Volatility Cone", left_format)
        worksheet_summary.write(14, 1, f"Difference: {volatility_comment['volatility_cone']:.2f}", center_format)
        worksheet_summary.write(14, 2, f"{volatility_comment['volatility_cone_comment']}",volatility_comment['volatility_cone_format'])
        worksheet_summary.write(16, 0, "3. VOLUME ANALYSIS", left_title_format)
        worksheet_summary.write(16, 1, "RVOL (Percentage)", center_title_format)
        worksheet_summary.write(16, 2, "COMMENT",right_title_format)
        worksheet_summary.write(17, 0, "Short-term (10 days)",left_format)
        worksheet_summary.write(17, 1, f"{volume_comment['ratio_short']:.2f}x",center_format)
        worksheet_summary.write(17, 2, f"{volume_comment['short_comment']}",volume_comment['short_comment_format'])
        worksheet_summary.write(18, 0, "Mid-term (50 days)", left_format)
        worksheet_summary.write(18, 1, f"{volume_comment['ratio_mid']:.2f}x", center_format)
        worksheet_summary.write(18, 2, f"{volume_comment['mid_comment']}", volume_comment['mid_comment_format'])
        worksheet_summary.write(19, 0, "Long-term (90 days)", left_format)
        worksheet_summary.write(19, 1, f"{volume_comment['ratio_long']:.2f}x", center_format)
        worksheet_summary.write(19, 2, f"{volume_comment['long_comment']}",volume_comment['long_comment_format'])
        worksheet_summary.set_column(0, 2, 25)
        # Sheet 'Summary'
        # Sheet 'Graphical Analysis'
        worksheet_graph = workbook.add_worksheet("Graphical Analysis")
        worksheet_graph.insert_image(0, 0, "analysis.png", {'image_data': create_image(df_1y, code, currency_symbol)})
        worksheet_graph.hide_gridlines(2)
        # Sheet 'Graphical Analysis'
        # Sheet 'Raw Data'
        df.index = df.index.date
        df.to_excel(writer, sheet_name='Raw Data', index=True)
        worksheet_raw = writer.sheets['Raw Data']
        worksheet_raw.set_column(0, 16, 40)
        # Sheet 'Raw Data'
    print(f"{file_name} is successfully saved to Desktop.")
    time.sleep(2)