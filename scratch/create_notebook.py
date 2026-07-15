import json
import os

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Advanced Risk Analytics & Investor Behaviour\n",
    "\n",
    "This notebook demonstrates Advanced Risk Analytics, Investor Behaviour Analytics, and Mutual Fund Clustering as part of Sprint 6."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Advanced Risk Analytics (VaR & CVaR, Rolling Sharpe)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib.image as mpimg\n",
    "from IPython.display import display\n",
    "\n",
    "var_cvar_df = pd.read_csv('../output/var_cvar_report.csv')\n",
    "print('VaR & CVaR Report (Top 5):')\n",
    "display(var_cvar_df.head())\n",
    "\n",
    "img = mpimg.imread('../output/rolling_sharpe_chart.png')\n",
    "plt.figure(figsize=(14, 7))\n",
    "plt.imshow(img)\n",
    "plt.axis('off')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Investor Behaviour Analytics"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "cohorts_df = pd.read_csv('../output/cohort_analysis.csv')\n",
    "print('Investor Cohort Analysis:')\n",
    "display(cohorts_df)\n",
    "\n",
    "sip_continuity_df = pd.read_csv('../output/sip_continuity.csv')\n",
    "print('\\nSIP Continuity Analysis (Top 5):')\n",
    "display(sip_continuity_df.head())\n",
    "\n",
    "status_counts = sip_continuity_df['status'].value_counts()\n",
    "status_counts.plot(kind='pie', autopct='%1.1f%%', title='SIP Continuity Status', ylabel='', figsize=(6,6))\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Fund Recommendation Engine & Portfolio Concentration"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "recs_low = pd.read_csv('../output/recommendations_low.csv')\n",
    "recs_mod = pd.read_csv('../output/recommendations_moderate.csv')\n",
    "recs_high = pd.read_csv('../output/recommendations_high.csv')\n",
    "\n",
    "print('Top Recommendations (Low Risk):')\n",
    "display(recs_low)\n",
    "print('\\nTop Recommendations (High Risk):')\n",
    "display(recs_high)\n",
    "\n",
    "# Reusing the HHI logic to demonstrate portfolio concentration\n",
    "import numpy as np\n",
    "np.random.seed(42)\n",
    "weights = np.random.dirichlet(np.ones(5), size=1)[0]\n",
    "hhi = np.sum(np.square(weights))\n",
    "classification = 'Diversified' if hhi < 0.15 else ('Moderate' if hhi <= 0.25 else 'Highly Concentrated')\n",
    "print(f'\\nSimulated Portfolio Weights: {[round(w, 3) for w in weights]}')\n",
    "print(f'HHI: {hhi:.4f} => {classification}')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. KMeans Clustering Engine"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "clusters_df = pd.read_csv('../output/cluster_labels.csv')\n",
    "print('Cluster Labels (Top 5):')\n",
    "display(clusters_df.head())\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(20, 8))\n",
    "img1 = mpimg.imread('../output/cluster_pca_plot.png')\n",
    "axes[0].imshow(img1)\n",
    "axes[0].axis('off')\n",
    "\n",
    "img2 = mpimg.imread('../output/cluster_scatter_plot.png')\n",
    "axes[1].imshow(img2)\n",
    "axes[1].axis('off')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 5. Business Insights\n",
    "\n",
    "1. **Risk-Reward Tradeoff in Clusters**: The KMeans clustering visually separates the mutual funds into distinct risk-return profiles, confirming that higher Volatility generally commands a higher CAGR, but the clusters also reveal funds that are sub-optimal (high volatility, lower returns).\n",
    "2. **Investor Cohort Stagnation**: The cohort analysis shows how average SIP amounts and total corpus behave across joining years. Early cohorts have accumulated a significantly larger corpus, emphasizing the power of compounding and long-term consistency.\n",
    "3. **SIP Churn Risk**: A noticeable percentage of investors (flagged as `AT_RISK`) have gaps greater than 35 days between SIPs. This presents an opportunity for targeted engagement campaigns to reduce churn.\n",
    "4. **Tail Risk (CVaR)**: While Historical VaR provides a threshold, the CVaR values for the High Risk funds show that in extreme market downturns, the expected loss can be significantly larger than the VaR boundary, highlighting the fat-tail risk in high-growth funds.\n",
    "5. **Portfolio Concentration**: Using the Herfindahl-Hirschman Index (HHI), we can automatically flag investors whose portfolios are 'Highly Concentrated'. This can be used as a trigger for automated diversification recommendations, steering them towards schemes with non-correlated assets."
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

os.makedirs('notebooks', exist_ok=True)
with open('notebooks/Advanced_Analytics.ipynb', 'w') as f:
    json.dump(notebook, f, indent=1)
print("Notebook created successfully.")
