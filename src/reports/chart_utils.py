import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def generate_revenue_chart(years, revenue):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.bar(years, revenue, color='#1f77b4')
    ax.set_title("Revenue Over Time")
    ax.set_ylabel("Cr")
    ax.set_xticks(years); ax.set_xticklabels([str(int(y)) if y else '' for y in years], rotation=45)
    # plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_net_profit_chart(years, net_profit):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    colors = ['#2ca02c' if v >= 0 else '#d62728' for v in net_profit]
    ax.bar(years, net_profit, color=colors)
    ax.set_title("Net Profit Over Time")
    ax.set_ylabel("Cr")
    ax.set_xticks(years); ax.set_xticklabels([str(int(y)) if y else '' for y in years], rotation=45)
    # plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_roe_roce_chart(years, roe, roce):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.plot(years, roe, marker='o', label='ROE (%)', color='#ff7f0e')
    ax.plot(years, roce, marker='s', label='ROCE (%)', color='#9467bd')
    ax.set_title("ROE vs ROCE")
    ax.set_ylabel("%")
    ax.set_xticks(years)
    ax.set_xticklabels([str(int(y)) if y else '' for y in years], rotation=45)
    ax.legend()
    # plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_bs_stacked_bar(years, equity, debt, other_liab, fixed_assets, working_capital, other_assets):
    fig, axes = plt.subplots(1, 2, figsize=(6, 2.5), sharey=True)
    
    # Liabilities
    axes[0].bar(years, equity, label='Equity', color='#1f77b4')
    axes[0].bar(years, debt, bottom=equity, label='Debt', color='#d62728')
    axes[0].bar(years, other_liab, bottom=np.array(equity)+np.array(debt), label='Other Liab', color='#7f7f7f')
    axes[0].set_title("Liabilities")
    axes[0].set_xticks(years)
    axes[0].set_xticklabels([str(int(y)) if y else '' for y in years], rotation=45)
    axes[0].legend(loc='upper left', fontsize='x-small')
    
    # Assets
    axes[1].bar(years, fixed_assets, label='Fixed Assets', color='#2ca02c')
    axes[1].bar(years, working_capital, bottom=fixed_assets, label='Working Cap', color='#ff7f0e')
    axes[1].bar(years, other_assets, bottom=np.array(fixed_assets)+np.array(working_capital), label='Other Assets', color='#9467bd')
    axes[1].set_title("Assets")
    axes[1].set_xticks(years)
    axes[1].set_xticklabels([str(int(y)) if y else '' for y in years], rotation=45)
    axes[1].legend(loc='upper left', fontsize='x-small')
    
    # plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_cf_waterfall(o, i, f, net):
    fig, ax = plt.subplots(figsize=(6, 2.5))
    categories = ['Operating', 'Investing', 'Financing', 'Net Change']
    values = [o, i, f, net]
    colors = ['#2ca02c' if v >= 0 else '#d62728' for v in values]
    
    # Calculate starting points for the waterfall
    starts = [0, o, o + i, 0] # Net change starts at 0 to show the final total
    
    ax.bar(categories, values, bottom=starts, color=colors)
    ax.set_title("Cash Flow Waterfall (Latest Year)")
    ax.set_ylabel("Cr")
    # plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf
