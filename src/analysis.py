import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib
# to prevent matplotlib running as GUI at the background
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
from datetime import datetime
from pathlib import Path
import src.utils as utils
import time
from src.shared import DATA_LOCK


exchange_days = {
    # 🇺🇸 US
    "NMS": 252,
    "NYQ": 252,
    "ASE": 252,

    # 🇹🇷 Turkey
    "IST": 252,

    # 🇬🇧 UK
    "LSE": 252,

    # 🇩🇪 Germany
    "XETRA": 252,

    # 🇫🇷 France
    "EPA": 252,

    # 🇨🇭 Switzerland
    "SWX": 252,

    # 🇯🇵 Japan
    "TYO": 245,

    # 🇭🇰 Hong Kong
    "HKG": 245,

    # 🇨🇳 China
    "SHH": 240,
    "SHE": 240,

    # 🌍 Forex
    "CCY": 252,

    # 🪙 Crypto
    "CCC": 365,

    # 🟡 Commodities
    "CMX": 252,
    "NYM": 252,

    # fallback
    "UNKNOWN": 252
}

def get_exchange_days(exchange):
    return exchange_days.get(exchange, exchange_days['UNKNOWN'])

def rsi(df, workbook):
    df['RSI'] = df.ta.rsi(length=14)

    if df['RSI'].iloc[-1] > 70:
        comment = "Overbought (Risk of Pullback)"
        rsi_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    elif df['RSI'].iloc[-1] < 30:
        comment = "Oversold (Potential Reversal)"
        rsi_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    else:
        comment = "Neutral"
        rsi_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})

    return {
        "comment": comment,
        "format": rsi_format
    }

def macd(df, workbook):
    df.ta.macd(append = True, fast = 12, slow = 26, signal = 9)
    if df['MACD_12_26_9'].iloc[-1] > df['MACDs_12_26_9'].iloc[-1]:
        macd_comment = "Bullish Momentum (Buying Pressure)"
        macd_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
        macd_val = f"{df['MACD_12_26_9'].iloc[-1]:.2f} > {df['MACDs_12_26_9'].iloc[-1]:.2f}"
    elif df['MACD_12_26_9'].iloc[-1] < df['MACDs_12_26_9'].iloc[-1]:
        macd_comment = "Bearish Momentum (Selling Pressure)"
        macd_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
        macd_val = f"{df['MACD_12_26_9'].iloc[-1]:.2f} < {df['MACDs_12_26_9'].iloc[-1]:.2f}"
    else:
        macd_comment = "Neutral"
        macd_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
        macd_val = f"{df['MACD_12_26_9'].iloc[-1]:.2f} = {df['MACDs_12_26_9'].iloc[-1]:.2f}"
    return {
        "comment": macd_comment,
        "format": macd_format,
        "value": macd_val
    }

def atr(df, workbook):
    df.ta.atr(length=14, append=True)
    last_price = df["Close"].iloc[-1]
    atr_percentage = df['ATRr_14'].iloc[-1] / last_price * 100

    if atr_percentage > 3:
        atr_comment = "High Volatility"
        atr_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    elif atr_percentage < 1.5:
        atr_comment = "Low Volatility"
        atr_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    else:
        atr_comment = "Normal Volatility"
        atr_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})

    return {
        "comment": atr_comment,
        "format": atr_format,
        "value": f"{atr_percentage:.2f}%"
    }

def bollinger(df, workbook):
    bbands = df.ta.bbands(length=20)
    # python wants a Series to add a column to a dataframe
    # therefore we use iloc
    df['BBL_20_2.0'] = bbands.filter(like = 'BBL').iloc[:,0]
    df['BBM_20_2.0'] = bbands.filter(like = 'BBM').iloc[:,0]
    df['BBU_20_2.0'] = bbands.filter(like = 'BBU').iloc[:,0]
    df['BBP_20_2.0'] = bbands.filter(like = 'BBP').iloc[:,0]
    df['BBB_20_2.0'] = bbands.filter(like = 'BBB').iloc[:,0]
    last_price = df["Close"].iloc[-1]
    if last_price >= df['BBU_20_2.0'].iloc[-1]:
        boll_comment = "Overbought (Resistance)"
        boll_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
        boll_val = f"Price: {last_price:.2f} >= Upper: {df['BBU_20_2.0'].iloc[-1]:.2f}"
    elif last_price <= df['BBL_20_2.0'].iloc[-1]:
        boll_comment = "Oversold (Support)"
        boll_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
        boll_val = f"Price: {last_price:.2f} <= Lower: {df['BBL_20_2.0'].iloc[-1]:.2f}"
    else:
        boll_comment = "Neutral"
        boll_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
        boll_val = f"L: {df['BBL_20_2.0'].iloc[-1]:.2f} < Price: {last_price:.2f} < U: {df['BBU_20_2.0'].iloc[-1]:.2f}"
    return {
        "comment": boll_comment,
        "format": boll_format,
        "value": boll_val
    }

def obv(df, workbook):
    df.ta.obv(append=True)
    sma20_obv = df['OBV'].rolling(window=20).mean().iloc[-1]

    if df['OBV'].iloc[-1] > sma20_obv:
        obv_comment = "Accumulation (Smart Money IN)"
        obv_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
        obv_val = f"OBV: {df['OBV'].iloc[-1]/1e6:.2f}M > {sma20_obv/1e6:.2f}M (SMA)"
    elif df['OBV'].iloc[-1] < sma20_obv:
        obv_comment = "Distribution (Smart Money OUT)"
        obv_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
        obv_val = f"OBV: {df['OBV'].iloc[-1]/1e6:.2f}M < {sma20_obv/1e6:.2f}M (SMA)"
    else:
        obv_comment = "Neutral"
        obv_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
        obv_val = f"OBV: {df['OBV'].iloc[-1]/1e6:.2f}M = {sma20_obv/1e6:.2f}M (SMA)"

    return {
        "comment": obv_comment,
        "format": obv_format,
        "value": obv_val
    }

def sma(df, workbook):
    df['SMA_50'] = df.ta.sma(length=50)
    df["SMA_200"] = df.ta.sma(length=200)
    price = df["Close"].iloc[-1]

    if price > df["SMA_50"].iloc[-1]:
        sma50_comment = "Bullish"
        sma50_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif price < df["SMA_50"].iloc[-1]:
        sma50_comment = "Bearish"
        sma50_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'ref'})
    else:
        sma50_comment = "Neutral"
        sma50_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})

    if price > df["SMA_200"].iloc[-1]:
        sma200_comment = "Long-Term Bullish Trend"
        sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif price < df["SMA_200"].iloc[-1]:
        sma200_comment = "Long-Term Bearish Trend"
        sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    else:
        sma200_comment = "Long-Term Neutral Trend"
        sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})

    if df["SMA_200"].iloc[-1] > df["SMA_50"].iloc[-1]:
        sma50_vs_sma200_comment = "Death Cross (Strong Sell)"
        sma50_vs_sma200_val = f"{df['SMA_50'].iloc[-1]:.2f} < {df['SMA_200'].iloc[-1]:.2f}"
        sma50_vs_sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    elif df["SMA_200"].iloc[-1] < df["SMA_50"].iloc[-1]:
        sma50_vs_sma200_comment = "Golden Cross (Strong Buy)"
        sma50_vs_sma200_val = f"{df['SMA_50'].iloc[-1]:.2f} > {df['SMA_200'].iloc[-1]:.2f}"
        sma50_vs_sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    else:
        sma50_vs_sma200_comment = "Neutral"
        sma50_vs_sma200_val = f"{df['SMA_50'].iloc[-1]:.2f} = {df['SMA_200'].iloc[-1]:.2f}"
        sma50_vs_sma200_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})

    return {
        "sma50": sma50_comment,
        "sma50_format": sma50_format,
        "sma200": sma200_comment,
        "sma200_format": sma200_format,
        "sma50_vs_sma200": sma50_vs_sma200_comment,
        "sma50_vs_sma200_val": sma50_vs_sma200_val,
        "sma50_vs_sma200_format": sma50_vs_sma200_format,
    }

def volatility(df, workbook, ticker, exchange):
    annual_exchange_day_count = get_exchange_days(exchange)
    # Historical volatility
    df['Returns'] = df['Close'].pct_change()
    # Short-term (1 month)
    df['HV_21'] = df['Returns'].rolling(window=21).std() * (annual_exchange_day_count ** 0.5) * 100
    # Mid-term (3 months)
    df['HV_63'] = df['Returns'].rolling(window=63).std() * (annual_exchange_day_count ** 0.5) * 100
    # Long-term (1 year)
    df['HV_252'] = df['Returns'].rolling(window=252).std() * (annual_exchange_day_count ** 0.5) * 100
    # Historical volatility

    if df['HV_21'].iloc[-1] < 15:
        hv_21_comment = "Low (Stable)"
        hv_21_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif 15 <= df['HV_21'].iloc[-1] <= 40:
        hv_21_comment = "Moderate (Normal)"
        hv_21_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
    else:
        hv_21_comment = "High (Volatile/Risky)"
        hv_21_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    if df['HV_63'].iloc[-1] < 15:
        hv_63_comment = "Low (Stable)"
        hv_63_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif 15 <= df['HV_63'].iloc[-1] <= 40:
        hv_63_comment = "Moderate (Normal)"
        hv_63_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
    else:
        hv_63_comment = "High (Volatile/Risky)"
        hv_63_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    if df['HV_252'].iloc[-1] < 15:
        hv_252_comment = "Low (Stable)"
        hv_252_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif 15 <= df['HV_252'].iloc[-1] <= 40:
        hv_252_comment = "Moderate (Normal)"
        hv_252_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'black'})
    else:
        hv_252_comment = "High (Volatile/Risky)"
        hv_252_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})

    volatility_cone = df["HV_21"].iloc[-1] - df["HV_252"].iloc[-1]
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

    if ratio_short > 2.0:
        short_comment = "Volume Spike (High Interest)"
        short_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'green'})
    elif ratio_short < 0.5:
        short_comment = "Low Liquidity"
        short_comment_format = workbook.add_format({'align': 'right', 'bold': True, 'font_color': 'red'})
    else:
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
        plots.append(mpf.make_addplot(df['SMA_50'], panel=0, color='#ff7b00', label='SMA 50 (short-term)', width=1.5))
    if 'SMA_200' in df.columns and not df['SMA_200'].dropna().empty:
        plots.append(mpf.make_addplot(df['SMA_200'], panel=0, color='blue', label="SMA 200 (long-term)", width=1.5))
    if 'HV_21' in df.columns and not df['HV_21'].dropna().empty:
        plots.append(mpf.make_addplot(df['HV_21'], panel=4, color='#E8020B', width=2, label='HV-21 (short-term)', ylabel = 'HV'))
    if 'HV_63' in df.columns and not df['HV_63'].dropna().empty:
       plots.append( mpf.make_addplot(df['HV_63'], panel=4, color='#FF7C01', width=2, label='HV-63 (mid-term)'))
    if 'HV_252' in df.columns and not df['HV_252'].dropna().empty:
        plots.append(mpf.make_addplot(df['HV_252'], panel=4, color='#1CC838', width=2, label='HV-252 (annual)'))
    if 'BBL_20_2.0' in df.columns and not df['BBL_20_2.0'].dropna().empty:
        bbl = True
        plots.append(mpf.make_addplot(df['BBL_20_2.0'], panel = 0, color = "#00ffa2", label='Bollinger Lower Band (20)', width = 1.5))
    else:
        bbl = False
    if 'BBU_20_2.0' in df.columns and not df['BBU_20_2.0'].dropna().empty:
        bbu = True
        plots.append(mpf.make_addplot(df['BBU_20_2.0'], panel = 0, color = "#ff6bea", label='Bollinger Upper Band (20)', width = 1.5))
    else:
        bbu = False
    if bbl and bbu:
        fill_dict = dict(y1 = df['BBL_20_2.0'].values, y2 = df['BBU_20_2.0'].values, alpha = 0.1, color = 'gray')
    else:
        fill_dict = None
    if 'BBM_20_2.0' in df.columns and not df['BBM_20_2.0'].dropna().empty:
        plots.append(mpf.make_addplot(df['BBM_20_2.0'], panel = 0, color = "#ffff00", label='SMA 20 (Bollinger Mid)', width = 1.5))
    if 'OBV' in df.columns and not df['OBV'].dropna().empty:
        # OBV have very high values, hence it may crush other indicators
        # Therefore we need to use an extra axis to show its values.
        plots.append(mpf.make_addplot(df['OBV'], panel = 1, color = '#0040ff', label = "On Balance Volume (OBV)", width = 2, secondary_y = True, ylabel = 'OBV (1 Billion)'))
    if 'MACD_12_26_9' in df.columns and not df['MACD_12_26_9'].dropna().empty:
        plots.append(mpf.make_addplot(df['MACD_12_26_9'], panel = 3, color = '#0040ff', label = "MACD Line", width = 2, ylabel = 'MACD'))
    if 'MACDs_12_26_9' in df.columns and not df['MACDs_12_26_9'].dropna().empty:
        plots.append(mpf.make_addplot(df['MACDs_12_26_9'], panel=3, color='#FF7C01', label="MACD Signal Line", width=2))
    if 'MACDh_12_26_9' in df.columns and not df['MACDh_12_26_9'].dropna().empty:
        macd_histogram_colors = ['#4DC790' if val >= 0 else '#FD6B6C' for val in df['MACDh_12_26_9']]
        plots.append(mpf.make_addplot(df['MACDh_12_26_9'], panel = 3, color = macd_histogram_colors, type = 'bar', label = "MACD Histogram ", width = 1.5, secondary_y = False))
    if 'ATRr_14' in df.columns and not df['ATRr_14'].dropna().empty:
        # ATR have very high values, hence it may crush other indicators
        # Therefore we need to use an extra axis to show its values.
        plots.append(mpf.make_addplot(df['ATRr_14'], panel = 4, color = 'black', label = "ATR 14", width = 2, secondary_y = True, ylabel = 'ATR 14'))
    my_style = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.size': 12}, y_on_right = False)
    arguments = dict(
        type='candle',
        style=my_style,
        volume=True,
        volume_panel=1,
        ylabel=f"Price ({currency_symbol})",
        xrotation=15,
        datetime_format="%Y-%m-%d",
        addplot=plots,
        panel_ratios=(6, 4, 4, 4, 4),
        num_panels=5,
        figsize=(45, 30),
        returnfig=True
    )
    if fill_dict:
        arguments['fill_between'] = fill_dict
    # ** (asterisk) operator is used for unpacking the dict arguments
    fig, axlist = mpf.plot(df, **arguments)
    fig.suptitle(f'{code} Annual Analysis', y=0.90, fontsize=16, weight='bold')
    fig.subplots_adjust(top=0.95)

    for i in range(1, len(axlist),2):
        axlist[i].yaxis.label.set_rotation(270)
        axlist[i].yaxis.set_label_coords(1.02, 0.5)

    for i in range(0,len(axlist),2):
        ax_main = axlist[i]
        ax_sec = axlist[i+1] if i+1 < len(axlist) else None
        handles,labels = ax_main.get_legend_handles_labels()
        if ax_sec:
            handles_sec, labels_sec = ax_sec.get_legend_handles_labels()
            # by adding the second ax's to main one
            # collision of the legends is prevented
            handles.extend(handles_sec)
            labels.extend(labels_sec)
            ax_sec_legend = ax_sec.get_legend()
            if ax_sec_legend:
                ax_sec_legend.set_visible(False)
        if handles:
            ax_main.legend(handles, labels, loc='upper left', fontsize=10)

    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
    plt.close(fig)
    return img_buffer

def analysis_report(data, which_asset, username, code):
    ticker = yf.Ticker(code)
    # to calculate hv-252 properly, we need data with at least 253 days
    # therefore we use 2y period
    try:
        df = ticker.history(period="2y", interval="1d")
        time.sleep(0.25)
        exchange = ticker.fast_info['exchange']
    except Exception:
        print(f"[ERROR]: Data could not fetched for {code} (API Error). Excel report could not be created. Please try again.")
        return

    with DATA_LOCK:
        currency = data["users"][username][which_asset][code]["currency"]
    currency_symbol = utils.get_currency(currency)
    annual_exchange_day_count = exchange_days.get(exchange, exchange_days['UNKNOWN'])
    now = datetime.now()
    file_date = now.strftime("%Y-%m-%d_%H.%M.%S")
    file_name = f"{code}_{file_date}_report.xlsx"
    desktop_path = Path.home() / "Desktop"
    full_path = desktop_path / file_name

    with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        rsi_comment = rsi(df, workbook)
        sma_comment = sma(df, workbook)
        volatility_comment = volatility(df, workbook, ticker, exchange)
        volume_comment = volume(df, workbook)
        macd_comment = macd(df, workbook)
        atr_comment = atr(df, workbook)
        boll_comment = bollinger(df, workbook)
        obv_comment = obv(df, workbook)
        df_1y = df.iloc[annual_exchange_day_count:].copy()
        left_title_format = workbook.add_format({'bold':True, 'italic':True, 'align':'left'})
        right_title_format = workbook.add_format({'bold':True, 'italic':True, 'align': 'right'})
        center_title_format = workbook.add_format({'bold':True, 'italic':True, 'align': 'center'})
        center_format = workbook.add_format({'align': 'center'})
        left_format = workbook.add_format({'align': 'left'})
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
        worksheet_summary.write(9, 0, "MACD vs Signal Lines", left_format)
        worksheet_summary.write(9, 1, f"{macd_comment['value']}", center_format)
        worksheet_summary.write(9, 2, f"{macd_comment['comment']}", macd_comment['format'])
        worksheet_summary.write(11, 0, "2. RISK & VOLATILITY", left_title_format)
        worksheet_summary.write(11, 1, "ANNUALIZED", center_title_format)
        worksheet_summary.write(11, 2, "COMMENT", right_title_format)
        worksheet_summary.write(12, 0, "Short-term (21 days)", left_format)
        worksheet_summary.write(12, 1, f"{df_1y['HV_21'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(12, 2, f"{volatility_comment['hv21']}", volatility_comment['hv21_format'])
        worksheet_summary.write(13, 0, "Mid-term (63 days)", left_format)
        worksheet_summary.write(13, 1, f"{df_1y['HV_63'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(13, 2, f"{volatility_comment['hv63']}", volatility_comment['hv63_format'])
        worksheet_summary.write(14, 0, "Long-term (252 days)", left_format)
        worksheet_summary.write(14, 1, f"{df_1y['HV_252'].iloc[-1]:.2f}", center_format)
        worksheet_summary.write(14, 2, f"{volatility_comment['hv252']}", volatility_comment['hv252_format'])
        worksheet_summary.write(15, 0, "Volatility Cone", left_format)
        worksheet_summary.write(15, 1, f"Difference: {volatility_comment['volatility_cone']:.2f}", center_format)
        worksheet_summary.write(15, 2, f"{volatility_comment['volatility_cone_comment']}",volatility_comment['volatility_cone_format'])
        worksheet_summary.write(16, 0, "ATR (% of Price)", left_format)
        worksheet_summary.write(16, 1, f"{atr_comment['value']}", center_format)
        worksheet_summary.write(16, 2, f"{atr_comment['comment']}", atr_comment['format'])
        worksheet_summary.write(17, 0, "Bollinger Bands Position", left_format)
        worksheet_summary.write(17,1,f"{boll_comment['value']}", center_format)
        worksheet_summary.write(17, 2, f"{boll_comment['comment']}", boll_comment['format'])
        worksheet_summary.write(19, 0, "3. VOLUME ANALYSIS", left_title_format)
        worksheet_summary.write(19, 1, "RVOL (Percentage)", center_title_format)
        worksheet_summary.write(19, 2, "COMMENT",right_title_format)
        worksheet_summary.write(20, 0, "Short-term (10 days)",left_format)
        worksheet_summary.write(20, 1, f"{volume_comment['ratio_short']:.2f}x",center_format)
        worksheet_summary.write(20, 2, f"{volume_comment['short_comment']}",volume_comment['short_comment_format'])
        worksheet_summary.write(21, 0, "Mid-term (50 days)", left_format)
        worksheet_summary.write(21, 1, f"{volume_comment['ratio_mid']:.2f}x", center_format)
        worksheet_summary.write(21, 2, f"{volume_comment['mid_comment']}", volume_comment['mid_comment_format'])
        worksheet_summary.write(22, 0, "Long-term (90 days)", left_format)
        worksheet_summary.write(22, 1, f"{volume_comment['ratio_long']:.2f}x", center_format)
        worksheet_summary.write(22, 2, f"{volume_comment['long_comment']}",volume_comment['long_comment_format'])
        worksheet_summary.write(23, 0, "OBV Trend (vs 20d SMA)", left_format)
        worksheet_summary.write(23,1,f"{obv_comment['value']}", center_format)
        worksheet_summary.write(23,2,f"{obv_comment['comment']}", obv_comment['format'])
        worksheet_summary.set_column(0, 0, 24)
        worksheet_summary.set_column(1, 1, 30)
        worksheet_summary.set_column(2, 2, 30)
        # Sheet 'Summary'
        # Sheet 'Graphical Analysis'
        worksheet_graph = workbook.add_worksheet("Graphical Analysis")
        worksheet_graph.insert_image(0, 0, "analysis.png", {'image_data': create_image(df_1y, code, currency_symbol)})
        worksheet_graph.hide_gridlines(2)
        # Sheet 'Graphical Analysis'
        # Sheet 'Raw Data'
        df_1y.index = df_1y.index.date
        df_1y.to_excel(writer, sheet_name='Raw Data', index=True)
        worksheet_raw = writer.sheets['Raw Data']
        worksheet_raw.set_column(0, 0, 9)
        worksheet_raw.set_column(1, 24, 40)
        # Sheet 'Raw Data'
    print(f"{file_name} is successfully saved to Desktop.")
    time.sleep(2)